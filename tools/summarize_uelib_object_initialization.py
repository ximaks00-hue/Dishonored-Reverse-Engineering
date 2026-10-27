#!/usr/bin/env python3
"""Summarize a full-install UELib object initialization JSONL corpus."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def group_name(relative_path: str) -> str:
    parts = relative_path.replace("\\", "/").split("/")
    if "CookedPCConsole" in parts:
        return "CookedPCConsole"
    for part in parts:
        if part.upper() in {"DLC05", "DLC06", "DLC07"}:
            return part.upper()
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--pkginfo-census", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-log", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    manifest_rows = read_csv(args.manifest)
    census_rows = read_csv(args.pkginfo_census)
    manifest = {r["RelativePath"].replace("\\", "/").casefold(): r for r in manifest_rows}
    census = {r["relative_path"].replace("\\", "/").casefold(): r for r in census_rows}
    summaries = [
        json.loads(line)
        for line in (run_dir / "package-summary.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    initialized = [
        json.loads(line)
        for line in (run_dir / "initialization-summary.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    if set(manifest) != set(census):
        raise SystemExit("Manifest and UModel package census path sets differ")
    expected = set(manifest)
    summary_by_path = {r["package"].replace("\\", "/").casefold(): r for r in summaries}
    init_by_path = {r["package"].replace("\\", "/").casefold(): r for r in initialized}
    if set(summary_by_path) != expected or set(init_by_path) != expected:
        raise SystemExit(
            f"run does not cover manifest: manifest={len(expected)} tables={len(summary_by_path)} "
            f"initialized={len(init_by_path)}"
        )

    package_rows: list[dict[str, Any]] = []
    group_totals: dict[str, Counter[str]] = defaultdict(Counter)
    mismatch_rows = 0
    all_types: Counter[str] = Counter()
    for key in sorted(expected):
        table = summary_by_path[key]
        init = init_by_path[key]
        file_row = manifest[key]
        info_row = census[key]
        object_types = init.get("objectTypes") or {}
        hash_size_match = (
            int(file_row["Length"]) == table["sourceBytes"]
            and file_row["SHA256"].casefold() == table["sourceSha256"].casefold()
        )
        table_counts_match = (
            int(info_row["exports"]) == table["exportCount"]
            and int(info_row["imports"]) == table["importCount"]
        )
        if not hash_size_match or not table_counts_match:
            mismatch_rows += 1
        all_types.update(object_types)
        group = group_name(table["package"])
        values = {
            "packages": 1,
            "exports": table["exportCount"],
            "imports": table["importCount"],
            "initialized_objects": init["initializedObjects"],
            "initialized_edges": init["initializedEdges"],
            "unknown_objects": object_types.get("UnknownObject", 0),
            "default_properties": init["defaultProperties"],
            "default_property_reference_mentions": init["defaultPropertyReferenceMentions"],
            "class_objects": object_types.get("UClass", 0),
            "function_objects": object_types.get("UFunction", 0),
            "property_objects": sum(
                v for k, v in object_types.items() if k.endswith("Property")
            ),
            "init_error_packages": int(bool(init.get("initializationError"))),
        }
        for metric, value in values.items():
            group_totals[group][metric] += value
        package_rows.append(
            {
                "relative_path": table["package"],
                "group": group,
                "source_bytes": table["sourceBytes"],
                "source_sha256": table["sourceSha256"],
                "exports": table["exportCount"],
                "imports": table["importCount"],
                "initialized_objects": init["initializedObjects"],
                "unknown_objects": object_types.get("UnknownObject", 0),
                "unknown_object_percent": round(
                    object_types.get("UnknownObject", 0) * 100 / max(1, init["initializedObjects"]), 3
                ),
                "default_properties": init["defaultProperties"],
                "default_property_reference_mentions": init["defaultPropertyReferenceMentions"],
                "class_objects": object_types.get("UClass", 0),
                "function_objects": object_types.get("UFunction", 0),
                "property_objects": values["property_objects"],
                "top_level_initialize_error": init.get("initializationError") or "",
                "manifest_hash_size_match": str(hash_size_match).lower(),
                "umodel_table_count_match": str(table_counts_match).lower(),
            }
        )

    write_csv(output / "uelib-object-initialization-by-package.csv", package_rows)

    object_states: Counter[str] = Counter()
    exception_types: Counter[str] = Counter()
    unknown_class_labels: Counter[tuple[str, str]] = Counter()
    exception_samples: list[dict[str, str]] = []
    property_type_reference_counts: Counter[str] = Counter()
    target_paths_needed: set[str] = set()
    mentions = [
        json.loads(line)
        for line in (run_dir / "default-property-reference-mentions.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    for row in mentions:
        target_paths_needed.add(row["referenceObjectPath"])

    found_paths: dict[str, list[str]] = defaultdict(list)
    object_path = run_dir / "initialized-objects.jsonl"
    with object_path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("objectType") == "UnknownObject":
                unknown_class_labels[(group_name(row["package"]), row.get("exportClassName") or "<null>")] += 1
            state = row.get("deserializationState") or "<null>"
            object_states[state] += 1
            exception_type = row.get("exceptionType")
            if exception_type:
                exception_types[exception_type] += 1
                if len(exception_samples) < 25:
                    exception_samples.append(
                        {
                            "package": row["package"],
                            "object_path": row.get("objectPath") or "",
                            "exception_type": exception_type,
                            "exception_message": (row.get("exceptionMessage") or "")[:800],
                        }
                    )
            if row.get("propertyTypeReferencePath"):
                property_type_reference_counts[row.get("exportClassName") or "<unknown>"] += 1
            path = row.get("objectPath") or ""
            if "'" in path:
                object_path_name = path.split("'", 1)[1].rsplit("'", 1)[0]
                if object_path_name in target_paths_needed:
                    found_paths[object_path_name].append(row.get("exportClassName") or row.get("importClassName") or "")

    unknown_class_rows = [
        {"group": group, "export_class_label": label, "unknown_object_rows": count}
        for (group, label), count in sorted(
            unknown_class_labels.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
        )
    ]
    write_csv(output / "uelib-unknown-object-export-class-counts.csv", unknown_class_rows)

    mention_class_matches = sum(
        row["referenceClassLabel"] in found_paths.get(row["referenceObjectPath"], [])
        for row in mentions
    )
    default_value_error_count = 0
    with (run_dir / "default-properties.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if json.loads(line).get("valueError"):
                default_value_error_count += 1

    group_rows: list[dict[str, Any]] = []
    for group, counts in sorted(group_totals.items()):
        group_rows.append(
            {
                "group": group,
                "packages": counts["packages"],
                "exports": counts["exports"],
                "imports": counts["imports"],
                "initialized_objects": counts["initialized_objects"],
                "unknown_objects": counts["unknown_objects"],
                "unknown_object_percent": round(
                    counts["unknown_objects"] * 100 / max(1, counts["initialized_objects"]), 3
                ),
                "default_properties": counts["default_properties"],
                "default_property_reference_mentions": counts["default_property_reference_mentions"],
                "class_objects": counts["class_objects"],
                "function_objects": counts["function_objects"],
                "property_objects": counts["property_objects"],
                "top_level_init_error_packages": counts["init_error_packages"],
            }
        )
    write_csv(output / "uelib-object-initialization-by-group.csv", group_rows)

    run_diagnostics: dict[str, Any] | None = None
    if args.run_log:
        log_lines = args.run_log.read_text(encoding="utf-8", errors="replace").splitlines()
        patterns = {
            "property_tag_value_size_error_lines": "PropertyTag value size error",
            "array_property_type_warning_lines": "Couldn't acquire array type",
            "import_export_guids_table_exception_lines": "UELib.UnrealException: Couldn't parse ImportExportGuidsTable",
            "trailing_data_diagnostic_lines": "Trailing data for object",
            "uelib_deserialization_exception_headers": "UELib.DeserializationException:",
        }
        run_diagnostics = {
            "log_path": str(args.run_log),
            "line_count": len(log_lines),
            "counts": {key: sum(pattern in line for line in log_lines) for key, pattern in patterns.items()},
            "examples": [line for line in log_lines if any(pattern in line for pattern in patterns.values())][:20],
            "package_attribution": "not recorded by this console output; do not assign these lines to packages",
        }

    summary = {
        "manifest_packages": len(expected),
        "table_summary_packages": len(summaries),
        "initialized_packages": len(initialized),
        "manifest_hash_size_or_umodel_count_mismatch_packages": mismatch_rows,
        "package_errors_rows": sum(
            1 for line in (run_dir / "package-errors.jsonl").open(encoding="utf-8") if line.strip()
        ),
        "top_level_initialize_error_packages": sum(bool(r.get("initializationError")) for r in initialized),
        "initialized_objects": sum(r["initializedObjects"] for r in initialized),
        "initialized_edges": sum(r["initializedEdges"] for r in initialized),
        "unknown_objects": all_types.get("UnknownObject", 0),
        "unknown_object_percent": round(
            all_types.get("UnknownObject", 0) * 100 / max(1, sum(r["initializedObjects"] for r in initialized)), 3
        ),
        "object_deserialization_states": dict(object_states),
        "object_exception_types": dict(exception_types),
        "object_exception_samples": exception_samples,
        "unknown_object_export_class_labels": unknown_class_rows,
        "initialized_object_type_totals": dict(sorted(all_types.items())),
        "property_type_reference_counts": dict(sorted(property_type_reference_counts.items())),
        "default_properties": sum(r["defaultProperties"] for r in initialized),
        "default_property_value_errors": default_value_error_count,
        "default_property_reference_mentions": len(mentions),
        "distinct_default_reference_target_paths": len(target_paths_needed),
        "reference_mentions_with_matching_initialized_object_path_and_export_class": mention_class_matches,
        "uelib_console_diagnostics": run_diagnostics,
        "default_property_references_are_parser_formatted_text_mentions": True,
        "group_totals": group_rows,
        "limitations": [
            "UELib 1.13.3 initialized object counts describe its API model, not complete UE3 payload decoding.",
            "UnknownObject and Errorlized records remain unresolved; one object exception and package-level parser console diagnostics were observed.",
            "Default-property values and reference comments are UELib formatted output. Mention-to-object checks use the same package load and are not independent parser validation.",
            "UPK export indices, object defaults, and runtime/loaded content are distinct. This profile does not establish runtime use.",
        ],
    }
    (output / "uelib-object-initialization-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
