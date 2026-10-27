#!/usr/bin/env python3
"""Extract the observed AKMAP string region and join exact resource basenames.

This records textual equality only. It does not decode the trailing AKMAP data
or claim that any matched resource is loaded at runtime.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_strings(data: bytes, start: int, end: int) -> list[tuple[int, str]]:
    if start < 0 or end > len(data) or start >= end or data[end - 1] != 0:
        raise ValueError("AKMAP string-region candidate has invalid bounds/terminator")
    result: list[tuple[int, str]] = []
    cursor = start
    while cursor < end - 1:
        terminator = data.find(b"\0", cursor, end)
        if terminator < 0:
            raise ValueError("Unterminated string in AKMAP candidate region")
        raw = data[cursor:terminator]
        if not raw or not all(0x20 <= byte <= 0x7E for byte in raw):
            raise ValueError(f"Non-printable or empty token at offset 0x{cursor:X}")
        result.append((cursor, raw.decode("ascii")))
        cursor = terminator + 1
    if cursor != end:
        raise ValueError("String-region cursor did not end at candidate boundary")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--build-record", type=Path, required=True)
    parser.add_argument("--strings-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    game_root = args.game_root.resolve(strict=True)
    manifest = read_csv(args.manifest.resolve(strict=True))
    akmaps = [row for row in manifest if row["relative_path"].casefold().endswith(".akmap")]
    if len(akmaps) != 4:
        raise SystemExit(f"Expected four manifest AKMAP files, got {len(akmaps)}")

    build_text = args.build_record.read_text(encoding="utf-8")
    match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if "10256413" not in build_text or not match:
        raise SystemExit("Build record does not identify build 10256413 and executable hash")
    expected_exe_sha = match.group(1).upper()
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_path = game_root.joinpath(*exe_rel.split("/"))
    manifest_exe = next((row for row in manifest if row["relative_path"].casefold() == exe_rel.casefold()), None)
    if (
        not exe_path.is_file()
        or manifest_exe is None
        or manifest_exe["sha256"].upper() != expected_exe_sha
        or sha256(exe_path) != expected_exe_sha
    ):
        raise SystemExit("Executable identity does not match build record and file manifest")

    basename_paths: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for row in manifest:
        path = Path(row["relative_path"].replace("\\", "/"))
        if path.suffix.casefold() in {".pck", ".upk"}:
            basename_paths[path.stem.casefold()][path.suffix.casefold()].append(row["relative_path"].replace("\\", "/"))

    string_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for row in akmaps:
        rel = row["relative_path"].replace("\\", "/")
        path = game_root.joinpath(*rel.split("/"))
        if not path.is_file() or path.stat().st_size != int(row["bytes"]):
            raise SystemExit(f"AKMAP missing or size-mismatched: {rel}")
        actual_hash = sha256(path)
        if actual_hash.casefold() != row["sha256"].casefold():
            raise SystemExit(f"AKMAP hash mismatch: {rel}")

        data = path.read_bytes()
        if len(data) < 16:
            raise SystemExit(f"AKMAP too short: {rel}")
        version, marker_offset = struct.unpack_from("<II", data, 0)
        if version != 1 or marker_offset + 8 > len(data) or data[marker_offset:marker_offset + 8] != b"EGLOBAL\0":
            raise SystemExit(f"Unexpected AKMAP header/tag layout: {rel}")
        region_end = marker_offset + 8
        strings = parse_strings(data, 8, region_end)
        post_words = []
        for word_offset in range(region_end, min(region_end + 16, len(data)), 4):
            if word_offset + 4 <= len(data):
                post_words.append(struct.unpack_from("<I", data, word_offset)[0])

        match_counts: Counter[str] = Counter()
        match_path_counts: Counter[str] = Counter()
        seen_exact: set[tuple[str, str]] = set()
        for index, (offset, value) in enumerate(strings):
            matches = basename_paths.get(value.casefold(), {})
            families = [ext for ext in (".pck", ".upk") if matches.get(ext)]
            for family in families:
                match_counts[family] += 1
                match_path_counts[family] += len(matches[family])
                seen_exact.add((family, value.casefold()))
            string_rows.append({
                "source_akmap": rel,
                "string_index": index,
                "file_offset_hex": f"0x{offset:X}",
                "value": value,
                "exact_match_families": ";".join(family[1:] for family in families),
                "matching_manifest_paths": ";".join(path for family in families for path in matches[family]),
                "claim": "exact basename text equality only; not proof of a runtime dependency",
            })

        family_summary = {
            "pck_unique_matched_strings": len({value for family, value in seen_exact if family == ".pck"}),
            "pck_matching_manifest_paths": match_path_counts[".pck"],
            "upk_unique_matched_strings": len({value for family, value in seen_exact if family == ".upk"}),
            "upk_matching_manifest_paths": match_path_counts[".upk"],
        }
        summaries.append({
            "source_akmap": rel,
            "manifest_bytes": int(row["bytes"]),
            "sha256": actual_hash,
            "version_u32": version,
            "field_04_u32": marker_offset,
            "ascii_tag_at_field_04": "EGLOBAL",
            "candidate_string_region_start": 8,
            "candidate_string_region_end_exclusive": region_end,
            "candidate_string_count": len(strings),
            **family_summary,
            "bytes_after_candidate_string_region": len(data) - region_end,
            "first_four_post_string_u32_values_raw": post_words,
            "limitations": [
                "The field/tag and candidate NUL-separated strings are structurally observed, but their format roles are unknown.",
                "Trailing binary data is not decoded; post-string DWORDs are raw values only.",
                "Exact basename equality is a candidate cross-file association, not a runtime dependency claim.",
            ],
        })

    args.strings_output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(string_rows[0])
    with args.strings_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(string_rows)

    summary = {
        "build_id": "10256413",
        "exe_sha256": expected_exe_sha,
        "akmap_files": len(akmaps),
        "string_rows": len(string_rows),
        "files": summaries,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
