#!/usr/bin/env python3
"""Parse HIRC structures from banks indexed in the exact-build AKPK cohort.

AKPK entry boundaries come from EXP-0130. Banks are deduplicated by exact
SHA-256 and byte size; results are checkpointed by build, payload, wwiser, and
parser identity so interrupted runs can resume without reparsing successes.
Relations are static parser output and do not prove runtime behavior.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from wwise_bank_hirc_census import WWISER_COMMIT, parse_bank
from wwise_pck_table_crosscheck import read_csv


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
DEFAULT_GAME_ROOT = ROOT / "Dishonored RHCP"
DEFAULT_WWISER = ROOT / ".tmp/wwiser-current/wwiser.py"
CACHE_SCHEMA_VERSION = 1
PARSED_FIELDS = (
    "bank_id", "bank_version", "hirc_object_count", "hirc_type_counts",
    "event_count", "action_count", "sound_count", "media_index_count", "media_index_ids",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def stable_key(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(encoded.encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def load_cache(path: Path) -> dict[str, dict]:
    """Read append-only JSONL checkpoints; tolerate only a torn final line."""
    records: dict[str, dict] = {}
    if not path.is_file():
        return records
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        last_line_start = raw.rfind(b"\n") + 1
        try:
            json.loads(raw[last_line_start:].decode("utf-8"))
            raw += b"\n"
        except (UnicodeDecodeError, json.JSONDecodeError):
            raw = raw[:last_line_start]
        path.write_bytes(raw)
    lines = raw.decode("utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                continue
            raise ValueError(f"malformed non-final cache line {i + 1}: {path}")
        if record.get("cache_key"):
            records[record["cache_key"]] = record
    return records


def read_bank_range(game_root: Path, item: dict) -> bytes:
    source = (game_root / Path(item["representative"]["source_path"])).resolve(strict=True)
    offset = int(item["representative"]["entry_offset_hex"], 16)
    size = int(item["entry_bytes"])
    with source.open("rb") as stream:
        stream.seek(offset)
        payload = stream.read(size)
    if len(payload) != size or payload[:4] != b"BKHD":
        raise ValueError(
            f"bank range size/magic mismatch: {item['representative']['source_path']} "
            f"@ {item['representative']['entry_offset_hex']}"
        )
    digest = sha256_bytes(payload)
    if digest != item["bank_payload_sha256"]:
        raise ValueError(f"bank payload changed after catalog scan: {item['bank_payload_sha256']}")
    return payload


def parse_one(item: dict, game_root: Path, wwiser: Path, timeout_seconds: int) -> dict:
    digest = item["bank_payload_sha256"]
    try:
        payload = read_bank_range(game_root, item)
        with tempfile.TemporaryDirectory(prefix=f"akpk-hirc-{digest[:12]}-") as temp_name:
            temp_dir = Path(temp_name)
            bnk_path = temp_dir / f"{digest}.bnk"
            xml_path = temp_dir / f"{digest}.xml"
            bnk_path.write_bytes(payload)
            try:
                result = subprocess.run(
                    [sys.executable, str(wwiser), "-d", "xml", "-dn", str(xml_path.with_suffix("")), str(bnk_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_seconds,
                )
                diagnostics = (result.stderr + result.stdout)[-1200:]
                if result.returncode != 0 or not xml_path.is_file():
                    raise RuntimeError(diagnostics or f"wwiser exit {result.returncode}")
                parsed = parse_bank(xml_path)
            except subprocess.TimeoutExpired as exc:
                diagnostics = str(exc)[-1200:]
                raise RuntimeError(f"wwiser timeout after {timeout_seconds}s: {diagnostics}") from exc
        clean = {key: parsed[key] for key in PARSED_FIELDS}
        clean["objects"] = parsed["_objects"]
        clean["edges"] = parsed["edges"]
        clean["media_index_ids"] = parsed["media_index_ids"]
        return {"status": "parsed", "error": "", "diagnostics": diagnostics, "parsed": clean}
    except Exception as exc:
        return {"status": "parse_error", "error": repr(exc), "diagnostics": "", "parsed": None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=BUILD / "files.csv")
    parser.add_argument("--build-record", type=Path, default=BUILD / "build.md")
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME_ROOT)
    parser.add_argument("--packages", type=Path, default=BUILD / "wwise-localized-akpk-packages.csv")
    parser.add_argument("--entries", type=Path, default=BUILD / "wwise-localized-akpk-entries.csv")
    parser.add_argument("--wwiser", type=Path, default=DEFAULT_WWISER)
    parser.add_argument("--output-dir", type=Path, default=BUILD)
    parser.add_argument("--prefix", default="wwise-localized-akpk-hirc")
    parser.add_argument(
        "--cache", type=Path,
        default=ROOT / ".tmp/wwise-localized-akpk-hirc-cache.jsonl",
        help="append-only local parse cache; keep outside Git",
    )
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--limit", type=int, default=0, help="optional unique-payload limit for a scoped run")
    parser.add_argument("--retry-failures", action="store_true", help="retry cached parse failures")
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout_seconds < 1 or args.checkpoint_every < 1:
        raise SystemExit("jobs, timeout-seconds, and checkpoint-every must be positive")

    manifest = read_csv(args.manifest.resolve(strict=True))
    manifest_by_path = {r["relative_path"]: r for r in manifest}
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    build_id_match = re.search(r"Steam build ID:\s*`?(\d+)", build_text)
    exe_hash_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if not build_id_match or not exe_hash_match:
        raise SystemExit("build record lacks Steam build ID or executable SHA-256")
    exe_path = (args.game_root / "Binaries/Win32/Dishonored.exe").resolve(strict=True)
    exe_hash = sha256_file(exe_path)
    if exe_hash != exe_hash_match.group(1).upper():
        raise SystemExit("current EXE SHA-256 differs from build record")
    exe_manifest = next((r for r in manifest if r["relative_path"].casefold() == "binaries/win32/dishonored.exe"), None)
    if not exe_manifest or exe_manifest["sha256"].upper() != exe_hash:
        raise SystemExit("current EXE SHA-256 differs from manifest")

    wwiser = args.wwiser.resolve(strict=True)
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(wwiser.parent), "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit("could not verify wwiser checkout commit") from exc
    if commit != WWISER_COMMIT:
        raise SystemExit(f"wwiser checkout commit mismatch: {commit}")
    parser_source = Path(__import__("inspect").getsourcefile(parse_bank)).resolve(strict=True)
    parser_sha = sha256_file(parser_source)

    package_rows = read_csv(args.packages.resolve(strict=True))
    package_by_path = {r["relative_path"]: r for r in package_rows}
    entry_path = args.entries.resolve(strict=True)
    entries = [r for r in read_csv(entry_path) if r["section"] == "bank"]
    if len(entries) != 4056:
        raise SystemExit(f"expected 4,056 bank entries from EXP-0130; found {len(entries)}")

    source_paths = sorted({r["source_path"] for r in entries})
    for rel in source_paths:
        expected = package_by_path.get(rel)
        record = manifest_by_path.get(rel)
        source = (args.game_root / Path(rel)).resolve(strict=True)
        if not expected or not record:
            raise SystemExit(f"source is absent from EXP-0130 package table or manifest: {rel}")
        actual_hash = sha256_file(source)
        actual_bytes = source.stat().st_size
        if actual_hash != expected["actual_sha256"].upper() or actual_hash != record["sha256"].upper():
            raise SystemExit(f"source hash mismatch: {rel}")
        if actual_bytes != int(expected["actual_bytes"]) or actual_bytes != int(record["bytes"]):
            raise SystemExit(f"source size mismatch: {rel}")

    # Catalog exact bank hashes without retaining a multi-gigabyte payload corpus.
    unique: dict[tuple[str, int], dict] = {}
    occurrence_rows: list[dict[str, object]] = []
    for row in entries:
        rel = row["source_path"]
        size = int(row["entry_bytes"])
        offset = int(row["entry_offset_hex"], 16)
        path = (args.game_root / Path(rel)).resolve(strict=True)
        with path.open("rb") as stream:
            stream.seek(offset)
            payload = stream.read(size)
        if len(payload) != size or payload[:4] != b"BKHD":
            raise SystemExit(f"bank range size/magic mismatch: {rel} @ {row['entry_offset_hex']}")
        digest = sha256_bytes(payload)
        key = (digest, size)
        item = unique.setdefault(key, {
            "bank_payload_sha256": digest,
            "entry_bytes": size,
            "occurrences": [],
            "representative": row,
        })
        item["occurrences"].append(row)
        occurrence_rows.append({
            "source_path": rel,
            "source_sha256": row["source_sha256"],
            "resource_id": row["resource_id"],
            "extension": row["extension"],
            "entry_offset_hex": row["entry_offset_hex"],
            "entry_bytes": size,
            "bank_payload_sha256": digest,
            "parse_status": "pending",
        })

    unique_items = sorted(unique.values(), key=lambda item: (item["bank_payload_sha256"], item["entry_bytes"]))
    if len(unique_items) != 2570:
        raise SystemExit(f"expected 2,570 distinct bank payloads from EXP-0130 cohort; found {len(unique_items)}")
    if args.limit:
        unique_items = unique_items[:args.limit]

    cache_context = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "build_id": build_id_match.group(1),
        "exe_sha256": exe_hash,
        "wwiser_commit": commit,
        "wwiser_script_sha256": sha256_file(wwiser),
        "parser_source_sha256": parser_sha,
        "python_version": sys.version.split()[0],
        "wwiser_options": ["-d", "xml"],
        "timeout_seconds": args.timeout_seconds,
    }
    for item in unique_items:
        item["cache_key"] = stable_key({
            **cache_context,
            "bank_payload_sha256": item["bank_payload_sha256"],
            "bank_payload_bytes": item["entry_bytes"],
        })

    cache_path = args.cache.resolve()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = load_cache(cache_path)
    cached_items = 0
    pending: list[dict] = []
    for item in unique_items:
        cached = cache.get(item["cache_key"])
        if cached and (cached["status"] == "parsed" or not args.retry_failures):
            cached_items += 1
        else:
            pending.append(item)

    print(
        f"source files verified={len(source_paths)}; occurrences={len(entries)}; "
        f"unique payloads={len(unique_items)}; cache hits={cached_items}; pending={len(pending)}",
        flush=True,
    )
    completed_this_run = 0
    try:
        with cache_path.open("a", encoding="utf-8", newline="\n") as cache_stream:
            batch_size = max(args.jobs, args.jobs * 2)
            for offset in range(0, len(pending), batch_size):
                batch = pending[offset : offset + batch_size]
                with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
                    futures = {
                        executor.submit(parse_one, item, args.game_root, wwiser, args.timeout_seconds): item
                        for item in batch
                    }
                    for future in concurrent.futures.as_completed(futures):
                        item = futures[future]
                        try:
                            outcome = future.result()
                        except Exception as exc:
                            outcome = {"status": "parse_error", "error": repr(exc), "diagnostics": "", "parsed": None}
                        record = {
                            "cache_key": item["cache_key"],
                            "bank_payload_sha256": item["bank_payload_sha256"],
                            "bank_payload_bytes": item["entry_bytes"],
                            **outcome,
                            "checkpointed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        }
                        cache_stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                        cache_stream.flush()
                        completed_this_run += 1
                        cache[item["cache_key"]] = record
                        if completed_this_run % args.checkpoint_every == 0:
                            os.fsync(cache_stream.fileno())
                        done = cached_items + completed_this_run
                        if done % 50 == 0 or done == len(unique_items):
                            failures = sum(
                                1 for current in unique_items
                                if cache.get(current["cache_key"], {}).get("status") == "parse_error"
                            )
                            print(
                                f"processed {done}/{len(unique_items)} unique banks; "
                                f"parse failures={failures}; checkpoints this run={completed_this_run}",
                                flush=True,
                            )
    except KeyboardInterrupt:
        print(
            f"Interrupted safely: {completed_this_run} new results checkpointed in {cache_path}. "
            "Rerun the same command to resume.",
            file=sys.stderr,
            flush=True,
        )
        return 130

    records_by_key = {item["cache_key"]: cache[item["cache_key"]] for item in unique_items}
    unique_rows: list[dict[str, object]] = []
    hirc_rows: list[dict[str, object]] = []
    edge_rows: list[dict[str, object]] = []
    outcome_counts: Counter[str] = Counter()
    type_totals: Counter[str] = Counter()
    parse_failures = 0
    for item in unique_items:
        result = records_by_key.get(item["cache_key"])
        if result is None:
            raise SystemExit(f"missing cache record for bank payload {item['bank_payload_sha256']}")
        status = result["status"]
        outcome_counts[status] += 1
        parsed = result.get("parsed")
        if status == "parse_error":
            parse_failures += 1
        row: dict[str, object] = {
            "bank_payload_sha256": item["bank_payload_sha256"],
            "bank_payload_bytes": item["entry_bytes"],
            "source_occurrence_count": len(item["occurrences"]),
            "representative_source_path": item["representative"]["source_path"],
            "representative_resource_id": item["representative"]["resource_id"],
            "cache_key": item["cache_key"],
            "status": status,
            "error": result.get("error", ""),
            "diagnostics": result.get("diagnostics", ""),
        }
        if parsed:
            row.update({key: parsed[key] for key in PARSED_FIELDS})
            type_totals.update(json.loads(parsed["hirc_type_counts"]))
            hirc_rows.extend({"bank_payload_sha256": item["bank_payload_sha256"], **obj} for obj in parsed["objects"])
            edge_rows.extend({
                "bank_payload_sha256": item["bank_payload_sha256"],
                "bank_version": parsed["bank_version"],
                **edge,
            } for edge in parsed["edges"])
        else:
            row.update({key: "" for key in PARSED_FIELDS})
        unique_rows.append(row)

    allowed_shas = {item["bank_payload_sha256"] for item in unique_items}
    selected_occurrences = [row for row in occurrence_rows if row["bank_payload_sha256"] in allowed_shas]
    status_by_sha = {item["bank_payload_sha256"]: records_by_key[item["cache_key"]]["status"] for item in unique_items}
    for row in selected_occurrences:
        row["parse_status"] = status_by_sha[row["bank_payload_sha256"]]

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix
    write_csv(out / f"{prefix}-unique.csv", unique_rows)
    write_csv(out / f"{prefix}-occurrences.csv", selected_occurrences)
    if hirc_rows:
        write_csv(out / f"{prefix}-objects.csv", hirc_rows)
    if edge_rows:
        write_csv(out / f"{prefix}-edges.csv", edge_rows)
    summary = {
        **cache_context,
        "packages_table_sha256": sha256_file(args.packages.resolve(strict=True)),
        "entries_table_sha256": sha256_file(entry_path),
        "source_files_checked": len(source_paths),
        "bank_entry_occurrences": len(entries),
        "unique_bank_payloads_in_cohort": len(unique),
        "unique_bank_payloads_in_scope": len(unique_items),
        "cache_hits": cached_items,
        "checkpointed_this_run": completed_this_run,
        "cache_path": str(cache_path),
        "cache_outcomes": dict(sorted(outcome_counts.items())),
        "bank_payload_bytes_by_unique_hash": sum(int(item["entry_bytes"]) for item in unique_items),
        "parse_failures": parse_failures,
        "bank_versions": dict(sorted(Counter(str(r.get("bank_version", "")) for r in unique_rows if r["status"] == "parsed").items())),
        "hirc_object_counts_by_type_across_unique_payloads": dict(sorted(type_totals.items())),
        "unique_hirc_object_rows": len(hirc_rows),
        "unique_static_edge_rows": len(edge_rows),
        "scoped_limit": args.limit,
        "limitations": [
            "AKPK bank offsets and sizes derive from the EXP-0130 table parser; this procedure is not an independent AKPK table-parser cross-check.",
            "HIRC parsing uses pinned wwiser and establishes parser-derived structures, not original Wwise source semantics.",
            "Deduplication is by exact SHA-256 and byte size; occurrence output preserves source package provenance.",
            "Relations are static parser output and do not establish runtime bank loading, event execution, language selection, or playback.",
        ],
    }
    summary_path = out / f"{prefix}-summary.json"
    temporary_summary = summary_path.with_name(summary_path.name + ".part")
    temporary_summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temporary_summary.replace(summary_path)
    print(json.dumps(summary, indent=2))
    return 0 if parse_failures == 0 and len(unique_items) == len(unique) else 2


if __name__ == "__main__":
    raise SystemExit(main())
