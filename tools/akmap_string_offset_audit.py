#!/usr/bin/env python3
"""Audit whether trailing AKMAP DWORD values address the preceding string pool.

The script preserves the candidate 12-byte grouping used by EXP-0116 and tests
the observed DWORDs as offsets relative to byte 8, where the bounded printable
string region begins. It records decoded suffixes without assigning row or
field semantics.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
from pathlib import Path

from akmap_name_catalog import parse_strings, read_csv, sha256

EXPECTED_GROUP_COUNTS = {
    "DishonoredGame/CookedPCConsole/MISSIONAUDIOCACHINGLIST.AKMAP": 2592,
    "DishonoredGame/DLC/PCConsole/DLC05/MISSIONAUDIOCACHINGLIST.AKMAP": 893,
    "DishonoredGame/DLC/PCConsole/DLC06/MISSIONAUDIOCACHINGLIST.AKMAP": 1558,
    "DishonoredGame/DLC/PCConsole/DLC07/MISSIONAUDIOCACHINGLIST.AKMAP": 2592,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--build-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    game_root = args.game_root.resolve(strict=True)
    manifest = read_csv(args.manifest.resolve(strict=True))
    build_text = args.build_record.read_text(encoding="utf-8")
    match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if "10256413" not in build_text or not match:
        raise SystemExit("Build record does not identify build 10256413 and executable SHA-256")
    expected_exe_sha = match.group(1).upper()
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_path = game_root.joinpath(*exe_rel.split("/"))
    exe_row = next((r for r in manifest if r["relative_path"].casefold() == exe_rel.casefold()), None)
    if exe_row is None or not exe_path.is_file():
        raise SystemExit("Build executable missing from current tree or saved manifest")
    if sha256(exe_path) != expected_exe_sha or exe_row["sha256"].upper() != expected_exe_sha:
        raise SystemExit("Current executable identity does not match build record and manifest")

    akmaps = [row for row in manifest if row["relative_path"].casefold().endswith(".akmap")]
    if len(akmaps) != 4:
        raise SystemExit(f"Expected four manifest AKMAP files, got {len(akmaps)}")

    output_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for row in akmaps:
        rel = row["relative_path"].replace("\\", "/")
        path = game_root.joinpath(*rel.split("/"))
        if not path.is_file() or path.stat().st_size != int(row["bytes"]):
            raise SystemExit(f"AKMAP missing or size mismatch: {rel}")
        actual_sha = sha256(path)
        if actual_sha.casefold() != row["sha256"].casefold():
            raise SystemExit(f"AKMAP hash mismatch: {rel}")

        data = path.read_bytes()
        version, tag_offset = struct.unpack_from("<II", data, 0)
        if version != 1 or data[tag_offset:tag_offset + 8] != b"EGLOBAL\0":
            raise SystemExit(f"Unexpected AKMAP preamble: {rel}")
        # EXP-0115's bounded sequence ends after the tag terminator, so EGLOBAL
        # is the last NUL-terminated token in this candidate addressable region.
        string_region = data[8:tag_offset + 8]
        try:
            strings = parse_strings(data, 8, tag_offset + 8)
        except ValueError as error:
            raise SystemExit(f"Invalid candidate string region in {rel}: {error}") from error
        tail = data[tag_offset + 8:]
        if len(tail) < 16 or len(tail) % 4:
            raise SystemExit(f"Post-string data is not DWORD aligned: {rel}")
        words = list(struct.unpack("<" + "I" * (len(tail) // 4), tail))
        candidate_values = words[4:]
        group_count = len(candidate_values) // 3
        remainder = candidate_values[group_count * 3:]
        expected_group_count = EXPECTED_GROUP_COUNTS.get(rel)
        if expected_group_count is None or group_count != expected_group_count:
            raise SystemExit(f"Unexpected candidate group denominator for {rel}: {group_count}")

        token_starts = {file_offset - 8 for file_offset, _ in strings}

        field_counts = [
            {"in_bounds": 0, "token_start": 0, "suffix_nonempty_printable": 0, "empty": 0}
            for _ in range(3)
        ]
        for group_index in range(group_count):
            values = candidate_values[group_index * 3:group_index * 3 + 3]
            for field_index, value in enumerate(values):
                stats = field_counts[field_index]
                in_bounds = value < len(string_region)
                if not in_bounds:
                    suffix = ""
                    status = "out_of_bounds"
                else:
                    stats["in_bounds"] += 1
                    target = string_region[value:]
                    raw_suffix = target.split(b"\0", 1)[0]
                    is_token_start = value in token_starts
                    if is_token_start:
                        stats["token_start"] += 1
                    if not raw_suffix:
                        stats["empty"] += 1
                        suffix = ""
                        status = "empty_at_nul"
                    elif all(0x20 <= byte <= 0x7E for byte in raw_suffix):
                        stats["suffix_nonempty_printable"] += 1
                        suffix = raw_suffix.decode("ascii")
                        status = "token_start" if is_token_start else "printable_suffix"
                    else:
                        suffix = raw_suffix.decode("ascii", errors="replace")
                        status = "nonprintable_suffix"
                output_rows.append({
                    "source_akmap": rel,
                    "group_index": group_index,
                    "field_index": field_index,
                    "raw_u32": value,
                    "candidate_pool_relative_offset": value,
                    "candidate_file_offset": 8 + value if in_bounds else "",
                    "target_suffix": suffix,
                    "target_is_token_start": value in token_starts if in_bounds else False,
                    "target_status": status,
                })

        remainder_audit = []
        for value in remainder:
            in_bounds = value < len(string_region)
            raw_suffix = string_region[value:].split(b"\0", 1)[0] if in_bounds else b""
            remainder_audit.append({
                "raw_u32": value,
                "in_string_region_bounds": in_bounds,
                "candidate_file_offset": 8 + value if in_bounds else None,
                "target_suffix": raw_suffix.decode("ascii", errors="replace"),
                "target_is_token_start": value in token_starts if in_bounds else False,
            })

        upk_stems = {
            manifest_row["relative_path"].replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0].casefold()
            for manifest_row in manifest
            if manifest_row["relative_path"].casefold().endswith(".upk")
        }
        unique_upk_name_matches = {
            value.casefold() for _, value in strings if value.casefold() in upk_stems
        }

        summaries.append({
            "source_akmap": rel,
            "bytes": len(data),
            "sha256": actual_sha,
            "candidate_string_pool_file_range": [8, tag_offset + 8],
            "candidate_string_pool_bytes": len(string_region),
            "post_string_bytes": len(tail),
            "post_string_first_four_u32_raw": words[:4],
            "distinct_exact_upk_basename_string_values": len(unique_upk_name_matches),
            "raw_header_word_1_equals_upk_basename_match_count": words[1] == len(unique_upk_name_matches),
            "candidate_group_width_bytes": 12,
            "candidate_group_count": group_count,
            "trailing_u32_after_candidate_groups": remainder,
            "trailing_u32_offset_audit": remainder_audit,
            "field_offset_checks": field_counts,
            "limitations": [
                "Values were tested as offsets relative to byte 8; this tests string-pool addressability, not field semantics.",
                "A value at a token start may resolve to a token; a value inside a token resolves only to its suffix.",
                "The 12-byte grouping is carried forward from EXP-0116 and remains a candidate record boundary.",
                "No resource dependency, package selection, or runtime load behavior is established.",
            ],
        })

    if len(output_rows) != 22905:
        raise SystemExit(f"Expected 22,905 candidate group fields, got {len(output_rows)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_akmap", "group_index", "field_index", "raw_u32",
        "candidate_pool_relative_offset", "candidate_file_offset", "target_suffix",
        "target_is_token_start", "target_status",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "build_id": "10256413",
        "exe_sha256": expected_exe_sha,
        "akmap_files": len(akmaps),
        "candidate_fields_audited": len(output_rows),
        "method": "Interpret each post-EXP-0116 candidate triplet DWORD as a byte offset relative to the string-region start at file byte 8; record bounds, exact token starts, and NUL-terminated suffixes.",
        "files": summaries,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
