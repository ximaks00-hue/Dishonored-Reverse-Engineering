#!/usr/bin/env python3
"""Hash-check PCK sources, extract catalogued WEM ranges temporarily, and decode."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import re
from pathlib import Path, PurePosixPath


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def decode_entry(
    item: dict[str, str], root: Path, temp_root: Path, decoder: str,
    timeout_seconds: int,
) -> dict[str, object]:
    relative = item["source_pck"].replace("\\", "/")
    pck_path = root.joinpath(*PurePosixPath(relative).parts)
    offset = int(item["entry_offset_hex"], 16)
    size = int(item["entry_bytes"])
    started = time.perf_counter()
    temp_path: Path | None = None
    try:
        with pck_path.open("rb") as stream:
            stream.seek(offset)
            payload = stream.read(size)
        if len(payload) != size:
            raise ValueError(f"Short read: expected {size}, received {len(payload)}")
        payload_sha = sha256_bytes(payload)
        fd, temp_name = tempfile.mkstemp(prefix="dishonored_wem_", suffix=".wem", dir=temp_root)
        temp_path = Path(temp_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        process = subprocess.run(
            [decoder, "-O", "-i", str(temp_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        decoder_log = "\n".join(part for part in (process.stdout.strip(), process.stderr.strip()) if part)
        return_code: int | str = process.returncode
        status = "decoded" if process.returncode == 0 else "decode_failed"
    except subprocess.TimeoutExpired as exc:
        payload_sha = ""
        return_code = "timeout"
        raw_log = exc.stderr or exc.stdout or ""
        if isinstance(raw_log, bytes):
            raw_log = raw_log.decode("utf-8", errors="replace")
        decoder_log = str(raw_log).strip() or f"Exceeded {timeout_seconds}s timeout"
        status = "timeout"
    except (OSError, ValueError) as exc:
        payload_sha = ""
        return_code = "read_or_launch_error"
        decoder_log = str(exc)
        status = "read_or_launch_error"
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return {
        "source_pck": relative,
        "embedded_name": item["embedded_name"],
        "entry_offset_hex": item["entry_offset_hex"],
        "entry_bytes": size,
        "payload_sha256": payload_sha,
        "vgmstream_exit_code": return_code,
        "status": status,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "decoder_log": decoder_log[-4000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--pck-catalog", required=True, type=Path)
    parser.add_argument("--build-record", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--decoder", type=Path, help="defaults to vgmstream-cli found on PATH")
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
        raise SystemExit("Could not parse vgmstream -V output") from exc
    # This CLI prints valid version JSON but returns 1 when no input filename
    # is supplied; the parsed version payload is the identity evidence here.
    if "version" not in decoder_info:
        raise SystemExit("Could not establish vgmstream version")

    root = args.game_root.resolve(strict=True)
    temp_root = args.temp_root.resolve(strict=True)
    with args.manifest.resolve(strict=True).open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    exe_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if "10256413" not in build_text or not exe_match:
        raise SystemExit("Build record does not identify build 10256413 and EXE SHA-256")
    expected_exe_sha = exe_match.group(1).upper()
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_row = next((row for row in manifest if row["relative_path"].casefold() == exe_rel.casefold()), None)
    exe_path = root.joinpath(*PurePosixPath(exe_rel).parts)
    if exe_row is None or not exe_path.is_file():
        raise SystemExit("Build EXE missing from current tree or manifest")
    if sha256_file(exe_path) != expected_exe_sha or exe_row["sha256"].upper() != expected_exe_sha:
        raise SystemExit("Current EXE identity does not match build record and manifest")

    package_rows = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in manifest
        if PurePosixPath(row["relative_path"].replace("\\", "/")).suffix.casefold() == ".pck"
    }
    if len(package_rows) != 503:
        raise SystemExit(f"Expected 503 manifest PCK files, got {len(package_rows)}")
    with args.pck_catalog.resolve(strict=True).open(encoding="utf-8-sig", newline="") as stream:
        pck_entries = list(csv.DictReader(stream))
    if len(pck_entries) != 2411:
        raise SystemExit(f"Expected 2,411 PCK entry rows from EXP-0065, got {len(pck_entries)}")

    referenced_packages = {
        row["source_pck"].replace("\\", "/").casefold() for row in pck_entries
    }
    if len(referenced_packages) != 503 or referenced_packages != set(package_rows):
        raise SystemExit("PCK entry catalog package paths do not match the 503 manifest PCKs")

    # Hash each source PCK once before trusting any captured entry range.
    package_hashes: dict[str, str] = {}
    for relative_key, manifest_row in package_rows.items():
        relative = manifest_row["relative_path"].replace("\\", "/")
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file() or path.stat().st_size != int(manifest_row["bytes"]):
            raise SystemExit(f"PCK missing or size mismatch: {relative}")
        actual_hash = sha256_file(path)
        if actual_hash != manifest_row["sha256"].upper():
            raise SystemExit(f"PCK SHA-256 mismatch: {relative}")
        package_hashes[relative_key] = actual_hash

    # Check that every captured table range is in bounds and record overlaps.
    intervals: dict[str, list[tuple[int, int, str]]] = {}
    for row in pck_entries:
        relative = row["source_pck"].replace("\\", "/")
        key = relative.casefold()
        if key not in package_rows:
            raise SystemExit(f"Catalog source is not manifest-listed: {relative}")
        offset = int(row["entry_offset_hex"], 16)
        size = int(row["entry_bytes"])
        package_size = int(package_rows[key]["bytes"])
        if int(row["pck_bytes"]) != package_size:
            raise SystemExit(f"Catalog source size differs from manifest: {relative}")
        if offset < 0 or size <= 0 or offset + size > package_size:
            raise SystemExit(f"Out-of-bounds embedded range: {relative} {row['embedded_name']}")
        intervals.setdefault(key, []).append((offset, offset + size, row["embedded_name"]))
    overlap_rows = []
    for key, ranges in intervals.items():
        previous_end = -1
        previous_name = ""
        for start, end, name in sorted(ranges):
            if start < previous_end:
                overlap_rows.append({"source_pck": package_rows[key]["relative_path"], "previous": previous_name, "current": name})
            if end > previous_end:
                previous_end, previous_name = end, name

    wem_entries = [row for row in pck_entries if row["embedded_name"].casefold().endswith(".wem")]
    if len(wem_entries) != 1908:
        raise SystemExit(f"Expected 1,908 WEM entries, got {len(wem_entries)}")

    results: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(decode_entry, row, root, temp_root, decoder, args.timeout_seconds): row
            for row in wem_entries
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: (str(row["source_pck"]).casefold(), str(row["embedded_name"]).casefold(), str(row["entry_offset_hex"])))
    for result in results:
        key = str(result["source_pck"]).casefold()
        result["source_pck_sha256"] = package_hashes[key]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_pck", "source_pck_sha256", "embedded_name", "entry_offset_hex",
        "entry_bytes", "payload_sha256", "vgmstream_exit_code", "status",
        "elapsed_seconds", "decoder_log",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    counts: dict[str, int] = {}
    for row in results:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    summary = {
        "build_id": "10256413",
        "exe_sha256": expected_exe_sha,
        "vgmstream_path": str(Path(decoder).resolve()),
        "vgmstream_sha256": sha256_file(Path(decoder).resolve()),
        "vgmstream_version": decoder_info["version"],
        "pck_sources_hash_checked": len(package_hashes),
        "pck_entry_catalog_rows": len(pck_entries),
        "pck_entry_ranges_out_of_bounds": 0,
        "pck_entry_range_overlaps": len(overlap_rows),
        "pck_entry_range_overlap_examples": overlap_rows[:20],
        "wem_entries": len(wem_entries),
        "wem_total_bytes": sum(int(row["entry_bytes"]) for row in wem_entries),
        "wem_source_pck_count": len({row["source_pck"].casefold() for row in wem_entries}),
        "jobs": args.jobs,
        "timeout_seconds_per_entry": args.timeout_seconds,
        "decode_options": ["-O", "-i"],
        "outcomes": counts,
        "decoded_input_wem_bytes": sum(int(row["entry_bytes"]) for row in results if row["status"] == "decoded"),
        "failed_entries": [
            {"source_pck": row["source_pck"], "embedded_name": row["embedded_name"], "status": row["status"]}
            for row in results if row["status"] != "decoded"
        ],
        "results_csv": str(args.output.resolve()),
        "limitations": [
            "WEM byte ranges come from the EXP-0065 QuickBMS list-only catalog; this run validates range bounds and decoder acceptance, not an independent PCK table parse.",
            "vgmstream decode success does not establish perceptual correctness, event mapping, or runtime playback selection.",
            "Each temporary WEM copy is removed after decode; no extracted media corpus is retained.",
        ],
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
