#!/usr/bin/env python3
"""Probe Bink movie metadata and same-stem text sidecars from a saved manifest."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath


PROBE_ENTRIES = (
    "format=format_name,duration,size:"
    "stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,"
    "sample_rate,channels,channel_layout:stream_tags=language,title"
)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def safe_relative(raw: str) -> PurePosixPath:
    rel = PurePosixPath(raw.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"manifest path escapes install root: {raw}")
    return rel


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def probe_movie(
    install_root: Path,
    ffprobe: str,
    row: dict[str, str],
) -> dict[str, object]:
    rel = safe_relative(row["relative_path"])
    path = install_root.joinpath(*rel.parts)
    stat_size = path.stat().st_size
    with path.open("rb") as stream:
        magic = stream.read(4).decode("ascii", errors="replace")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            PROBE_ENTRIES,
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    record: dict[str, object] = {
        "relative_path": rel.as_posix(),
        "manifest_bytes": int(row["bytes"]),
        "actual_bytes": stat_size,
        "magic": magic,
        "probe_exit": result.returncode,
        "probe_error": result.stderr.strip(),
        "format_name": "",
        "duration_s": "",
        "reported_bytes": "",
        "video_codec": "",
        "width": "",
        "height": "",
        "avg_frame_rate": "",
        "audio_stream_count": "",
        "audio_codecs": "",
        "audio_layouts": "",
        "languages": "",
    }
    if result.returncode != 0:
        return record

    payload = json.loads(result.stdout)
    format_data = payload.get("format", {})
    streams = payload.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = [item for item in streams if item.get("codec_type") == "audio"]
    record.update(
        {
            "format_name": format_data.get("format_name", ""),
            "duration_s": format_data.get("duration", ""),
            "reported_bytes": format_data.get("size", ""),
            "video_codec": video.get("codec_name", ""),
            "width": video.get("width", ""),
            "height": video.get("height", ""),
            "avg_frame_rate": video.get("avg_frame_rate", ""),
            "audio_stream_count": len(audio),
            "audio_codecs": ";".join(item.get("codec_name", "") for item in audio),
            "audio_layouts": ";".join(
                f"{item.get('channels', '')}ch/{item.get('sample_rate', '')}Hz"
                for item in audio
            ),
            "languages": ";".join(
                item.get("tags", {}).get("language", "") for item in audio
            ),
        }
    )
    return record


def subtitle_profiles(
    install_root: Path,
    movie_rows: list[dict[str, str]],
    probes: list[dict[str, object]],
) -> list[dict[str, object]]:
    binks = {
        PurePosixPath(str(row["relative_path"])).as_posix().casefold(): row
        for row in probes
    }
    texts = [
        row
        for row in movie_rows
        if safe_relative(row["relative_path"]).suffix.casefold() == ".txt"
    ]
    profiles: list[dict[str, object]] = []
    for row in texts:
        rel = safe_relative(row["relative_path"])
        path = install_root.joinpath(*rel.parts)
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        lines = text.splitlines()
        first_pair = ",".join(lines[0].split(",")[:2]) if lines else ""
        cues: list[tuple[int, int, str]] = []
        malformed = 0
        for line in lines[1:]:
            cells = line.split(",")
            if len(cells) != 3:
                malformed += 1
                continue
            try:
                cues.append((int(cells[0]), int(cells[1]), cells[2]))
            except ValueError:
                malformed += 1
        matching_bik = rel.with_suffix(".bik").as_posix()
        movie = binks.get(matching_bik.casefold())
        duration = float(movie["duration_s"]) if movie and movie["duration_s"] else ""
        max_second = max((cue[1] for cue in cues), default="")
        profiles.append(
            {
                "relative_path": rel.as_posix(),
                "manifest_bytes": int(row["bytes"]),
                "actual_bytes": path.stat().st_size,
                "header_pair_raw": first_pair,
                "parsed_three_field_rows": len(cues),
                "malformed_rows_after_header": malformed,
                "companion_bik_path": movie["relative_path"] if movie else "",
                "companion_bik_duration_s": duration,
                "first_field_min": min((cue[0] for cue in cues), default=""),
                "second_field_max": max_second,
                "event_names": ";".join(cue[2] for cue in cues),
            }
        )
    profiles.sort(key=lambda item: str(item["relative_path"]).casefold())
    return profiles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("install_root", type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("research/builds/BUILD-STEAM-10256413/files.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("research/builds/BUILD-STEAM-10256413"),
    )
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    manifest = read_manifest(args.manifest)
    movie_rows = [
        row
        for row in manifest
        if "/movies/" in safe_relative(row["relative_path"]).as_posix().casefold()
    ]
    bink_rows = [
        row
        for row in movie_rows
        if safe_relative(row["relative_path"]).suffix.casefold() == ".bik"
    ]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(probe_movie, args.install_root, args.ffprobe, row)
            for row in bink_rows
        ]
        probes = [future.result() for future in as_completed(futures)]
    probes.sort(key=lambda item: str(item["relative_path"]).casefold())
    subtitles = subtitle_profiles(args.install_root, movie_rows, probes)
    write_csv(args.output_dir / "movie-bink-probe.csv", probes)
    write_csv(args.output_dir / "movie-subtitle-cue-profile.csv", subtitles)

    failures = sum(int(row["probe_exit"]) != 0 for row in probes)
    bad_magic = sum(row["magic"] != "BIKi" for row in probes)
    size_mismatch = sum(
        int(row["manifest_bytes"]) != int(row["actual_bytes"])
        or str(row["manifest_bytes"]) != str(row["reported_bytes"])
        for row in probes
    )
    pairs = sum(bool(row["companion_bik_path"]) for row in subtitles)
    cue_count = sum(int(row["parsed_three_field_rows"]) for row in subtitles)
    print(
        f"bik={len(probes)} probe_failures={failures} bad_magic={bad_magic} "
        f"size_mismatch={size_mismatch} text_sidecars={len(subtitles)} "
        f"paired_sidecars={pairs} parsed_text_rows={cue_count}"
    )
    return 1 if failures or bad_magic or size_mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
