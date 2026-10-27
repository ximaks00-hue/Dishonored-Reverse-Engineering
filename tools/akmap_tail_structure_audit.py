#!/usr/bin/env python3
"""Measure raw DWORD alignment patterns after the EXP-0115 AKMAP strings.

The candidate 12-byte grouping is a diagnostic hypothesis only; this tool does
not assign field meanings or decode AKMAP records.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from pathlib import Path

from akmap_name_catalog import parse_strings, read_csv, sha256


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
    hash_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if "10256413" not in build_text or not hash_match:
        raise SystemExit("Build record does not identify build 10256413 and executable SHA-256")
    expected_exe_sha = hash_match.group(1).upper()
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_path = game_root.joinpath(*exe_rel.split("/"))
    exe_manifest = next((row for row in manifest if row["relative_path"].casefold() == exe_rel.casefold()), None)
    if not exe_path.is_file() or exe_manifest is None:
        raise SystemExit("Build executable missing from tree or manifest")
    if sha256(exe_path) != expected_exe_sha or exe_manifest["sha256"].upper() != expected_exe_sha:
        raise SystemExit("Executable identity does not match build record and manifest")

    akmaps = [row for row in manifest if row["relative_path"].casefold().endswith(".akmap")]
    if len(akmaps) != 4:
        raise SystemExit(f"Expected four AKMAP files, got {len(akmaps)}")

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
        version, field_04 = struct.unpack_from("<II", data, 0)
        if version != 1 or data[field_04:field_04 + 8] != b"EGLOBAL\0":
            raise SystemExit(f"Unexpected AKMAP preamble: {rel}")
        string_end = field_04 + 8
        strings = parse_strings(data, 8, string_end)
        tail = data[string_end:]
        if len(tail) < 16 or len(tail) % 4:
            raise SystemExit(f"Trailing region is not DWORD aligned: {rel}")
        words = list(struct.unpack("<" + "I" * (len(tail) // 4), tail))
        candidate_data = words[4:]
        complete_triplets = len(candidate_data) // 3
        remainder_words = len(candidate_data) % 3
        triplets = [tuple(candidate_data[i:i + 3]) for i in range(0, complete_triplets * 3, 3)]
        string_count = len(strings)
        equal_first_third = sum(a == c for a, _, c in triplets)
        col_counts = [
            sum(values[col] < string_count for values in triplets)
            for col in range(3)
        ]
        sample_rows = [list(values) for values in triplets[:8]]
        summaries.append({
            "source_akmap": rel,
            "bytes": len(data),
            "sha256": actual_sha,
            "string_count_from_EXP_0115_region": string_count,
            "post_string_bytes": len(tail),
            "post_string_raw_first_four_u32": words[:4],
            "candidate_payload_u32_count_after_first_four": len(candidate_data),
            "candidate_12_byte_group_count": complete_triplets,
            "candidate_trailing_u32_remainder": remainder_words,
            "candidate_groups_with_field0_equal_field2": equal_first_third,
            "candidate_groups_with_field0_equal_field2_fraction": equal_first_third / complete_triplets if complete_triplets else None,
            "candidate_groups_field_values_below_local_string_count_by_column": col_counts,
            "first_eight_candidate_groups_raw": sample_rows,
            "interpretation_limit": "Grouping is arithmetic only; raw values below local string count are not established string indices.",
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_akmap", "bytes", "sha256", "string_count_from_EXP_0115_region",
        "post_string_bytes", "post_string_raw_first_four_u32",
        "candidate_payload_u32_count_after_first_four", "candidate_12_byte_group_count",
        "candidate_trailing_u32_remainder", "candidate_groups_with_field0_equal_field2",
        "candidate_groups_with_field0_equal_field2_fraction",
        "candidate_groups_field_values_below_local_string_count_by_column",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for summary in summaries:
            writer.writerow({key: json.dumps(summary[key]) if isinstance(summary[key], (list, dict)) else summary[key] for key in fields})

    result = {
        "build_id": "10256413",
        "exe_sha256": expected_exe_sha,
        "akmap_files": len(akmaps),
        "method": "Raw little-endian DWORD census after the EXP-0115 candidate string-region end; grouping remainder measured after first four DWORDs.",
        "files": summaries,
        "limitations": [
            "The 12-byte grouping is a diagnostic alignment hypothesis, not a decoded structure.",
            "Field equality and local string-count ranges do not establish field semantics or string references.",
            "No runtime dependency or resource-loading claim is made.",
        ],
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
