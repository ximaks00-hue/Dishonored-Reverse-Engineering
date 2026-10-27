#!/usr/bin/env python3
"""Validate and summarize a full-install UELib on-demand object-load pass."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

CLASS_CROSSWALK = {
    "Texture2D": "Texture2D",
    "MaterialInstanceConstant": "MaterialInstanceConstant",
    "StaticMesh3": "StaticMesh",
    "LightMapTexture2D": "LightMapTexture2D",
    "SkeletalMesh3": "SkeletalMesh",
    "Material3": "Material",
    "AnimSet": "AnimSet",
}


def read_csv(path: Path) -> list[dict[str, str]]:
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


def new_count() -> Counter[str]:
    return Counter()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--pkginfo-census", type=Path, required=True)
    ap.add_argument("--prior-profile", type=Path, required=True,
                    help="EXP-0070 per-package default-property row counts")
    ap.add_argument("--prior-default-properties", type=Path, required=True,
                    help="EXP-0070 default-property rows for owner-level reconciliation")
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--run-log", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    manifest_rows = read_csv(args.manifest)
    manifest = {
        row["RelativePath"].replace("\\", "/").casefold(): row
        for row in manifest_rows if row["RelativePath"].lower().endswith(".upk")
    }
    census = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in read_csv(args.pkginfo_census)
    }
    if len(manifest) != 904 or set(manifest) != set(census):
        raise SystemExit(f"expected matching 904 package sets; manifest={len(manifest)} census={len(census)}")
    prior_defaults = {
        row["relative_path"].replace("\\", "/").casefold(): int(row["default_properties"])
        for row in read_csv(args.prior_profile)
    }
    if set(prior_defaults) != set(manifest):
        raise SystemExit(f"prior EXP-0070 package denominator mismatch: {len(prior_defaults)}")
    prior_owner_rows: Counter[tuple[str, int]] = Counter()
    with args.prior_default_properties.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            prior_owner_rows[(row["package"].replace("\\", "/").casefold(), int(row["ownerPackageIndex"]))] += 1

    def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = row["package"].replace("\\", "/").casefold()
                if key in result:
                    raise SystemExit(f"duplicate package row in {path.name}: {key}")
                result[key] = row
        return result

    package_tables = read_jsonl(args.run_dir / "package-summary.jsonl")
    initialization = read_jsonl(args.run_dir / "initialization-summary.jsonl")
    errors_path = args.run_dir / "package-errors.jsonl"
    package_errors = sum(bool(line.strip()) for line in errors_path.open(encoding="utf-8"))
    if set(package_tables) != set(manifest) or set(initialization) != set(manifest):
        raise SystemExit(
            f"run coverage mismatch: manifest={len(manifest)} tables={len(package_tables)} "
            f"initialization={len(initialization)}"
        )

    package_metrics: dict[str, Counter[str]] = {key: Counter() for key in manifest}
    for key, row in package_tables.items():
        file_row = manifest[key]
        census_row = census[key]
        init = initialization[key]
        if (int(row["sourceBytes"]) != int(file_row["Length"])
                or row["sourceSha256"].upper() != file_row["SHA256"].upper()):
            raise SystemExit(f"manifest identity mismatch in UELib rows: {row['package']}")
        if (int(row["exportCount"]) != int(census_row["exports"])
                or int(row["importCount"]) != int(census_row["imports"])):
            raise SystemExit(f"package table count mismatch with UModel: {row['package']}")
        if (init["sourceSha256"].upper() != file_row["SHA256"].upper()
                or init.get("initializationError")):
            raise SystemExit(f"initialization identity/error mismatch: {row['package']}")
        package_metrics[key].update({
            "export_count": int(row["exportCount"]),
            "import_count": int(row["importCount"]),
            "table_object_count": int(row["objectRows"]),
            "initialized_object_count": int(init["initializedObjects"]),
            "initialized_edge_count": int(init["initializedEdges"]),
            "default_property_rows": int(init["defaultProperties"]),
            "default_property_reference_mentions": int(init["defaultPropertyReferenceMentions"]),
        })

    run_summaries = []
    for line in args.run_log.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("{"):
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "packagesInScope" in candidate:
                run_summaries.append(candidate)
    if not run_summaries:
        raise SystemExit("full-run terminal summary is missing from the supplied run log")
    terminal = run_summaries[-1]
    if (terminal.get("packagesInScope") != 904 or terminal.get("processed") != 904
            or terminal.get("failed") != 0 or terminal.get("initializeObjects") is not True
            or terminal.get("outputDir") != str(args.run_dir.resolve())):
        raise SystemExit(f"run log does not show a successful complete pass: {terminal}")

    overall = Counter()
    by_group: dict[str, Counter[str]] = defaultdict(Counter)
    by_class: dict[str, Counter[str]] = {label: Counter() for label in set(CLASS_CROSSWALK.values())}
    per_package_class: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    by_on_demand_class: dict[str, Counter[str]] = defaultdict(Counter)
    on_demand_class_packages: dict[str, set[str]] = defaultdict(set)
    on_demand_class_wrappers: dict[str, set[str]] = defaultdict(set)
    on_demand_failures: list[dict[str, Any]] = []
    baseline_on_demand_overlaps: list[dict[str, Any]] = []
    baseline_owner_mismatches: list[dict[str, Any]] = []
    prior_owner_rows_seen: set[tuple[str, int]] = set()
    total_object_rows = 0
    with (args.run_dir / "initialized-objects.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row["package"].replace("\\", "/").casefold()
            label = row.get("exportClassName")
            group = group_name(row["package"])
            state = row.get("deserializationState") or "<null>"
            count = int(row.get("defaultPropertyCount") or 0)
            attempted = bool(row.get("onDemandLoadAttempted"))
            load_error = bool(row.get("onDemandLoadError"))
            thrown = bool(row.get("exceptionType"))
            counters = package_metrics[key]
            owner_key = (key, int(row.get("packageIndex") or 0))
            prior_count = prior_owner_rows.get(owner_key, 0)
            if prior_count:
                prior_owner_rows_seen.add(owner_key)
                if prior_count != count:
                    baseline_owner_mismatches.append({
                        "package": row["package"],
                        "package_index": row.get("packageIndex"),
                        "object_name": row.get("objectName"),
                        "export_class_label": row.get("exportClassName"),
                        "exp_0070_property_rows": prior_count,
                        "current_property_rows": count,
                    })
                if attempted:
                    baseline_on_demand_overlaps.append({
                        "package": row["package"],
                        "package_index": row.get("packageIndex"),
                        "object_name": row.get("objectName"),
                        "export_class_label": row.get("exportClassName"),
                        "object_type": row.get("objectType"),
                        "prior_property_rows": prior_count,
                        "current_property_rows": count,
                        "deserialization_state": state,
                    })
            counters["initialized_rows_seen"] += 1
            counters[f"state:{state}"] += 1
            counters["objects_with_default_property_rows"] += count > 0
            counters["default_property_rows_from_objects"] += count
            counters["default_property_rows_not_from_on_demand_attempts"] += count if not attempted else 0
            if row.get("shouldDeserializeOnDemand"):
                counters["should_deserialize_on_demand"] += 1
            if attempted:
                counters["on_demand_attempted"] += 1
                counters["on_demand_objects_with_default_property_rows"] += count > 0
                counters["on_demand_default_property_rows"] += count
                counters["on_demand_state:" + state] += 1
                counters["on_demand_diagnostic_lines"] += int(row.get("onDemandDiagnosticLineCount") or 0)
                counters["on_demand_load_errors"] += load_error
                counters["on_demand_thrown_exceptions"] += thrown
                label = row.get("exportClassName") or "<null>"
                type_bucket = by_on_demand_class[label]
                type_bucket["attempted"] += 1
                type_bucket[f"state:{state}"] += 1
                type_bucket["objects_with_properties"] += count > 0
                type_bucket["property_rows"] += count
                type_bucket["diagnostic_lines"] += int(row.get("onDemandDiagnosticLineCount") or 0)
                type_bucket["escaped_errors"] += load_error
                type_bucket["recorded_exceptions"] += thrown
                on_demand_class_packages[label].add(key)
                on_demand_class_wrappers[label].add(row.get("objectType") or "<null>")
                if state == "Errorlized" or thrown or load_error:
                    on_demand_failures.append({
                        "package": row["package"],
                        "package_index": row.get("packageIndex"),
                        "export_class_label": label,
                        "object_type": row.get("objectType"),
                        "object_name": row.get("objectName"),
                        "object_path": row.get("objectPath"),
                        "deserialization_state": state,
                        "exception_type": row.get("exceptionType"),
                        "exception_message": row.get("exceptionMessage"),
                        "escaped_load_error": row.get("onDemandLoadError"),
                        "diagnostic_lines": row.get("onDemandDiagnosticLineCount"),
                        "diagnostic_sample": row.get("onDemandDiagnosticSample"),
                    })
            if row.get("table") == "export" and label in by_class:
                bucket = by_class[label]
                pkg_bucket = per_package_class[(key, label)]
                for target in (bucket, pkg_bucket):
                    target["exports"] += 1
                    target["unknown_object"] += row.get("objectType") == "UnknownObject"
                    target["should_on_demand"] += bool(row.get("shouldDeserializeOnDemand"))
                    target["on_demand_attempted"] += attempted
                    target[f"state:{state}"] += 1
                    target[f"on_demand_state:{state}"] += attempted
                    target["objects_with_properties"] += count > 0
                    target["property_rows"] += count
                    target["load_diagnostic_lines"] += int(row.get("onDemandDiagnosticLineCount") or 0)
                    target["load_errors"] += load_error
                    target["thrown_exceptions"] += thrown
            total_object_rows += 1
            overall["initialized_rows_seen"] += 1
            overall[f"state:{state}"] += 1
            overall["default_property_rows_from_objects"] += count
            overall["default_property_rows_not_from_on_demand_attempts"] += count if not attempted else 0
            overall["objects_with_default_property_rows"] += count > 0
            overall["should_deserialize_on_demand"] += bool(row.get("shouldDeserializeOnDemand"))
            overall["on_demand_attempted"] += attempted
            overall[f"on_demand_state:{state}"] += attempted
            overall["on_demand_objects_with_default_property_rows"] += attempted and count > 0
            overall["on_demand_default_property_rows"] += count if attempted else 0
            overall["on_demand_load_errors"] += load_error
            overall["on_demand_thrown_exceptions"] += thrown
            overall["on_demand_diagnostic_lines"] += int(row.get("onDemandDiagnosticLineCount") or 0)
            by_group[group]["initialized_rows_seen"] += 1
            by_group[group][f"state:{state}"] += 1
            by_group[group]["default_property_rows"] += count
            by_group[group]["objects_with_default_property_rows"] += count > 0
            by_group[group]["should_deserialize_on_demand"] += bool(row.get("shouldDeserializeOnDemand"))
            by_group[group]["on_demand_attempted"] += attempted
            by_group[group]["on_demand_load_errors"] += load_error
            by_group[group]["on_demand_thrown_exceptions"] += thrown

    package_row_mismatches = [
        key for key, counters in package_metrics.items()
        if counters["initialized_rows_seen"] != counters["table_object_count"]
        or counters["initialized_rows_seen"] != counters["initialized_object_count"]
        or counters["default_property_rows_from_objects"] != counters["default_property_rows"]
    ]
    if package_row_mismatches:
        raise SystemExit(f"initialized/default row mismatch in {len(package_row_mismatches)} packages: {package_row_mismatches[:5]}")

    property_value_diagnostics = Counter()
    with (args.run_dir / "default-properties.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            property_value_diagnostics["rows"] += 1
            property_value_diagnostics["value_errors"] += bool(row.get("valueError"))
            property_value_diagnostics["diagnostic_lines"] += int(row.get("valueDiagnosticLineCount") or 0)
            property_value_diagnostics["rows_with_diagnostics"] += int(row.get("valueDiagnosticLineCount") or 0) > 0

    group_rows = []
    for group, counters in sorted(by_group.items()):
        group_rows.append({"group": group, **dict(counters)})
    package_rows = []
    for key, row in sorted(package_tables.items()):
        previous = prior_defaults[key]
        package_rows.append({
            "relative_path": row["package"],
            "group": group_name(row["package"]),
            "exp_0070_default_property_rows": previous,
            "current_default_property_rows_after_on_demand": package_metrics[key]["default_property_rows_from_objects"],
            "property_row_increase_vs_exp_0070": package_metrics[key]["default_property_rows_from_objects"] - previous,
            **dict(package_metrics[key]),
            "package_error_row": False,
        })
    class_rows = []
    for umodel_class, uelib_label in CLASS_CROSSWALK.items():
        counters = by_class[uelib_label]
        packages_class = sum(per_package_class[(key, uelib_label)]["exports"] > 0 for key in manifest)
        packages_attempted = sum(per_package_class[(key, uelib_label)]["on_demand_attempted"] > 0 for key in manifest)
        class_rows.append({
            "umodel_fake_class": umodel_class,
            "uelib_export_class_label": uelib_label,
            "uelib_exports": counters["exports"],
            "uelib_unknown_object_exports": counters["unknown_object"],
            "should_deserialize_on_demand": counters["should_on_demand"],
            "on_demand_attempted": counters["on_demand_attempted"],
            "uelib_deserialized_exports": counters["state:Deserialized"],
            "uelib_errorlized_exports": counters["state:Errorlized"],
            "on_demand_deserialized": counters["on_demand_state:Deserialized"],
            "on_demand_errorlized": counters["on_demand_state:Errorlized"],
            "objects_with_default_property_rows": counters["objects_with_properties"],
            "default_property_rows": counters["property_rows"],
            "on_demand_load_diagnostic_lines": counters["load_diagnostic_lines"],
            "on_demand_escaped_call_errors": counters["load_errors"],
            "on_demand_recorded_exceptions": counters["thrown_exceptions"],
            "packages_with_exports": packages_class,
            "packages_with_on_demand_attempts": packages_attempted,
            "claim": "aggregate class-label correspondence only; not an object-level UModel join",
        })
    on_demand_class_rows = []
    for label, counters in sorted(by_on_demand_class.items(), key=lambda item: (-item[1]["attempted"], item[0].casefold())):
        wrappers = ";".join(sorted(on_demand_class_wrappers[label]))
        on_demand_class_rows.append({
            "export_class_label": label,
            "uelib_wrapper_types": wrappers,
            "packages": len(on_demand_class_packages[label]),
            "on_demand_attempted": counters["attempted"],
            "on_demand_deserialized": counters["state:Deserialized"],
            "on_demand_errorlized": counters["state:Errorlized"],
            "on_demand_state_zero": counters["state:0"],
            "objects_with_default_property_rows": counters["objects_with_properties"],
            "default_property_rows": counters["property_rows"],
            "load_diagnostic_lines": counters["diagnostic_lines"],
            "escaped_load_errors": counters["escaped_errors"],
            "recorded_exceptions": counters["recorded_exceptions"],
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        ("by-group.csv", group_rows),
        ("by-package.csv", package_rows),
        ("by-export-class.csv", class_rows),
        ("on-demand-by-export-class.csv", on_demand_class_rows),
        ("on-demand-failures.csv", on_demand_failures),
        ("baseline-on-demand-overlap.csv", baseline_on_demand_overlaps),
        ("baseline-owner-count-mismatches.csv", baseline_owner_mismatches),
    ]
    for filename, rows in outputs:
        with (args.output_dir / filename).open("w", encoding="utf-8", newline="") as stream:
            fieldnames = list(dict.fromkeys(field for row in rows for field in row))
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    summary = {
        "scope": "all 904 packages in BUILD-STEAM-10256413 manifest",
        "package_count": len(manifest),
        "package_source_hash_size_matches": 904,
        "package_table_counts_match_umodel_census": 904,
        "package_initialization_errors": 0,
        "package_extraction_errors": package_errors,
        "terminal_log_processed_packages": terminal["processed"],
        "terminal_log_failed_packages": terminal["failed"],
        "package_row_reconciliation_errors": len(package_row_mismatches),
        "table_objects": sum(x["table_object_count"] for x in package_metrics.values()),
        "initialized_object_rows": total_object_rows,
        "on_demand_attempts": overall["on_demand_attempted"],
        "on_demand_state_counts": {
            state.removeprefix("on_demand_state:"): count
            for state, count in overall.items() if state.startswith("on_demand_state:") and count
        },
        "on_demand_escaped_call_errors": overall["on_demand_load_errors"],
        "on_demand_thrown_exceptions": overall["on_demand_thrown_exceptions"],
        "on_demand_diagnostic_lines": overall["on_demand_diagnostic_lines"],
        "objects_with_default_property_rows": overall["objects_with_default_property_rows"],
        "default_property_rows": overall["default_property_rows_from_objects"],
        "on_demand_objects_with_default_property_rows": overall["on_demand_objects_with_default_property_rows"],
        "on_demand_default_property_rows": overall["on_demand_default_property_rows"],
        "exp_0070_default_property_rows": sum(prior_defaults.values()),
        "exp_0070_property_owners_reconciled": len(prior_owner_rows_seen),
        "exp_0070_property_owners_missing": len(set(prior_owner_rows) - prior_owner_rows_seen),
        "exp_0070_owner_property_row_count_mismatches": len(baseline_owner_mismatches),
        "exp_0070_rows_belonging_to_on_demand_attempted_objects": sum(
            row["prior_property_rows"] for row in baseline_on_demand_overlaps
        ),
        "net_new_property_rows_after_on_demand_load": (
            overall["default_property_rows_from_objects"] - sum(prior_defaults.values())
        ),
        "new_rows_emitted_by_on_demand_objects_after_baseline_overlap": (
            overall["on_demand_default_property_rows"]
            - sum(row["prior_property_rows"] for row in baseline_on_demand_overlaps)
        ),
        "on_demand_property_value_diagnostics": {
            "total_default_property_rows": property_value_diagnostics["rows"],
            "value_errors_across_all_rows": property_value_diagnostics["value_errors"],
            "captured_diagnostic_lines_for_on_demand_rows": property_value_diagnostics["diagnostic_lines"],
            "on_demand_rows_with_captured_diagnostics": property_value_diagnostics["rows_with_diagnostics"],
        },
        "overall_deserialization_states": {
            state.removeprefix("state:"): count for state, count in overall.items() if state.startswith("state:")
        },
        "uelib_claim": "Load() results and parser-formatted fields only; property-value diagnostics are captured for on-demand-loaded objects, and success state does not guarantee every property/array value decoded without diagnostics.",
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
