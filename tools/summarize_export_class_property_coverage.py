#!/usr/bin/env python3
"""Compare selected UModel fake-export cohorts with UELib initialized export rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# These are explicit label crosswalks for an aggregate comparison, not claims that
# the tools select identical object sets. UModel's *3 labels are normalized to the
# corresponding UELib package class label for the table.
CLASS_CROSSWALK = {
    "Texture2D": "Texture2D",
    "MaterialInstanceConstant": "MaterialInstanceConstant",
    "StaticMesh3": "StaticMesh",
    "LightMapTexture2D": "LightMapTexture2D",
    "SkeletalMesh3": "SkeletalMesh",
    "Material3": "Material",
    "AnimSet": "AnimSet",
}


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def group_name(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    if "CookedPCConsole" in parts:
        return "CookedPCConsole"
    for part in parts:
        if part.upper() in {"DLC05", "DLC06", "DLC07"}:
            return part.upper()
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--uelib-run-dir", type=Path, required=True)
    ap.add_argument("--umodel-per-package", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    manifest_rows = csv_rows(args.manifest)
    manifest = {
        row["RelativePath"].replace("\\", "/").casefold(): row for row in manifest_rows
        if row["RelativePath"].lower().endswith(".upk")
    }
    umodel = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in csv_rows(args.umodel_per_package)
    }
    if len(manifest) != 904 or set(manifest) != set(umodel):
        raise SystemExit(f"expected same 904 package paths; manifest={len(manifest)} UModel={len(umodel)}")

    package_summaries: dict[str, dict[str, Any]] = {}
    with (args.uelib_run_dir / "package-summary.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row["package"].replace("\\", "/").casefold()
            if key in package_summaries:
                raise SystemExit(f"duplicate UELib package summary: {key}")
            package_summaries[key] = row
    if set(package_summaries) != set(manifest):
        raise SystemExit(f"UELib summary path mismatch; rows={len(package_summaries)}")
    for key, file_row in manifest.items():
        uelib_row = package_summaries[key]
        umodel_row = umodel[key]
        expected_bytes = int(file_row["Length"])
        expected_hash = file_row["SHA256"].upper()
        if (int(uelib_row["sourceBytes"]) != expected_bytes
                or uelib_row["sourceSha256"].upper() != expected_hash):
            raise SystemExit(f"UELib source identity mismatch: {uelib_row['package']}")
        if (str(umodel_row.get("identity_match", "")).casefold() != "true"
                or int(umodel_row["observed_bytes"]) != expected_bytes
                or umodel_row["observed_sha256"].upper() != expected_hash):
            raise SystemExit(f"UModel source identity mismatch: {umodel_row['relative_path']}")

    class_rows: dict[str, dict[str, Any]] = {}
    property_objects: dict[tuple[str, int], int] = defaultdict(int)
    with (args.uelib_run_dir / "default-properties.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            property_objects[(row["package"].replace("\\", "/").casefold(), int(row["ownerPackageIndex"]))] += 1

    target_labels = set(CLASS_CROSSWALK.values())
    with (args.uelib_run_dir / "initialized-objects.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            label = row.get("exportClassName")
            key = row["package"].replace("\\", "/").casefold()
            if row.get("table") != "export" or label not in target_labels:
                continue
            if key not in class_rows:
                class_rows[key] = {}
            # Key each class/package with compact counters.
            bucket_key = f"{key}\0{label}"
            bucket = class_rows.setdefault(bucket_key, {
                "exports": 0, "unknown": 0, "typed": 0, "deserialized": 0,
                "objects_with_properties": 0, "property_rows": 0,
            })
            bucket["exports"] += 1
            if row.get("objectType") == "UnknownObject":
                bucket["unknown"] += 1
            else:
                bucket["typed"] += 1
            if row.get("deserializationState") == "Deserialized":
                bucket["deserialized"] += 1
            count = property_objects.get((key, int(row["packageIndex"])), 0)
            bucket["property_rows"] += count
            bucket["objects_with_properties"] += count > 0

    result: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    for umodel_class, uelib_label in CLASS_CROSSWALK.items():
        aggregate = Counter()
        packages_uelib = packages_uelib_unknown = 0
        packages_umodel = package_overlap = 0
        for key in manifest:
            bucket = class_rows.get(f"{key}\0{uelib_label}", {})
            exports = int(bucket.get("exports", 0))
            requests = json.loads(umodel[key].get("class_counts_json") or "{}").get(umodel_class, 0)
            aggregate.update({
                "uelib_exports": exports,
                "uelib_unknown": int(bucket.get("unknown", 0)),
                "uelib_typed": int(bucket.get("typed", 0)),
                "uelib_deserialized": int(bucket.get("deserialized", 0)),
                "uelib_property_objects": int(bucket.get("objects_with_properties", 0)),
                "uelib_property_rows": int(bucket.get("property_rows", 0)),
                "umodel_fake_requests": requests,
            })
            packages_uelib += exports > 0
            packages_uelib_unknown += int(bucket.get("unknown", 0)) > 0
            packages_umodel += requests > 0
            package_overlap += exports > 0 and requests > 0

        result.append({
            "umodel_fake_class": umodel_class,
            "uelib_export_class_label": uelib_label,
            "uelib_exports": aggregate["uelib_exports"],
            "uelib_unknown_object_exports": aggregate["uelib_unknown"],
            "uelib_non_unknown_exports": aggregate["uelib_typed"],
            "uelib_deserialized_exports": aggregate["uelib_deserialized"],
            "uelib_objects_with_default_property_rows": aggregate["uelib_property_objects"],
            "uelib_default_property_rows": aggregate["uelib_property_rows"],
            "uelib_packages_with_class": packages_uelib,
            "uelib_packages_with_unknown_class": packages_uelib_unknown,
            "umodel_fake_export_requests": aggregate["umodel_fake_requests"],
            "umodel_packages_with_fake_requests": packages_umodel,
            "packages_with_both_class_and_fake_request": package_overlap,
            "claim": "aggregate class-label crosswalk only; fake requests and UELib exports are not object-level matched",
        })
        totals["uelib_exports"] += aggregate["uelib_exports"]
        totals["uelib_unknown"] += aggregate["uelib_unknown"]
        totals["uelib_properties"] += aggregate["uelib_property_rows"]
        totals["umodel_fake_requests"] += aggregate["umodel_fake_requests"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "class-coverage.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result[0]))
        writer.writeheader()
        writer.writerows(result)
    summary = {
        "package_count": len(manifest),
        "uelib_package_summary_rows": len(package_summaries),
        "umodel_package_rows": len(umodel),
        "class_crosswalk_count": len(CLASS_CROSSWALK),
        "crosswalks_are_object_level_matches": False,
        "selected_cohort_totals": dict(totals),
        "cohorts": result,
        "scope_note": "Class-label aggregate comparison only. UModel fake-export requests are selected serialization attempts, not successful exports or one-to-one object matches.",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "cohorts"}, indent=2))


if __name__ == "__main__":
    main()
