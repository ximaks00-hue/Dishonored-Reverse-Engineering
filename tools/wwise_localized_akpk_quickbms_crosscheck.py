#!/usr/bin/env python3
"""Cross-check localized AKPK Python entry rows against QuickBMS list-only output."""

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
import time
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
GAME_ROOT = ROOT / "Dishonored RHCP"
QUICKBMS = ROOT / "third_party/quickbms-0.12.0/quickbms.exe"
BMS = ROOT / ".tmp/wwise_pck_extractor.bms"
QUICKBMS_SHA256 = "FF812D38E22AEA0CC2CDC13C5C91CA34FAE4443AB12987002105BE6BAB3F4948"
BMS_SHA256 = "4459C0A4C354A92DCAD335599C389E8296908BD8B38FB128BD4C505AEAEE6B5D"
CACHE_VERSION = 1
LIST_RE = re.compile(r"^\s*([0-9a-fA-F]{1,16})\s+(\d+)\s+(.+?)\s*$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".part")
    try:
        with temp.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def load_cache(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    lines = raw.splitlines()
    if raw and not raw.endswith(b"\n"):
        lines = lines[:-1]
    records: dict[str, dict] = {}
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        records[row["cache_key"]] = row
    return records


def parse_listing(text: str) -> list[dict[str, object]]:
    rows = []
    for line in text.splitlines():
        match = LIST_RE.match(line)
        if not match:
            continue
        offset, size, name = match.groups()
        rows.append({"offset": int(offset, 16), "size": int(size), "embedded_name": name.replace("\\", "/")})
    return rows


def quickbms_one(item: dict, source: Path, quickbms: Path, bms: Path, list_root: Path) -> dict:
    list_path = list_root / f"{item['source_sha256']}.txt"
    list_path.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            [str(quickbms), "-0", "-L", str(list_path), str(bms), str(source)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=180,
        )
        listing = list_path.read_text(encoding="utf-8", errors="replace") if list_path.is_file() else ""
        entries = parse_listing(listing)
        diagnostics = (result.stdout + "\n" + result.stderr)[-1600:]
        status = "listed" if result.returncode == 0 else "quickbms_error"
        if result.returncode == 0 and not entries:
            status = "empty_listing"
        return {"status": status, "return_code": result.returncode, "entries": entries, "diagnostics": diagnostics}
    except subprocess.TimeoutExpired as exc:
        return {"status": "timeout", "return_code": "", "entries": [], "diagnostics": str(exc)[-1600:]}
    except Exception as exc:
        return {"status": "error", "return_code": "", "entries": [], "diagnostics": repr(exc)}
    finally:
        list_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=BUILD / "files.csv")
    parser.add_argument("--build-record", type=Path, default=BUILD / "build.md")
    parser.add_argument("--game-root", type=Path, default=GAME_ROOT)
    parser.add_argument("--packages", type=Path, default=BUILD / "wwise-localized-akpk-packages.csv")
    parser.add_argument("--entries", type=Path, default=BUILD / "wwise-localized-akpk-entries.csv")
    parser.add_argument("--quickbms", type=Path, default=QUICKBMS)
    parser.add_argument("--bms", type=Path, default=BMS)
    parser.add_argument("--output-dir", type=Path, default=BUILD)
    parser.add_argument("--prefix", default="wwise-localized-akpk-quickbms")
    parser.add_argument("--cache", type=Path, default=ROOT / ".tmp/wwise-localized-akpk-quickbms-cache.jsonl")
    parser.add_argument("--list-dir", type=Path, default=ROOT / ".tmp/quickbms-akpk-lists")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        raise SystemExit("jobs must be positive")

    manifest = read_csv(args.manifest.resolve(strict=True))
    manifest_by_path = {r["relative_path"].replace("\\", "/").casefold(): r for r in manifest}
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    build_match = re.search(r"Steam build ID:\s*`?(\d+)", build_text)
    exe_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if not build_match or not exe_match:
        raise SystemExit("build record is missing exact build identity")
    exe_path = args.game_root / "Binaries/Win32/Dishonored.exe"
    exe_sha = sha256_file(exe_path.resolve(strict=True))
    if exe_sha != exe_match.group(1).upper():
        raise SystemExit("local executable does not match build record")
    exe_manifest = manifest_by_path.get("binaries/win32/dishonored.exe")
    if not exe_manifest or exe_manifest["sha256"].upper() != exe_sha:
        raise SystemExit("local executable does not match manifest")

    quickbms = args.quickbms.resolve(strict=True)
    bms = args.bms.resolve(strict=True)
    quickbms_sha = sha256_file(quickbms)
    bms_sha = sha256_file(bms)
    if quickbms_sha != QUICKBMS_SHA256 or bms_sha != BMS_SHA256:
        raise SystemExit("QuickBMS or Wwise BMS hash differs from EXP-0065 pinned toolchain")
    version_result = subprocess.run([str(quickbms), "-V"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    version_text = (version_result.stdout + "\n" + version_result.stderr).strip()[-500:]

    packages = read_csv(args.packages.resolve(strict=True))
    entries = read_csv(args.entries.resolve(strict=True))
    if len(packages) != 4059 or len(entries) != 16168:
        raise SystemExit(f"EXP-0130 denominator mismatch: packages={len(packages)}, entries={len(entries)}")
    entries_by_content: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    entries_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in entries:
        source = row["source_path"].replace("\\", "/")
        package_row = next((p for p in packages if p["relative_path"].replace("\\", "/") == source), None)
        if package_row is None:
            raise SystemExit(f"entry source absent from EXP-0130 package catalog: {source}")
        content_key = (package_row["actual_sha256"].upper(), int(package_row["actual_bytes"]))
        entries_by_content[content_key].append(row)
        entries_by_source[source].append(row)

    # Verify every manifest-listed source path, then run the parser once per exact
    # byte-identical package payload and map its result back to all occurrences.
    path_checks: list[tuple[dict[str, str], Path]] = []
    unique_sources: dict[tuple[str, int], dict] = {}
    package_content_keys: dict[str, tuple[str, int]] = {}
    for row in packages:
        rel = row["relative_path"].replace("\\", "/")
        key_rel = rel.casefold()
        record = manifest_by_path.get(key_rel)
        if not record:
            raise SystemExit(f"package path absent from manifest: {rel}")
        if int(record["bytes"]) != int(row["actual_bytes"]) or record["sha256"].upper() != row["actual_sha256"].upper():
            raise SystemExit(f"EXP-0130 package row disagrees with build manifest: {rel}")
        pure = PurePosixPath(rel)
        if pure.is_absolute() or ".." in pure.parts:
            raise SystemExit(f"package path escapes game root: {rel}")
        source = args.game_root.resolve(strict=True).joinpath(*pure.parts)
        path_checks.append((row, source))

    print(f"verifying {len(path_checks)} source paths and {len(entries_by_content)} distinct nonempty container payloads", flush=True)
    verified_rows: list[dict[str, str]] = []
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(sha256_file, path): (row, path) for row, path in path_checks}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row, path = futures[future]
            actual = future.result()
            if actual != row["actual_sha256"].upper() or path.stat().st_size != int(row["actual_bytes"]):
                raise SystemExit(f"local source differs from manifest/EXP-0130: {row['relative_path']}")
            verified_rows.append(row)
            if index % 500 == 0 or index == len(path_checks):
                print(f"verified source paths {index}/{len(path_checks)}", flush=True)

    for row in packages:
        key = (row["actual_sha256"].upper(), int(row["actual_bytes"]))
        package_content_keys[row["relative_path"].replace("\\", "/")] = key
        if key not in unique_sources and key[1] > 0:
            rel = PurePosixPath(row["relative_path"].replace("\\", "/"))
            unique_sources[key] = {
                "source_sha256": key[0], "source_bytes": key[1],
                "representative_source_path": row["relative_path"],
                "source_occurrence_count": 0,
                "source": args.game_root.resolve(strict=True).joinpath(*rel.parts),
            }
        if key in unique_sources:
            unique_sources[key]["source_occurrence_count"] += 1
    if len(unique_sources) != 2570 or sum(int(r["actual_bytes"]) == 0 for r in packages) != 3:
        raise SystemExit("unexpected unique payload or empty package denominator")

    context = {
        "cache_version": CACHE_VERSION,
        "build_id": build_match.group(1), "exe_sha256": exe_sha,
        "quickbms_sha256": quickbms_sha, "quickbms_version": version_text,
        "bms_sha256": bms_sha, "quickbms_options": ["-0", "-L"],
    }
    jobs = []
    for key, item in sorted(unique_sources.items()):
        item["cache_key"] = hashlib.sha256(json.dumps({**context, "source_sha256": key[0], "source_bytes": key[1]}, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
        jobs.append(item)
    cache_path = args.cache.resolve()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    args.list_dir.resolve().mkdir(parents=True, exist_ok=True)
    cache = load_cache(cache_path)
    cache_hits = sum(item["cache_key"] in cache and cache[item["cache_key"]]["status"] == "listed" for item in jobs)
    pending = [item for item in jobs if item["cache_key"] not in cache or cache[item["cache_key"]]["status"] != "listed"]
    print(f"QuickBMS cache hits={cache_hits}; list-only jobs pending={len(pending)}", flush=True)
    completed = 0
    with cache_path.open("a", encoding="utf-8", newline="\n") as cache_stream:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
            future_map = {
                executor.submit(quickbms_one, item, item["source"], quickbms, bms, args.list_dir.resolve()): item
                for item in pending
            }
            for future in concurrent.futures.as_completed(future_map):
                item = future_map[future]
                outcome = future.result()
                record = {"cache_key": item["cache_key"], "source_sha256": item["source_sha256"], "source_bytes": item["source_bytes"], **outcome}
                cache_stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                cache_stream.flush()
                cache[item["cache_key"]] = record
                completed += 1
                if completed % 100 == 0 or completed == len(pending):
                    os.fsync(cache_stream.fileno())
                    known = [cache[x["cache_key"]] for x in jobs if x["cache_key"] in cache]
                    failures = sum(row.get("status") != "listed" for row in known)
                    print(f"listed {len(known)}/{len(jobs)} unique packages; completed failures={failures}", flush=True)

    unique_results: list[dict[str, object]] = []
    qbm_entry_rows: list[dict[str, object]] = []
    for item in jobs:
        result = cache.get(item["cache_key"])
        if not result:
            raise SystemExit(f"missing QuickBMS result for {item['source_sha256']}")
        representative_path = item["representative_source_path"].replace("\\", "/")
        expected_rows = entries_by_source.get(representative_path, [])
        grouped_rows = entries_by_content.get((item["source_sha256"], item["source_bytes"]), [])
        grouped_paths = sorted({r["source_path"].replace("\\", "/") for r in grouped_rows})
        representative_counter = Counter(
            (r["embedded_name"].replace("/", "\\").casefold(), int(r["entry_offset_hex"], 16), int(r["entry_bytes"]))
            for r in expected_rows
        )
        path_catalogs_consistent = all(
            Counter(
                (r["embedded_name"].replace("/", "\\").casefold(), int(r["entry_offset_hex"], 16), int(r["entry_bytes"]))
                for r in entries_by_source[path]
            ) == representative_counter
            for path in grouped_paths
        )
        expected_counter = Counter((r["embedded_name"].replace("/", "\\").casefold(), int(r["entry_offset_hex"], 16), int(r["entry_bytes"])) for r in expected_rows)
        actual_entries = result.get("entries", [])
        actual_counter = Counter((str(r["embedded_name"]).replace("/", "\\").casefold(), int(r["offset"]), int(r["size"])) for r in actual_entries)
        missing = list((expected_counter - actual_counter).elements())
        extra = list((actual_counter - expected_counter).elements())
        status = "exact_match" if result["status"] == "listed" and not missing and not extra and path_catalogs_consistent else "mismatch"
        unique_results.append({
            "source_sha256": item["source_sha256"], "source_bytes": item["source_bytes"],
            "source_occurrence_count": item["source_occurrence_count"],
            "representative_source_path": item["representative_source_path"],
            "python_catalogs_consistent_across_identical_sources": path_catalogs_consistent,
            "quickbms_status": result["status"], "quickbms_return_code": result.get("return_code", ""),
            "python_entry_rows": len(expected_rows), "quickbms_entry_rows": len(actual_entries),
            "missing_python_rows": len(missing), "extra_quickbms_rows": len(extra),
            "comparison_status": status, "diagnostics": result.get("diagnostics", ""),
        })
        for row in actual_entries:
            key = (str(row["embedded_name"]).replace("/", "\\").casefold(), int(row["offset"]), int(row["size"]))
            qbm_entry_rows.append({
                "source_sha256": item["source_sha256"], "source_bytes": item["source_bytes"],
                "embedded_name": row["embedded_name"], "offset_hex": f"0x{int(row['offset']):08X}",
                "entry_bytes": int(row["size"]), "matches_python_multiset": expected_counter[key] > 0,
            })

    per_source = []
    for row in packages:
        key = (row["actual_sha256"].upper(), int(row["actual_bytes"]))
        unique_result = next((x for x in unique_results if x["source_sha256"] == key[0] and x["source_bytes"] == key[1]), None)
        if key[1] == 0:
            state, rows = "empty_source", 0
        elif unique_result:
            state, rows = str(unique_result["comparison_status"]), int(unique_result["quickbms_entry_rows"])
        else:
            state, rows = "missing_unique_result", 0
        per_source.append({
            "source_path": row["relative_path"], "source_sha256": key[0], "source_bytes": key[1],
            "quickbms_entry_rows": rows, "comparison_status": state,
        })

    args.output_dir.resolve().mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir.resolve() / f"{args.prefix}-unique.csv", unique_results)
    write_csv(args.output_dir.resolve() / f"{args.prefix}-entries.csv", qbm_entry_rows)
    write_csv(args.output_dir.resolve() / f"{args.prefix}-packages.csv", per_source)
    exact_unique = sum(r["comparison_status"] == "exact_match" for r in unique_results)
    summary = {
        **context,
        "packages_table_sha256": sha256_file(args.packages.resolve(strict=True)),
        "entries_table_sha256": sha256_file(args.entries.resolve(strict=True)),
        "source_package_rows": len(packages), "nonempty_source_paths_checked": len(path_checks) - 3,
        "empty_source_paths": 3, "unique_nonempty_source_payloads": len(jobs),
        "unique_quickbms_invocations_this_run": completed, "unique_cache_hits": cache_hits,
        "python_entry_rows": len(entries), "quickbms_unique_payload_entry_rows": len(qbm_entry_rows),
        "python_unique_content_entry_rows": sum(int(r["python_entry_rows"]) for r in unique_results),
        "unique_payloads_with_successful_cached_listings": sum(r["quickbms_status"] == "listed" for r in unique_results),
        "unique_payloads_exact_match": exact_unique,
        "unique_payloads_mismatch_or_failed": len(jobs) - exact_unique,
        "source_paths_exact_match": sum(r["comparison_status"] == "exact_match" for r in per_source),
        "source_paths_empty": sum(r["comparison_status"] == "empty_source" for r in per_source),
        "source_paths_mismatch_or_failed": sum(r["comparison_status"] not in {"exact_match", "empty_source"} for r in per_source),
        "elapsed_verification_seconds": round(time.perf_counter() - started, 3),
        "cache_path": str(cache_path),
        "limitations": [
            "QuickBMS list-only output is a second implementation using the pinned community Wwise extractor script, not an independent vendor specification.",
            "Both implementations are applied to the same exact AKPK source bytes; payload semantics and runtime package/locale selection are not tested.",
            "Exact agreement covers catalogued entry path, offset, and size; it does not establish HIRC reference meaning or playback.",
        ],
    }
    summary_path = args.output_dir.resolve() / f"{args.prefix}-summary.json"
    temp = summary_path.with_suffix(summary_path.suffix + ".part")
    temp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temp.replace(summary_path)
    print(json.dumps(summary, indent=2))
    return 0 if summary["unique_payloads_mismatch_or_failed"] == 0 and summary["source_paths_mismatch_or_failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
