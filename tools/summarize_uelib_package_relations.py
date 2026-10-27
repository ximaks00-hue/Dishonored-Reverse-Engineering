#!/usr/bin/env python3
"""Reconcile full-install UELib package tables and summarize import roots."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relations-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--pkginfo-census", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    manifest_rows = read_csv(args.manifest)
    census_rows = read_csv(args.pkginfo_census)
    manifest = {row["RelativePath"].replace("\\", "/").casefold(): row for row in manifest_rows}
    census = {row["relative_path"].replace("\\", "/").casefold(): row for row in census_rows}
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    summaries = [
        json.loads(line)
        for line in (args.relations_dir / "package-summary.jsonl").open(encoding="utf-8")
        if line.strip()
    ]
    expected_keys = set(manifest)
    if set(census) != expected_keys:
        raise SystemExit(
            f"manifest/census package sets differ: manifest={len(manifest)} census={len(census)}"
        )
    summary_keys = {row["package"].replace("\\", "/").casefold() for row in summaries}
    if summary_keys != expected_keys or len(summaries) != len(expected_keys):
        raise SystemExit(
            "summary/manifest package sets differ: "
            f"summary={len(summaries)} manifest={len(expected_keys)} "
            f"missing={len(expected_keys - summary_keys)} extra={len(summary_keys - expected_keys)}"
        )
    package_rows: list[dict[str, object]] = []
    link_totals: Counter[str] = Counter()
    mismatch_count = 0
    for row in summaries:
        key = row["package"].replace("\\", "/").casefold()
        manifest_row = manifest.get(key)
        census_row = census.get(key)
        if not manifest_row or not census_row:
            mismatch_count += 1
        hash_match = bool(
            manifest_row
            and int(manifest_row["Length"]) == row["sourceBytes"]
            and manifest_row["SHA256"].casefold() == row["sourceSha256"].casefold()
        )
        exports_match = bool(census_row and int(census_row["exports"]) == row["exportCount"])
        imports_match = bool(census_row and int(census_row["imports"]) == row["importCount"])
        if not (hash_match and exports_match and imports_match):
            mismatch_count += 1
        for relation, count in row["links"].items():
            link_totals[relation] += count
        package_rows.append(
            {
                "relative_path": row["package"],
                "source_bytes": row["sourceBytes"],
                "source_sha256": row["sourceSha256"],
                "package_version": row["packageVersion"],
                "licensee_version": row["licenseeVersion"],
                "uelib_exports": row["exportCount"],
                "census_exports": census_row["exports"] if census_row else "",
                "uelib_imports": row["importCount"],
                "census_imports": census_row["imports"] if census_row else "",
                **row["links"],
                "manifest_hash_size_match": str(hash_match).lower(),
                "census_count_match": str(exports_match and imports_match).lower(),
            }
        )
    fields = list(package_rows[0]) if package_rows else []
    write_csv(output / "uelib-package-table-coverage.csv", package_rows, fields)

    packages_by_stem: dict[str, list[str]] = defaultdict(list)
    for row in manifest_rows:
        if row["RelativePath"].casefold().endswith(".upk"):
            packages_by_stem[Path(row["RelativePath"]).stem.casefold()].append(
                row["RelativePath"].replace("\\", "/")
            )

    import_roots: Counter[tuple[str, str]] = Counter()
    import_examples: dict[tuple[str, str], list[str]] = defaultdict(list)
    parsed_import_rows = 0
    object_path = args.relations_dir / "package-objects.jsonl"
    with object_path.open(encoding="utf-8") as stream:
        for line in stream:
            if '"table":"import"' not in line:
                continue
            row = json.loads(line)
            source = row["package"].replace("\\", "/")
            package_name = row.get("packageName", "")
            if not package_name:
                continue
            key = (source, package_name)
            import_roots[key] += 1
            parsed_import_rows += 1
            examples = import_examples[key]
            if len(examples) < 3:
                examples.append(row["objectName"])

    import_edge_rows: list[dict[str, object]] = []
    resolution_counts: Counter[str] = Counter()
    for (source, package_name), count in sorted(import_roots.items()):
        candidates = packages_by_stem.get(package_name.casefold(), [])
        if len(candidates) == 1:
            status = "unique_filename_stem_candidate"
        elif len(candidates) > 1:
            status = "ambiguous_filename_stem"
        else:
            status = "no_filename_stem_match"
        resolution_counts[status] += 1
        import_edge_rows.append(
            {
                "source_package": source,
                "import_package_name": package_name,
                "import_table_rows": count,
                "candidate_target_paths": json.dumps(candidates, ensure_ascii=False),
                "resolution_status": status,
                "sample_imported_object_names": json.dumps(import_examples[(source, package_name)], ensure_ascii=False),
                "claim": "import_table_package_name_and_filename_stem_candidate_only",
            }
        )
    if import_edge_rows:
        write_csv(
            output / "uelib-import-package-candidates.csv",
            import_edge_rows,
            list(import_edge_rows[0]),
        )

    unresolved_marker = b'"target":"unresolved:'
    unresolved_index_rows = 0
    tail = b""
    with (args.relations_dir / "package-edges.jsonl").open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            data = tail + chunk
            unresolved_index_rows += data.count(unresolved_marker)
            tail = data[-(len(unresolved_marker) - 1) :]

    summary = {
        "package_summary_rows": len(summaries),
        "manifest_package_rows": len(manifest),
        "independent_pkginfo_rows": len(census),
        "package_hash_size_and_export_import_count_mismatches": mismatch_count,
        "total_export_table_rows": sum(row["uelib_exports"] for row in package_rows),
        "total_import_table_rows": sum(row["uelib_imports"] for row in package_rows),
        "serialized_index_reference_counts": dict(link_totals),
        "unresolved_package_table_index_rows": unresolved_index_rows,
        "all_non_null_package_indices_resolved_within_local_tables": unresolved_index_rows == 0,
        "import_root_rows_parsed": parsed_import_rows,
        "source_package_to_import_root_pairs": len(import_edge_rows),
        "package_name_to_filename_stem_candidates": dict(resolution_counts),
        "limitations": [
            "UELib 1.13.3 parsed import/export table indices before object initialization; no property payload or bytecode references were extracted here.",
            "Class, outer, super, template, and archetype links are signed package-table indices resolved only within that package's import/export tables.",
            "An import package name matching an installed UPK filename stem is a candidate path association; duplicate and absent stems remain explicit, and a match does not prove runtime loading.",
            "This census does not recover asset dependencies embedded in binary payloads or UnrealScript property values.",
        ],
    }
    (output / "uelib-package-relations-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
