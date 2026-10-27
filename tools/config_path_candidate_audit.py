#!/usr/bin/env python3
"""Audit literal config path-like declarations against the recorded install tree.

The emitted path candidates are syntactic normalizations under several named
bases. They are not claims about Unreal's runtime config/path resolution.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import posixpath
import re
from collections import Counter
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def path_kind(row: dict[str, str]) -> str | None:
    key = row["key"].lstrip("+-!").casefold()
    value = row["value"].strip()
    if key == "basedon":
        if re.search(r"[\\/]", value) or re.search(r"\.(ini|int|upk)$", value, re.I):
            return "based_on_file_candidate"
        return None
    if key.endswith("classpath"):
        return None
    if key.endswith(("path", "paths")) and re.search(r"[\\/]|%[A-Z0-9_]+%", value, re.I):
        return "path_value_candidate"
    return None


def candidate_status(
    game_root: Path,
    candidate: str,
    manifest_paths: set[str],
) -> tuple[str, int, bool]:
    if candidate.startswith("/"):
        return "rooted_value_unresolved", 0, False
    if ":" in candidate:
        return "drive_qualified_unresolved", 0, False
    if "*" in candidate or "?" in candidate:
        return "wildcard_unresolved", 0, False
    if candidate == ".." or candidate.startswith("../"):
        return "outside_install_root", 0, False

    absolute = game_root.joinpath(*candidate.split("/"))
    normalized = candidate.casefold().rstrip("/")
    exact_file = normalized in manifest_paths
    descendant_count = sum(
        1 for path in manifest_paths
        if path == normalized or path.startswith(normalized + "/")
    )
    if absolute.is_file():
        return "file_present", descendant_count, exact_file
    if absolute.is_dir():
        return "directory_present", descendant_count, exact_file
    if descendant_count:
        return "manifest_entries_but_target_absent", descendant_count, exact_file
    return "absent_in_tree", 0, exact_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config-directives", type=Path, required=True)
    parser.add_argument("--build-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    game_root = args.game_root.resolve(strict=True)
    manifest_rows = read_csv(args.manifest.resolve(strict=True))
    manifest_paths = {
        row["relative_path"].replace("\\", "/").casefold()
        for row in manifest_rows
    }
    build_text = args.build_record.read_text(encoding="utf-8")
    match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if not match:
        raise SystemExit("Build record has no executable SHA-256")
    expected_sha = match.group(1).upper()
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_path = game_root.joinpath(*exe_rel.split("/"))
    if not exe_path.is_file():
        raise SystemExit(f"Missing build executable: {exe_path}")
    actual_sha = hashlib.sha256(exe_path.read_bytes()).hexdigest().upper()
    manifest_exe = next((row for row in manifest_rows if row["relative_path"].casefold() == exe_rel.casefold()), None)
    if actual_sha != expected_sha or manifest_exe is None or manifest_exe["sha256"].upper() != expected_sha:
        raise SystemExit("Executable identity does not match build record and file manifest")

    source_rows = read_csv(args.config_directives.resolve(strict=True))
    bases = (
        ("source_directory", lambda row: posixpath.dirname(row["source_path"])),
        ("install_root", lambda row: ""),
        ("game_root", lambda row: "DishonoredGame"),
        ("engine_root", lambda row: "Engine"),
    )
    output_rows: list[dict[str, object]] = []
    for row in source_rows:
        kind = path_kind(row)
        if kind is None:
            continue
        raw_value = row["value"].strip()
        normalized_value = raw_value.replace("\\", "/").rstrip("/")
        macro_note = ""
        if "%GAME%" in normalized_value:
            normalized_value = normalized_value.replace("%GAME%", "Dishonored")
            macro_note = "candidate substitution %GAME% -> Dishonored; not verified from runtime"
        out: dict[str, object] = {
            "source_path": row["source_path"],
            "line": row["line"],
            "section": row["section"],
            "key": row["key"],
            "value": raw_value,
            "reference_kind": kind,
            "normalized_value_candidate": normalized_value,
            "normalization_note": macro_note,
        }
        for base_name, base_fn in bases:
            base = base_fn(row)
            candidate = posixpath.normpath(posixpath.join(base, normalized_value))
            status, count, exact_file = candidate_status(game_root, candidate, manifest_paths)
            out[f"{base_name}_candidate"] = candidate
            out[f"{base_name}_status"] = status
            out[f"{base_name}_manifest_file_count"] = count
            out[f"{base_name}_exact_manifest_file"] = exact_file
        output_rows.append(out)

    if len(source_rows) != 76 or len(output_rows) != 63:
        raise SystemExit(f"Input denominator mismatch: {len(source_rows)} directives / {len(output_rows)} path candidates")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0]) if output_rows else []
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts: dict[str, dict[str, int]] = {}
    for base_name, _ in bases:
        status_counts[base_name] = dict(Counter(str(row[f"{base_name}_status"]) for row in output_rows))
    summary = {
        "build_id": "10256413",
        "exe_sha256": expected_sha,
        "input_directive_rows": len(source_rows),
        "path_candidate_rows": len(output_rows),
        "reference_kind_counts": dict(Counter(str(row["reference_kind"]) for row in output_rows)),
        "normalization_bases": [name for name, _ in bases],
        "candidate_status_counts_by_base": status_counts,
        "limitations": [
            "Path candidates are normalized strings under explicit bases, not runtime resolution results.",
            "%GAME% -> Dishonored is a candidate substitution only.",
            "An absent target may be generated, platform-specific, virtual, or resolved by other engine rules.",
            "A present target establishes filesystem/manifest presence, not that the game loads it.",
        ],
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
