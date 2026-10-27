#!/usr/bin/env python3
"""Compare selected UELib property rows with UModel formatted object dumps."""

from __future__ import annotations

import argparse
import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

TOP_LEVEL_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[\d+\])?\s*=", re.MULTILINE)
INITIALIZED_OBJECT_RE = re.compile(r"\"package\":\"([^\"]+)\".*\"objectName\":\"([^\"]+)\"")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def find_scalar(text: str, key: str, kind: str) -> str | None:
    match = re.search(rf"(?<![A-Za-z0-9_]){re.escape(key)}\s*=\s*([^,\r\n}}]+)", text)
    if not match:
        return None
    value = match.group(1).strip().strip('"')
    if kind == "number":
        try:
            return str(Decimal(value).normalize())
        except InvalidOperation:
            return None
    return value


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--uelib-run-dir", type=Path, required=True)
    ap.add_argument("--samples", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    run_dir = args.uelib_run_dir.resolve(strict=True)
    samples = read_csv(args.samples.resolve(strict=True))
    initialized_path = run_dir / "initialized-objects.jsonl"
    default_path = run_dir / "default-properties.jsonl"
    wanted = {(r["relative_path"], r["object_name"]): r for r in samples}
    found: dict[tuple[str, str], list[dict[str, Any]]] = {key: [] for key in wanted}

    # Stream the large object corpus but decode only lines matching the selected package/name pairs.
    with initialized_path.open(encoding="utf-8") as f:
        for line in f:
            match = INITIALIZED_OBJECT_RE.search(line)
            if not match:
                continue
            key = match.group(1), match.group(2)
            if key not in wanted:
                continue
            row = json.loads(line)
            if row.get("table") == "export" and row.get("exportClassName") == wanted[key]["expected_uelib_class"]:
                found[key].append(row)

    object_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for key, matches in found.items():
        if len(matches) != 1:
            raise SystemExit(f"expected one UELib export row for {key}, found {len(matches)}")
        object_by_key[key] = matches[0]

    property_rows: dict[tuple[str, int], list[dict[str, Any]]] = {}
    relevant = {(row["package"], row["packageIndex"]) for row in object_by_key.values()}
    with default_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            key = row["package"], row["ownerPackageIndex"]
            if key in relevant:
                property_rows.setdefault(key, []).append(row)

    result_rows: list[dict[str, Any]] = []
    for sample in samples:
        key = sample["relative_path"], sample["object_name"]
        obj = object_by_key[key]
        obj_key = obj["package"], obj["packageIndex"]
        props = property_rows.get(obj_key, [])
        uelib_names = sorted({row["propertyName"] for row in props})
        umodel_path = Path.cwd() / Path(sample["umodel_props_path"])
        if not umodel_path.is_file():
            raise SystemExit(f"UModel property dump not found: {umodel_path}")
        umodel_text = umodel_path.read_text(encoding="utf-8", errors="replace")
        umodel_names = sorted(set(TOP_LEVEL_FIELD_RE.findall(umodel_text)))
        checks = json.loads(sample["value_checks_json"] or "{}")
        uelib_text = "\n".join(str(row.get("value", "")) for row in props)
        value_results = {}
        for name, rule in checks.items():
            u = find_scalar(uelib_text, name, rule["kind"])
            m = find_scalar(umodel_text, name, rule["kind"])
            expected = str(Decimal(rule["expected"]).normalize()) if rule["kind"] == "number" else rule["expected"]
            value_results[name] = {
                "uelib_value": u,
                "umodel_value": m,
                "expected_value": expected,
                "uelib_matches_expected": u == expected,
                "umodel_matches_expected": m == expected,
                "cross_parser_match": u is not None and u == m,
            }
        result_rows.append({
            "sample_id": sample["sample_id"],
            "relative_path": sample["relative_path"],
            "source_sha256": obj["sourceSha256"],
            "object_name": sample["object_name"],
            "package_index": obj["packageIndex"],
            "object_path": obj["objectPath"],
            "uelib_object_type": obj["objectType"],
            "uelib_export_class": obj["exportClassName"],
            "uelib_deserialization_state": obj["deserializationState"],
            "uelib_property_count": len(props),
            "uelib_property_names": ";".join(uelib_names),
            "umodel_top_level_field_count": len(umodel_names),
            "umodel_top_level_field_names": ";".join(umodel_names),
            "shared_field_names": ";".join(sorted(set(uelib_names) & set(umodel_names))),
            "uelib_only_field_names": ";".join(sorted(set(uelib_names) - set(umodel_names))),
            "umodel_only_field_names": ";".join(sorted(set(umodel_names) - set(uelib_names))),
            "field_name_sets_equal": set(uelib_names) == set(umodel_names),
            "selected_value_checks_json": json.dumps(value_results, separators=(",", ":")),
        })

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "comparison.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(result_rows[0]))
        writer.writeheader()
        writer.writerows(result_rows)

    summary = {
        "sample_count": len(result_rows),
        "samples_with_equal_property_name_sets": sum(row["field_name_sets_equal"] for row in result_rows),
        "selected_scalar_checks": sum(len(json.loads(row["selected_value_checks_json"])) for row in result_rows),
        "selected_cross_parser_scalar_matches": sum(
            item["cross_parser_match"]
            for row in result_rows
            for item in json.loads(row["selected_value_checks_json"]).values()
        ),
        "scope_note": "Property-row and formatted-dump comparison only; neither view is the raw serialized byte stream.",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
