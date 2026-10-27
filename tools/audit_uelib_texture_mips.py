#!/usr/bin/env python3
"""Decode and size-check every mip row emitted by the UELib census helper."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from compare_uelib_mip_data_to_umodel_tga import decode_bulk, decode_dxt1, sha256, sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mip-census-csv", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--tfc", type=Path, required=True)
    parser.add_argument("--pixel-format", choices=("PF_DXT1", "PF_G8"), default="PF_DXT1")
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    with args.mip_census_csv.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Mip census CSV contains no rows")

    mip_records = []
    for row in rows:
        index = int(row["mip_index"])
        if row["range_in_file"].lower() != "true":
            raise ValueError(f"Mip {index} range is outside its source file")
        if "StoreInSeparateFile" not in row["bulk_flags"] and row["inline_range_within_export_serial"].lower() != "true":
            raise ValueError(f"Inline mip {index} range is outside the export serial interval")
        raw, bulk_info = decode_bulk(row, args.package, args.tfc)
        width, height = int(row["width"]), int(row["height"])
        if args.pixel_format == "PF_DXT1":
            decoded_pixel_count = len(decode_dxt1(raw, width, height))
        else:
            expected = width * height
            if len(raw) != expected:
                raise ValueError(
                    f"PF_G8 size mismatch for mip {index}: got {len(raw)}, expected {expected}"
                )
            decoded_pixel_count = expected
        mip_records.append({
            "mip_index": index,
            "width": width,
            "height": height,
            "bulk_flags": row["bulk_flags"],
            "storage_file": bulk_info["storage_file"],
            "storage_offset": bulk_info["storage_offset"],
            "storage_size": bulk_info["storage_size"],
            "decoded_bytes": len(raw),
            "decoded_sha256": sha256(raw),
            "pixel_format": args.pixel_format,
            "decoded_pixel_count": decoded_pixel_count,
            **{key: value for key, value in bulk_info.items() if key.startswith("lzo_")},
        })

    result = {
        "mip_census_csv": str(args.mip_census_csv),
        "mip_count": len(rows),
        "package_file": str(args.package),
        "package_sha256": sha256_file(args.package),
        "tfc_file": str(args.tfc),
        "tfc_sha256": sha256_file(args.tfc),
        "pixel_format": args.pixel_format,
        "all_mips_range_valid_and_format_decoded": len(mip_records) == len(rows),
        "all_mips_range_valid_and_dxt1_decoded": args.pixel_format == "PF_DXT1" and len(mip_records) == len(rows),
        "claim_limit": (
            f"All recorded ranges passed file/serial bounds and their decoded byte lengths match {args.pixel_format} dimensions; this audit alone does not compare every mip to UModel output."
        ),
        "mips": mip_records,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "mip_count": len(mip_records),
        "pixel_format": result["pixel_format"],
        "all_mips_range_valid_and_format_decoded": result["all_mips_range_valid_and_format_decoded"],
        "output_json": str(args.output_json),
    }, indent=2))


if __name__ == "__main__":
    main()
