#!/usr/bin/env python3
"""Check whether bytes following aliased LightMap inline mips contain the recorded GUID."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def audit(summary_path: Path) -> dict[str, object]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    package = Path(summary["package_file"])
    csv_path = Path(summary["output_csv"])
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    inline_ends = [
        int(row["storage_end_exclusive"])
        for row in rows
        if row["storage_file"].casefold() == package.name.casefold()
    ]
    if not inline_ends:
        raise ValueError(f"No inline mip ranges in {csv_path}")
    last_inline_end = max(inline_ends)
    serial_end = int(summary["export_serial_end_exclusive"])
    tail_size = serial_end - last_inline_end
    if tail_size < 0 or last_inline_end < 0 or serial_end > package.stat().st_size:
        raise ValueError(f"Invalid package/export bounds in {summary_path}")

    package_sha = sha256_file(package)
    if package_sha != summary["package_sha256"].upper():
        raise ValueError(f"Package hash differs from census summary: {summary_path}")
    data = package.read_bytes()[last_inline_end:serial_end]
    if len(data) != tail_size:
        raise ValueError(f"Truncated trailing range in {summary_path}")

    expected_guid = summary["texture_file_cache_guid_components"]
    guid_words = struct.unpack("<IIII", data[8:24]) if len(data) >= 24 else ()
    guid_matches = len(data) == 32 and guid_words == tuple(
        int(expected_guid[key]) for key in ("A", "B", "C", "D")
    )
    return {
        "summary_file": str(summary_path),
        "object_name": summary["object_name"],
        "package_file": str(package),
        "package_sha256": package_sha,
        "package_index": summary["package_index"],
        "export_serial_end_exclusive": serial_end,
        "last_inline_mip_end_exclusive": last_inline_end,
        "trailing_byte_count": tail_size,
        "trailing_bytes_hex": data.hex().upper(),
        "first_two_u32_le": list(struct.unpack("<II", data[:8])) if len(data) >= 8 else [],
        "guid_u32_le": list(guid_words),
        "summary_guid_u32_le": [int(expected_guid[key]) for key in ("A", "B", "C", "D")],
        "guid_words_match_summary": guid_matches,
        "last_two_u32_le": list(struct.unpack("<II", data[24:32])) if len(data) == 32 else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", nargs="+", type=Path, help="UELib mip census summary JSON files")
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()

    records = [audit(path) for path in args.summaries]
    result = {
        "sample_count": len(records),
        "all_trailing_regions_are_32_bytes": all(row["trailing_byte_count"] == 32 for row in records),
        "all_embedded_guid_words_match_summary": all(row["guid_words_match_summary"] for row in records),
        "all_prefix_and_suffix_words_are_consistent": all(
            row["first_two_u32_le"] == [4, 4] and row["last_two_u32_le"] == [0, 1]
            for row in records
        ),
        "interpretation_limit": "The byte layout repeats and its embedded four little-endian words match the census GUID fields. This establishes byte correspondence only; meanings of the other words and engine/runtime semantics remain unknown.",
        "samples": records,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "samples"}, indent=2))


if __name__ == "__main__":
    main()
