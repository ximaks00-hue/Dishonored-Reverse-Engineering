#!/usr/bin/env python3
"""Summarize serialized TextureFlipBook properties from the EXP-0088 JSONL corpus."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


FIELDS = (
    "HorizontalImages",
    "VerticalImages",
    "FrameRate",
    "FrameTime",
    "SizeX",
    "SizeY",
    "OriginalSizeX",
    "OriginalSizeY",
    "Format",
    "TextureFileCacheName",
    "MipTailBaseIdx",
    "FirstResourceMemMip",
)
MARKER = b'"ownerObjectPath":"TextureFlipBook'


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {
            row["relative_path"].replace("\\", "/").casefold(): row
            for row in csv.DictReader(stream)
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--properties", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()

    manifest = read_manifest(args.manifest)
    objects: dict[tuple[str, int, str], dict[str, Any]] = {}
    matched_property_rows = 0
    with args.properties.open("rb") as stream:
        for line in stream:
            if MARKER not in line:
                continue
            row = json.loads(line)
            package = str(row["package"]).replace("\\", "/")
            owner_index = int(row["ownerPackageIndex"])
            owner_path = str(row["ownerObjectPath"])
            key = (package, owner_index, owner_path)
            item = objects.setdefault(
                key,
                {
                    "source_package": package,
                    "source_sha256": str(row["sourceSha256"]).upper(),
                    "owner_package_index": owner_index,
                    "owner_object_path": owner_path,
                    "property_rows": 0,
                    "value_error_rows": 0,
                    "properties": {},
                },
            )
            item["property_rows"] += 1
            matched_property_rows += 1
            if row.get("valueError"):
                item["value_error_rows"] += 1
            property_name = row.get("propertyName")
            if property_name in FIELDS:
                item["properties"].setdefault(property_name, []).append(row.get("value"))

    if not objects:
        raise ValueError("No TextureFlipBook owner rows found in property corpus")

    records = []
    value_counts = {field: Counter() for field in FIELDS}
    missing_property_counts = Counter()
    hash_match_count = 0
    for item in sorted(objects.values(), key=lambda x: (x["source_package"].casefold(), x["owner_package_index"])):
        manifest_row = manifest.get(item["source_package"].casefold())
        manifest_sha = manifest_row["sha256"].upper() if manifest_row else None
        hash_match = manifest_sha is not None and manifest_sha == item["source_sha256"]
        hash_match_count += int(hash_match)
        record = {
            key: item[key]
            for key in ("source_package", "source_sha256", "owner_package_index", "owner_object_path", "property_rows", "value_error_rows")
        }
        record["manifest_sha256_match"] = hash_match
        for field in FIELDS:
            values = item["properties"].get(field, [])
            distinct = sorted({"<null>" if value is None else str(value) for value in values})
            record[field] = " | ".join(distinct)
            if not values:
                missing_property_counts[field] += 1
            else:
                value_counts[field].update("<null>" if value is None else str(value) for value in values)
        records.append(record)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0])
    with args.output_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    summary = {
        "source_properties_jsonl": str(args.properties),
        "source_manifest": str(args.manifest),
        "owner_row_count": len(records),
        "property_row_count": matched_property_rows,
        "distinct_package_count": len({row["source_package"] for row in records}),
        "manifest_sha256_match_count": hash_match_count,
        "all_packages_match_manifest_sha256": hash_match_count == len(records),
        "objects_with_value_errors": sum(int(row["value_error_rows"] > 0) for row in records),
        "property_value_distributions": {
            field: dict(sorted(counts.items())) for field, counts in value_counts.items()
        },
        "objects_missing_selected_properties": dict(sorted(missing_property_counts.items())),
        "output_csv": str(args.output_csv),
        "claim_limit": "This summarizes property values emitted by UELib's EXP-0088 corpus. It does not independently validate serialization, class semantics, TFC payloads, or runtime playback.",
    }
    args.output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "property_value_distributions"}, indent=2))
    print(json.dumps(summary["property_value_distributions"], indent=2))


if __name__ == "__main__":
    main()
