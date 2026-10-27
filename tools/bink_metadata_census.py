#!/usr/bin/env python3
"""Probe all manifest-listed Bink files with FFprobe without decoding frames."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath

SHOW_ENTRIES = (
    "format=format_name,duration,size:"
    "stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffprobe", type=Path, help="defaults to ffprobe found on PATH")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()
    ffprobe = str(args.ffprobe.resolve(strict=True)) if args.ffprobe else shutil.which("ffprobe")
    if not ffprobe:
        parser.error("ffprobe was not found; pass --ffprobe <path>")
    root = args.game_root.resolve(strict=True)
    with args.manifest.resolve(strict=True).open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    candidates = [
        row for row in manifest
        if PurePosixPath(row["relative_path"].replace("\\", "/")).suffix.casefold() == ".bik"
    ]

    rows: list[dict[str, object]] = []
    outcome_counts: Counter[str] = Counter()
    codec_counts: Counter[str] = Counter()
    for item in candidates:
        relative = item["relative_path"].replace("\\", "/")
        path = root.joinpath(*PurePosixPath(relative).parts)
        error = ""
        probe: dict[str, object] = {}
        exit_code: int | str = "missing"
        if path.is_file():
            try:
                process = subprocess.run(
                    [
                        ffprobe, "-v", "error", "-show_entries", SHOW_ENTRIES,
                        "-of", "json", str(path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=args.timeout_seconds,
                )
                exit_code = process.returncode
                error = process.stderr.strip()[:2000]
                if process.stdout.strip():
                    try:
                        probe = json.loads(process.stdout)
                    except json.JSONDecodeError as exception:
                        error = (error + f"; invalid_json:{exception}")[:2000]
            except subprocess.TimeoutExpired:
                exit_code = "timeout"
                error = f"timeout_after_{args.timeout_seconds}s"
        actual_size = path.stat().st_size if path.is_file() else ""
        streams = probe.get("streams", []) if isinstance(probe, dict) else []
        fmt = probe.get("format", {}) if isinstance(probe, dict) else {}
        videos = [stream for stream in streams if stream.get("codec_type") == "video"]
        audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
        status = "parsed" if exit_code == 0 and fmt and streams else "failed"
        outcome_counts[status] += 1
        for stream in videos:
            codec_counts[str(stream.get("codec_name", "<unknown>"))] += 1
        rows.append({
            "relative_path": relative,
            "manifest_bytes": int(item["bytes"]),
            "exists": path.is_file(),
            "observed_bytes": actual_size,
            "size_match": actual_size == int(item["bytes"]) if path.is_file() else False,
            "ffprobe_exit_code": exit_code,
            "format_name": fmt.get("format_name", "") if isinstance(fmt, dict) else "",
            "duration_seconds": fmt.get("duration", "") if isinstance(fmt, dict) else "",
            "stream_count": len(streams),
            "video_codecs": ";".join(str(s.get("codec_name", "")) for s in videos),
            "video_dimensions": ";".join(
                f"{s.get('width', '')}x{s.get('height', '')}" for s in videos
            ),
            "video_frame_rates": ";".join(str(s.get("r_frame_rate", "")) for s in videos),
            "audio_codecs": ";".join(str(s.get("codec_name", "")) for s in audios),
            "audio_channels": ";".join(str(s.get("channels", "")) for s in audios),
            "error": error,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    print(f"FFprobe: {ffprobe}")
    print(f"Manifest Bink candidates: {len(candidates)}")
    print(f"Outcomes: {dict(sorted(outcome_counts.items()))}")
    print(f"Video codecs: {dict(sorted(codec_counts.items()))}")
    print(f"Current file-size matches: {sum(bool(row['size_match']) for row in rows)}/{len(rows)}")
    print(f"Metadata census: {args.output.resolve()}")


if __name__ == "__main__":
    main()
