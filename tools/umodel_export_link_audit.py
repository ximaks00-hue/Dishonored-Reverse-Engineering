#!/usr/bin/env python3
"""Audit UModel export catalog links and import-name resolution coverage.

This derives candidate package-local object relations from UModel's displayed
outer-qualified export labels and measures import-name matches against the
installed export catalog. It does not parse UE3 serialized object references.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def package_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_object_path(value: str) -> tuple[str, str]:
    value = value.strip().replace("\\", "/")
    outer, dot, name = value.rpartition(".")
    return (outer, name) if dot else ("", value)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--census", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{args.catalog.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    manifest = {
        row["RelativePath"].replace("\\", "/").casefold(): row
        for row in package_rows(args.manifest)
    }
    census = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in package_rows(args.census)
    }

    packages = conn.execute(
        "SELECT relative_path, bytes, sha256, exports, imports, listed_objects, "
        "warning_lines, error_lines, list_status FROM packages ORDER BY relative_path"
    ).fetchall()
    if len(packages) != 904:
        raise SystemExit(f"expected 904 catalog packages, found {len(packages)}")

    package_exports = {
        row["relative_path"].replace("\\", "/").casefold(): int(row["n"])
        for row in conn.execute(
            "SELECT relative_path, COUNT(*) AS n FROM objects GROUP BY relative_path"
        )
    }
    export_total = sum(package_exports.values())

    package_check_rows: list[dict[str, Any]] = []
    missing_packages: list[str] = []
    for pkg in packages:
        key = pkg["relative_path"].replace("\\", "/").casefold()
        m = manifest.get(key)
        c = census.get(key)
        actual = package_exports[key]
        package_check_rows.append(
            {
                "relative_path": pkg["relative_path"],
                "catalog_bytes": pkg["bytes"],
                "manifest_bytes": int(m["Length"]) if m else "",
                "catalog_sha256": pkg["sha256"],
                "manifest_sha256": m["SHA256"] if m else "",
                "census_exports": int(c["exports"]) if c else "",
                "catalog_exports": pkg["exports"],
                "listed_objects": pkg["listed_objects"],
                "actual_object_rows": actual,
                "imports": pkg["imports"],
                "list_status": pkg["list_status"],
                "manifest_match": bool(
                    m
                    and int(m["Length"]) == pkg["bytes"]
                    and m["SHA256"].casefold() == pkg["sha256"].casefold()
                ),
                "export_count_match": (
                    actual == pkg["exports"] == pkg["listed_objects"]
                    and c is not None
                    and int(c["exports"]) == actual
                ),
            }
        )
        if not m or not c:
            missing_packages.append(pkg["relative_path"])
    for r in package_check_rows:
        r["manifest_match"] = str(r["manifest_match"]).lower()
        r["export_count_match"] = str(r["export_count_match"]).lower()
    with (output_dir / "package-reconciliation.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(package_check_rows[0]))
        w.writeheader()
        w.writerows(package_check_rows)

    # Candidate export links are package-local outer/name relationships from
    # UModel's printed object path. They are not serialized UE3 references.
    candidates: list[dict[str, Any]] = []
    candidate_counts: Counter[str] = Counter()
    for pkg in packages:
        p = pkg["relative_path"]
        key = p.casefold()
        obj_rows = conn.execute(
            "SELECT export_index, object_class, object_name FROM objects "
            "WHERE relative_path = ? ORDER BY export_index",
            (p,),
        ).fetchall()
        local_names: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for er in obj_rows:
            nm = er["object_name"]
            local_names[nm.casefold()].append(
                {"export_index": er["export_index"], "object_name": nm, "object_class": er["object_class"]}
            )
            if "." in nm:
                local_names[nm.rsplit(".", 1)[1].casefold()].append(
                    {"export_index": er["export_index"], "object_name": nm, "object_class": er["object_class"]}
                )
        for er in obj_rows:
            outer, leaf = split_object_path(er["object_name"])
            if not outer:
                continue
            matches = local_names.get(outer.casefold(), [])
            if len(matches) != 1:
                candidate_counts["unresolved_outer" if not matches else "ambiguous_outer"] += 1
                continue
            parent = matches[0]
            candidates.append(
                {
                    "relative_path": p,
                    "export_index": er["export_index"],
                    "object_class": er["object_class"],
                    "object_name": er["object_name"],
                    "outer_label": outer,
                    "leaf_label": leaf,
                    "candidate_outer_export_index": parent["export_index"],
                    "candidate_outer_name": parent["object_name"],
                    "candidate_outer_class": parent["object_class"],
                    "claim": "candidate_from_umodel_label_only",
                }
            )
            candidate_counts["unique_outer_candidate"] += 1
    if candidates:
        with (output_dir / "candidate-export-outer-links.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(candidates[0]))
            w.writeheader()
            w.writerows(candidates)

    summary = {
        "catalog_package_rows": len(packages),
        "catalog_export_rows": export_total,
        "manifest_rows": len(manifest),
        "census_rows": len(census),
        "package_rows_manifest_and_census_absent": len(missing_packages),
        "manifest_hash_and_size_matches": sum(r["manifest_match"] == "true" for r in package_check_rows),
        "per_package_export_count_matches": sum(r["export_count_match"] == "true" for r in package_check_rows),
        "candidate_export_outer_links": dict(candidate_counts),
        "import_resolution": {
            "status": "unavailable_from_export_only_UModel_catalog",
            "note": "The current catalog stores export labels only; it has no import table or serialized object-reference fields.",
        },
        "limitations": [
            "UModel -list label strings do not establish serialized UE3 outer, class, super, or object-reference values.",
            "Candidate outer links are generated only when one local export label uniquely matches the displayed outer prefix.",
            "No package export, property decode, bytecode decode, or runtime reachability was performed.",
        ],
        "missing_package_examples": missing_packages[:10],
        "candidate_link_rows": len(candidates),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
