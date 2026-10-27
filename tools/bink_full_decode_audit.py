#!/usr/bin/env python3
"""Decode every mapped video/audio stream in manifest-listed Bink files to null."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path, PurePosixPath


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run_decode(
    item: dict[str, str], root: Path, ffmpeg: str, timeout_seconds: int,
) -> dict[str, object]:
    relative = item["relative_path"].replace("\\", "/")
    path = root.joinpath(*PurePosixPath(relative).parts)
    command = [
        ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-xerror",
        "-threads", "1", "-i", str(path), "-map", "0:v:0", "-map", "0:a?",
        "-f", "null", "-",
    ]
    started = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
        return_code: int | str = process.returncode
        error = process.stderr.strip()
        status = "decoded" if process.returncode == 0 else "decode_failed"
    except subprocess.TimeoutExpired as exc:
        return_code = "timeout"
        stderr = exc.stderr or ""
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        error = str(stderr).strip() or f"Exceeded {timeout_seconds}s timeout"
        status = "timeout"
    except OSError as exc:
        return_code = "launch_error"
        error = str(exc)
        status = "launch_error"
    return {
        "relative_path": relative,
        "manifest_bytes": int(item["bytes"]),
        "manifest_sha256": item["sha256"].upper(),
        "ffmpeg_exit_code": return_code,
        "status": status,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stream_mapping": "0:v:0 plus all optional 0:a? streams to null muxer",
        "error": error[-4000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--build-record", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--ffmpeg", type=Path, help="defaults to ffmpeg found on PATH")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 8:
        parser.error("--jobs must be between 1 and 8")

    ffmpeg = str(args.ffmpeg.resolve(strict=True)) if args.ffmpeg else shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("ffmpeg was not found; pass --ffmpeg <path>")
    ffmpeg_version = subprocess.run(
        [ffmpeg, "-version"], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=30,
    )
    version_line = ffmpeg_version.stdout.splitlines()[0] if ffmpeg_version.stdout else ""
    if ffmpeg_version.returncode != 0 or not version_line:
        raise SystemExit("Could not establish FFmpeg version")

    manifest_path = args.manifest.resolve(strict=True)
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    exe_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if "10256413" not in build_text or not exe_match:
        raise SystemExit("Build record does not identify build 10256413 and EXE SHA-256")
    expected_exe_sha = exe_match.group(1).upper()
    root = args.game_root.resolve(strict=True)
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_row = next((r for r in manifest if r["relative_path"].casefold() == exe_rel.casefold()), None)
    exe_path = root.joinpath(*PurePosixPath(exe_rel).parts)
    if exe_row is None or not exe_path.is_file():
        raise SystemExit("Build EXE missing from current tree or manifest")
    if sha256(exe_path) != expected_exe_sha or exe_row["sha256"].upper() != expected_exe_sha:
        raise SystemExit("Current EXE identity does not match build record and manifest")

    candidates = [
        row for row in manifest
        if PurePosixPath(row["relative_path"].replace("\\", "/")).suffix.casefold() == ".bik"
    ]
    if len(candidates) != 76:
        raise SystemExit(f"Expected 76 manifest-listed Bink files, got {len(candidates)}")
    for item in candidates:
        relative = item["relative_path"].replace("\\", "/")
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file() or path.stat().st_size != int(item["bytes"]):
            raise SystemExit(f"Bink file missing or size mismatch: {relative}")
        if sha256(path) != item["sha256"].upper():
            raise SystemExit(f"Bink SHA-256 mismatch: {relative}")

    results: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(run_decode, item, root, ffmpeg, args.timeout_seconds): item
            for item in candidates
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: str(row["relative_path"]).casefold())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "relative_path", "manifest_bytes", "manifest_sha256", "ffmpeg_exit_code",
        "status", "elapsed_seconds", "stream_mapping", "error",
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
        "ffmpeg_path": str(Path(ffmpeg).resolve()),
        "ffmpeg_sha256": sha256(Path(ffmpeg).resolve()),
        "ffmpeg_version": version_line,
        "manifest_bik_files": len(candidates),
        "manifest_total_bytes": sum(int(row["bytes"]) for row in candidates),
        "jobs": args.jobs,
        "timeout_seconds_per_file": args.timeout_seconds,
        "mapping": "Decode first video stream and every optional audio stream; send output to FFmpeg null muxer.",
        "outcomes": counts,
        "decoded_bytes": sum(int(row["manifest_bytes"]) for row in results if row["status"] == "decoded"),
        "failed_files": [row["relative_path"] for row in results if row["status"] != "decoded"],
        "results_csv": str(args.output.resolve()),
        "limitations": [
            "A zero FFmpeg exit status establishes decoder acceptance of the mapped streams, not audiovisual quality or semantic correctness.",
            "This audit does not establish which movie/track the game selects at runtime.",
        ],
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
