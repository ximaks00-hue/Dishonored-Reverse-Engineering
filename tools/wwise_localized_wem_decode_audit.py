#!/usr/bin/env python3
"""Hash-check localized AKPK sources and decode each distinct embedded WEM once."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path, PurePosixPath

from wwise_pck_table_crosscheck import read_csv


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def decode_unique(
    item: dict[str, object],
    root: Path,
    temp_root: Path,
    decoder: str,
    timeout_seconds: int,
) -> dict[str, object]:
    relative = str(item["representative_source_path"])
    source = root.joinpath(*PurePosixPath(relative).parts)
    offset = int(item["representative_offset"])
    size = int(item["payload_bytes"])
    started = time.perf_counter()
    temp_path: Path | None = None
    try:
        with source.open("rb") as stream:
            stream.seek(offset)
            payload = stream.read(size)
        if len(payload) != size:
            raise ValueError(f"short read: expected {size}, got {len(payload)}")
        payload_hash = sha256_bytes(payload)
        if payload_hash != item["payload_sha256"]:
            raise ValueError("representative payload hash changed after inventory")
        fd, temp_name = tempfile.mkstemp(prefix="localized_wem_", suffix=".wem", dir=temp_root)
        temp_path = Path(temp_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        result = subprocess.run(
            [decoder, "-O", "-i", str(temp_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_seconds,
        )
        log = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        status = "decoded" if result.returncode == 0 else "decode_failed"
        return {**item, "vgmstream_exit_code": result.returncode, "status": status,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "decoder_log": log[-4000:]}
    except subprocess.TimeoutExpired as exc:
        raw = exc.stderr or exc.stdout or ""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        return {**item, "vgmstream_exit_code": "timeout", "status": "timeout",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "decoder_log": str(raw).strip() or f"exceeded {timeout_seconds}s"}
    except (OSError, ValueError) as exc:
        return {**item, "vgmstream_exit_code": "read_or_launch_error",
                "status": "read_or_launch_error",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "decoder_log": str(exc)}
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--build-record", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--packages", required=True, type=Path)
    parser.add_argument("--entries", required=True, type=Path)
    parser.add_argument("--decoded-output", required=True, type=Path)
    parser.add_argument("--occurrences-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--decoder", type=Path)
    parser.add_argument("--temp-root", type=Path, default=Path(".tmp"))
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 8:
        parser.error("--jobs must be between 1 and 8")

    decoder = str(args.decoder.resolve(strict=True)) if args.decoder else shutil.which("vgmstream-cli")
    if not decoder:
        parser.error("vgmstream-cli was not found; pass --decoder <path>")
    version_result = subprocess.run(
        [decoder, "-V"], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=30,
    )
    try:
        decoder_info = json.loads(version_result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("could not parse vgmstream -V output") from exc
    if "version" not in decoder_info:
        raise SystemExit("could not establish vgmstream version")

    root = args.game_root.resolve(strict=True)
    temp_root = args.temp_root.resolve(strict=True)
    manifest = read_csv(args.manifest.resolve(strict=True))
    manifest_by_path = {
        row["relative_path"].replace("\\", "/").casefold(): row for row in manifest
    }
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    exe_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if "10256413" not in build_text or not exe_match:
        raise SystemExit("build record does not identify build 10256413 and EXE SHA-256")
    expected_exe_hash = exe_match.group(1).upper()
    exe_relative = "Binaries/Win32/Dishonored.exe"
    exe_row = manifest_by_path.get(exe_relative.casefold())
    exe_path = root.joinpath(*PurePosixPath(exe_relative).parts)
    if exe_row is None or sha256_file(exe_path) != expected_exe_hash or exe_row["sha256"].upper() != expected_exe_hash:
        raise SystemExit("current EXE identity does not match build record and manifest")

    packages = read_csv(args.packages.resolve(strict=True))
    package_by_path = {row["relative_path"].casefold(): row for row in packages}
    entries = read_csv(args.entries.resolve(strict=True))
    sound_rows = [row for row in entries if row["section"] == "sound"]
    if len(packages) != 4059 or len(entries) != 16168 or len(sound_rows) != 12112:
        raise SystemExit(
            f"unexpected AKPK denominators: {len(packages)} packages, "
            f"{len(entries)} entries, {len(sound_rows)} sound entries"
        )

    entries_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        entries_by_source[entry["source_path"].casefold()].append(entry)

    unique: dict[tuple[str, int], dict[str, object]] = {}
    occurrences: list[dict[str, object]] = []
    source_hashes: dict[str, str] = {}
    range_overlaps = 0
    range_out_of_bounds = 0
    payload_bytes = 0
    for source_key, source_entries in entries_by_source.items():
        package = package_by_path.get(source_key)
        manifest_row = manifest_by_path.get(source_key)
        if package is None or manifest_row is None:
            raise SystemExit(f"entry source missing from package/manifest catalog: {source_key}")
        relative = package["relative_path"].replace("\\", "/")
        path = root.joinpath(*PurePosixPath(relative).parts)
        data = path.read_bytes()
        actual_hash = sha256_bytes(data)
        if len(data) != int(manifest_row["bytes"]) or actual_hash != manifest_row["sha256"].upper():
            raise SystemExit(f"source size/hash mismatch: {relative}")
        if actual_hash != package["actual_sha256"]:
            raise SystemExit(f"source differs from EXP-0130 package catalog: {relative}")
        source_hashes[source_key] = actual_hash

        ranges: list[tuple[int, int]] = []
        for entry in source_entries:
            start = int(entry["entry_offset_hex"], 16)
            size = int(entry["entry_bytes"])
            end = start + size
            if start < 0 or size <= 0 or end > len(data):
                range_out_of_bounds += 1
                continue
            ranges.append((start, end))
            if entry["section"] != "sound":
                continue
            payload = data[start:end]
            if payload[:4] != b"RIFF":
                raise SystemExit(f"sound entry lacks RIFF marker: {relative}@{start:#x}")
            digest = sha256_bytes(payload)
            key = (digest, size)
            payload_bytes += size
            if key not in unique:
                unique[key] = {
                    "payload_sha256": digest,
                    "payload_bytes": size,
                    "occurrences": 0,
                    "representative_source_path": relative,
                    "representative_offset": start,
                }
            unique[key]["occurrences"] = int(unique[key]["occurrences"]) + 1
            occurrences.append(
                {
                    "source_path": relative,
                    "source_sha256": actual_hash,
                    "extension": entry["extension"],
                    "resource_id": entry["resource_id"],
                    "language_id": entry["language_id"],
                    "language_name": entry["language_name"],
                    "entry_offset_hex": entry["entry_offset_hex"],
                    "entry_bytes": size,
                    "payload_sha256": digest,
                }
            )
        ranges.sort()
        for left, right in zip(ranges, ranges[1:]):
            if left[1] > right[0]:
                range_overlaps += 1

    unique_items = sorted(unique.values(), key=lambda row: str(row["payload_sha256"]))
    results: list[dict[str, object]] = []
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [
            executor.submit(decode_unique, item, root, temp_root, decoder, args.timeout_seconds)
            for item in unique_items
        ]
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            if done % 250 == 0 or done == len(futures):
                print(f"decoded unique payloads {done}/{len(futures)}", flush=True)
    results.sort(key=lambda row: str(row["payload_sha256"]))
    status_by_hash = {str(row["payload_sha256"]): str(row["status"]) for row in results}
    for row in occurrences:
        row["unique_payload_decode_status"] = status_by_hash.get(str(row["payload_sha256"]), "missing_result")

    write_csv(args.decoded_output, results)
    write_csv(args.occurrences_output, occurrences)
    outcome_counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        outcome_counts[status] = outcome_counts.get(status, 0) + 1
    summary = {
        "build_id": "10256413",
        "exe_sha256": expected_exe_hash,
        "vgmstream_path": str(Path(decoder).resolve()),
        "vgmstream_sha256": sha256_file(Path(decoder).resolve()),
        "vgmstream_version": decoder_info["version"],
        "akpk_package_rows": len(packages),
        "akpk_source_hashes_checked": len(source_hashes),
        "akpk_entry_rows": len(entries),
        "akpk_sound_entry_rows": len(sound_rows),
        "akpk_entry_ranges_out_of_bounds": range_out_of_bounds,
        "sound_or_bank_range_overlaps": range_overlaps,
        "sound_payload_total_bytes": payload_bytes,
        "unique_payload_hash_size_pairs": len(unique_items),
        "unique_payload_bytes_decoded": sum(int(row["payload_bytes"]) for row in results if row["status"] == "decoded"),
        "jobs": args.jobs,
        "timeout_seconds_per_unique_payload": args.timeout_seconds,
        "decode_options": ["-O", "-i"],
        "outcomes": outcome_counts,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "WEM ranges derive from the EXP-0130 AKPK table parser; no independent QuickBMS table cross-check exists for this extension cohort.",
            "Payloads with identical SHA-256 and byte size were decoded once; every catalogued occurrence maps to that exact payload hash.",
            "vgmstream acceptance does not prove perceptual correctness, event identity, locale policy, or runtime playback.",
            "Each temporary WEM copy was removed after decoding; no extracted media corpus was retained."
        ],
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"sound_entries={len(sound_rows)} unique_payloads={len(unique_items)} "
        f"outcomes={outcome_counts} range_overlaps={range_overlaps} "
        f"out_of_bounds={range_out_of_bounds} elapsed_s={summary['elapsed_seconds']}"
    )
    return int(bool(range_out_of_bounds or range_overlaps or outcome_counts.get("decode_failed")
                    or outcome_counts.get("timeout") or outcome_counts.get("read_or_launch_error")))


if __name__ == "__main__":
    raise SystemExit(main())
