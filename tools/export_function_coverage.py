#!/usr/bin/env python3
"""Create/check a portable per-function coverage export from published files only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
VERSION = 1
BUILD_ID = "10256413"
EXECUTABLE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
FUNCTIONS = Path("research/executable/functions.csv")
TRIAGE = Path("research/executable/evidence/function-triage/internal-function-triage.csv")
TRIAGE_SUMMARY = Path("research/executable/evidence/function-triage/internal-function-triage-summary.json")
OVERLAY = Path("research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0155.csv")
OVERLAY_SUMMARY = Path("research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0155.json")
CURATED = Path("research/executable/evidence/function-triage/curated-function-claims-EXP-0155.json")
CURATED_SCHEMA = Path("schemas/curated-function-claims.schema.json")
EXPORT_SCHEMA = Path("schemas/function-coverage-export.schema.json")
BUILD_RECORD = Path("research/builds/BUILD-STEAM-10256413/build.md")
EXP_PATHS = {
    "EXP-0041": Path("experiments/EXP-0041-ghidra-function-count-reconciliation.md"),
    "EXP-0072": Path("experiments/EXP-0072-exact-build-internal-function-subsystem-triage.md"),
    "EXP-0155": Path("experiments/EXP-0155-set-enabled-shared-native-adapter.md"),
}
OTHER_INPUTS = (
    FUNCTIONS,
    TRIAGE,
    TRIAGE_SUMMARY,
    OVERLAY,
    OVERLAY_SUMMARY,
    CURATED,
    CURATED_SCHEMA,
    EXPORT_SCHEMA,
    BUILD_RECORD,
    Path("knowledge/database/schema.sql"),
    Path("tools/knowledge/sync_from_experiments.py"),
    Path("docs/methodology/function-evidence-model.md"),
)
OUTPUT_JSON = Path("research/executable/evidence/function-triage/function-coverage-EXP-0155.json")
OUTPUT_CSV = Path("research/executable/evidence/function-triage/function-coverage-EXP-0155.csv")
CSV_COLUMNS = [
    "address",
    "rva",
    "name",
    "signature",
    "size_bytes",
    "analysis_axis",
    "analysis_source",
    "review_status",
    "overlay_claim_status",
    "semantic_axis",
    "claim_status",
    "claim_summary",
    "claim_source",
    "connectivity_axis",
    "runtime_axis",
    "highest_portable_evidence_level",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    value = yaml.safe_load(match.group(1))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: frontmatter must be an object")
    return value


def _validate_schema(instance: dict[str, Any], schema_path: Path) -> None:
    schema = _read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    problems = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.absolute_path))
    if problems:
        details = "; ".join(f"{list(error.absolute_path)}: {error.message}" for error in problems)
        raise ValueError(f"{schema_path}: exported record fails schema: {details}")


def _build_identity(root: Path, exp41: dict[str, Any]) -> dict[str, str]:
    build_text = (root / BUILD_RECORD).read_text(encoding="utf-8")
    app_id = re.search(r"Steam app ID:\s*`?(\d+)", build_text)
    build_id = re.search(r"Steam build ID:\s*`?(\d+)", build_text)
    sha = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    architecture = re.search(r"Architecture:\s*([^\r\n(]+)", build_text)
    image_base = re.search(r"image base\s+`?(0x[0-9A-Fa-f]+)", (root / EXP_PATHS["EXP-0041"]).read_text(encoding="utf-8"), re.I)
    if not all((app_id, build_id, sha, architecture, image_base)):
        raise ValueError("build record or EXP-0041 is missing required identity fields")
    actual = {
        "app_id": app_id.group(1),
        "build_id": build_id.group(1),
        "architecture": architecture.group(1).strip(),
        "module": "Dishonored.exe",
        "image_base": f"0x{int(image_base.group(1), 16):08X}",
        "executable_sha256": sha.group(1).upper(),
    }
    if actual["build_id"] != BUILD_ID or actual["executable_sha256"] != EXECUTABLE_SHA256:
        raise ValueError("build record identity does not match the export's registered build")
    if exp41.get("build") != BUILD_ID:
        raise ValueError("EXP-0041 build identity differs from the build record")
    return actual


def build_export(root: Path = ROOT) -> tuple[dict[str, Any], bytes]:
    """Build deterministic manifest and CSV bytes using only repository files."""
    root = root.resolve()
    exp_metadata = {key: _frontmatter(root / path) for key, path in EXP_PATHS.items()}
    for exp_id, metadata in exp_metadata.items():
        if metadata.get("id") != exp_id or metadata.get("build") != BUILD_ID:
            raise ValueError(f"{exp_id}: record ID/build does not match export scope")

    build = _build_identity(root, exp_metadata["EXP-0041"])
    function_rows = _read_csv(root / FUNCTIONS)
    triage_rows = _read_csv(root / TRIAGE)
    overlay_rows = _read_csv(root / OVERLAY)
    triage_summary = _read_json(root / TRIAGE_SUMMARY)
    overlay_summary = _read_json(root / OVERLAY_SUMMARY)
    curated = _read_json(root / CURATED)
    _validate_schema(curated, root / CURATED_SCHEMA)

    indexed: dict[int, dict[str, str]] = {}
    for row in function_rows:
        address = int(row["address"], 16)
        if address in indexed:
            raise ValueError(f"duplicate function index address: 0x{address:08X}")
        if address < int(build["image_base"], 16) or int(row["size"]) <= 0:
            raise ValueError(f"invalid VA/size in published function index: 0x{address:08X}")
        indexed[address] = row
    if len(indexed) != 72437:
        raise ValueError(f"expected 72,437 published internal function rows, found {len(indexed)}")

    triage_addresses = [int(row["address"], 16) for row in triage_rows]
    if len(triage_addresses) != len(set(triage_addresses)) or set(triage_addresses) != set(indexed):
        raise ValueError("EXP-0072 triage address set does not exactly match the published function index")
    if (
        triage_summary.get("build_id") != BUILD_ID
        or triage_summary.get("exe_sha256", "").upper() != EXECUTABLE_SHA256
        or triage_summary.get("function_index_rows") != len(indexed)
        or triage_summary.get("function_index_unique_addresses") != len(indexed)
        or len(triage_rows) != len(indexed)
    ):
        raise ValueError("EXP-0072 triage summary identity or denominator mismatch")
    if (
        triage_summary.get("functions_assigned_unknown_subsystem_bucket")
        + triage_summary.get("functions_assigned_symbol_name_candidate_bucket")
        != len(indexed)
    ):
        raise ValueError("EXP-0072 subsystem bucket counts do not sum to the index denominator")

    overlay_by_address: dict[int, dict[str, str]] = {}
    for row in overlay_rows:
        address = int(row["address"], 16)
        if address in overlay_by_address:
            raise ValueError(f"duplicate address in cumulative review overlay: 0x{address:08X}")
        if address not in indexed:
            raise ValueError(f"reviewed address is missing from function index: 0x{address:08X}")
        overlay_by_address[address] = row
    if (
        overlay_summary.get("build_id") != BUILD_ID
        or overlay_summary.get("exe_sha256", "").upper() != EXECUTABLE_SHA256
        or overlay_summary.get("indexed_internal_functions") != len(indexed)
        or overlay_summary.get("cumulative_manual_body_reviewed_functions") != len(overlay_by_address)
        or overlay_summary.get("cumulative_rows_csv") != OVERLAY.name
    ):
        raise ValueError("EXP-0155 overlay summary does not match its source rows or build")

    if (
        curated.get("app_id") != build["app_id"]
        or curated.get("build_id") != BUILD_ID
        or curated.get("executable_sha256", "").upper() != EXECUTABLE_SHA256
        or curated.get("module") != build["module"]
    ):
        raise ValueError("curated function claim registry has a different build or module identity")
    curated_by_address: dict[int, dict[str, Any]] = {}
    exp_paths = {path.stem[:8]: path for path in (root / "experiments").glob("EXP-*.md")}
    for record in curated.get("records", []):
        address = int(record["address"], 16)
        if address in curated_by_address:
            raise ValueError(f"duplicate curated function claim: 0x{address:08X}")
        if address not in indexed:
            raise ValueError(f"curated function address is missing from function index: 0x{address:08X}")
        if record["experiment"] not in exp_paths:
            raise ValueError(f"curated function claim references missing source {record['experiment']}")
        curated_by_address[address] = record

    image_base = int(build["image_base"], 16)
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    level_counts = {"L0": 0, "L1": 0, "L2": 0}
    for address in sorted(indexed):
        source = indexed[address]
        overlay = overlay_by_address.get(address)
        claim = curated_by_address.get(address)
        analyzed = overlay is not None or claim is not None
        confirmed = claim is not None and claim["claim_status"] == "confirmed"
        if confirmed:
            level = "L2"
        elif analyzed:
            level = "L1"
        else:
            level = "L0"
        level_counts[level] += 1

        analysis_sources: list[str] = []
        if overlay is not None:
            analysis_sources.append(f"{OVERLAY.as_posix()}#EXP-0155")
        if claim is not None:
            analysis_sources.append(f"{CURATED.as_posix()}#{claim['experiment']}")
        writer.writerow({
            "address": f"0x{address:08X}",
            "rva": f"0x{address - image_base:08X}",
            "name": source["name"],
            "signature": source["signature"],
            "size_bytes": source["size"],
            "analysis_axis": "analyzed" if analyzed else "indexed",
            "analysis_source": ";".join(analysis_sources),
            "review_status": (
                overlay["review_status"] if overlay is not None
                else "curated_static_role_record" if claim is not None
                else "not_reviewed_in_portable_overlay"
            ),
            "overlay_claim_status": overlay["claim_status"] if overlay is not None else "",
            "semantic_axis": (
                "confirmed" if confirmed else "claim_recorded" if claim is not None else "no_portable_claim"
            ),
            "claim_status": claim["claim_status"] if claim is not None else "",
            "claim_summary": claim["summary"] if claim is not None else "",
            "claim_source": claim["experiment"] if claim is not None else "",
            "connectivity_axis": "not_exported",
            "runtime_axis": "not_exported",
            "highest_portable_evidence_level": level,
        })
    csv_bytes = out.getvalue().encode("utf-8")

    input_paths = [*OTHER_INPUTS, *EXP_PATHS.values()]
    inputs = []
    for path in input_paths:
        entry: dict[str, Any] = {"path": path.as_posix(), "sha256": sha256_file(root / path)}
        if path in {FUNCTIONS, TRIAGE, OVERLAY}:
            entry["rows"] = len(_read_csv(root / path))
        inputs.append(entry)

    source_records = []
    for exp_id in EXP_PATHS:
        metadata = exp_metadata[exp_id]
        source_records.append({
            "id": exp_id,
            "path": EXP_PATHS[exp_id].as_posix(),
            "sha256": sha256_file(root / EXP_PATHS[exp_id]),
            "claim_status": metadata["claim_status"],
        })

    manifest: dict[str, Any] = {
        "schema_version": VERSION,
        "metric_scope": (
            "Repository-published function evidence only. This export is not a snapshot of arbitrary rows in the ignored local SQLite database."
        ),
        "build": build,
        "generated_by": {
            "tool": "tools/export_function_coverage.py",
            "version": VERSION,
            "sha256": sha256_file(root / "tools/export_function_coverage.py"),
        },
        "source_records": source_records,
        "inputs": inputs,
        "measurements": {
            "denominator": len(indexed),
            "analysis": {
                "indexed_only": len(indexed) - len(overlay_by_address | curated_by_address),
                "analyzed": len(overlay_by_address | curated_by_address),
                "manual_review_overlay": len(overlay_by_address),
                "curated_records": len(curated_by_address),
            },
            "semantic_claims": {
                "confirmed": sum(row["claim_status"] == "confirmed" for row in curated_by_address.values()),
                "other_claims": sum(row["claim_status"] != "confirmed" for row in curated_by_address.values()),
                "no_portable_claim": len(indexed) - len(curated_by_address),
            },
            "portable_highest_known_level": level_counts,
            "unpublished_levels": ["L3", "L4"],
            "triage_baseline": {
                "unknown_subsystem": triage_summary["functions_assigned_unknown_subsystem_bucket"],
                "symbol_name_candidates": triage_summary["functions_assigned_symbol_name_candidate_bucket"],
            },
        },
        "per_function_export": {
            "path": OUTPUT_CSV.as_posix(),
            "sha256": sha256_bytes(csv_bytes),
            "rows": len(indexed),
            "columns": CSV_COLUMNS,
        },
        "limitations": [
            "The exporter consumes the committed function index; it does not re-index the executable or launch Ghidra.",
            "The executable, Ghidra project and SQLite database are not read. Build identity is taken from the recorded build file and source EXP metadata.",
            "L0-L2 represent the highest evidence level recoverable from the listed portable inputs. L3 and L4 are not exported; their absence here is not proof that an ignored local database has no such rows.",
            "The EXP-0072 label/callgraph triage is a static candidate baseline, not semantic ownership or runtime reachability.",
            "The CSV's connectivity_axis and runtime_axis are marked not_exported rather than inferred from missing local database rows.",
        ],
    }
    _validate_schema(manifest, root / EXPORT_SCHEMA)
    return manifest, csv_bytes


def _canonical_json(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (defaults to this checkout)")
    parser.add_argument("--check", action="store_true", help="verify committed exports without rewriting them")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest, csv_bytes = build_export(root)
    json_bytes = _canonical_json(manifest)
    manifest_path = root / OUTPUT_JSON
    csv_path = root / OUTPUT_CSV

    if args.check:
        if not manifest_path.is_file() or manifest_path.read_bytes() != json_bytes:
            raise SystemExit(f"stale or missing export: {OUTPUT_JSON}; run python tools/export_function_coverage.py")
        if not csv_path.is_file() or csv_path.read_bytes() != csv_bytes:
            raise SystemExit(f"stale or missing export: {OUTPUT_CSV}; run python tools/export_function_coverage.py")
        print(f"Function coverage export OK: {manifest['measurements']['denominator']} rows; provenance hashes match")
        return 0

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_bytes(csv_bytes)
    manifest_path.write_bytes(json_bytes)
    print(f"Wrote {OUTPUT_JSON} and {OUTPUT_CSV}; run with --check to verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
