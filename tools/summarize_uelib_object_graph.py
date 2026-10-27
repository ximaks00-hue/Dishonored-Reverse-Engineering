#!/usr/bin/env python3
"""Build bounded-memory object, inheritance and reference catalogs from UELib JSONL."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


def rows(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def csv_writer(path: Path, fields: list[str], compressed: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = gzip.open(path, "wt", encoding="utf-8", newline="", compresslevel=6) if compressed else path.open("w", encoding="utf-8", newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    return stream, writer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.run_dir / "initialized-objects.jsonl"
    if not input_path.is_file():
        raise SystemExit(f"missing input file: {input_path}")

    with tempfile.TemporaryDirectory(prefix="uelib-object-graph-") as temp:
        db_path = Path(temp) / "index.sqlite"
        db = sqlite3.connect(db_path)
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("PRAGMA temp_store=FILE")
        db.execute("PRAGMA cache_size=-65536")
        db.execute("""CREATE TABLE objects (
            package TEXT NOT NULL, package_index INTEGER NOT NULL,
            object_type TEXT, object_name TEXT, object_path TEXT,
            object_path_key TEXT,
            class_path TEXT, outer_path TEXT, archetype_path TEXT,
            default_object_path TEXT, super_path TEXT, next_field_path TEXT,
            property_type_reference_path TEXT, export_class_name TEXT,
            import_class_name TEXT, default_property_count INTEGER,
            deserialization_state TEXT, exception_type TEXT,
            PRIMARY KEY(package, package_index)) WITHOUT ROWID""")
        batch: list[tuple[Any, ...]] = []
        object_count = 0
        for row in rows(input_path):
            batch.append((
                row["package"], int(row["packageIndex"]), row.get("objectType"),
                row.get("objectName"), row.get("objectPath"),
                (row.get("objectPath").split("'",1)[1].rsplit("'",1)[0] if row.get("objectPath") and "'" in row["objectPath"] else row.get("objectPath")),
                row.get("classPath"),
                row.get("outerPath"), row.get("archetypePath"), row.get("defaultObjectPath"),
                row.get("superPath"), row.get("nextFieldPath"), row.get("propertyTypeReferencePath"),
                row.get("exportClassName"), row.get("importClassName"),
                int(row.get("defaultPropertyCount") or 0), row.get("deserializationState"),
                row.get("exceptionType"),
            ))
            object_count += 1
            if len(batch) >= 10000:
                db.executemany("INSERT INTO objects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                db.commit()
                batch.clear()
        if batch:
            db.executemany("INSERT INTO objects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            db.commit()
        object_packages = int(db.execute("SELECT count(DISTINCT package) FROM objects").fetchone()[0])
        duplicate_index_count = object_count - int(db.execute("SELECT count(*) FROM objects").fetchone()[0])
        db.execute("CREATE INDEX object_path_lookup ON objects(package, object_path_key, export_class_name, import_class_name)")
        db.execute("CREATE INDEX object_class_examples ON objects(package, object_type, export_class_name, import_class_name, class_path, package_index, object_path)")
        db.execute("CREATE INDEX object_property_type_examples ON objects(object_type, property_type_reference_path, package, package_index, object_path)")
        db.commit()

        class_fields = ["package", "object_type", "export_or_import_class_label", "class_path", "object_rows", "rows_with_object_path", "default_property_rows", "sample_object_paths", "claim"]
        class_stream, class_writer = csv_writer(args.output_dir / "uelib-class-object-catalog.csv", class_fields)
        class_cursor = db.cursor()
        class_sample_cursor = db.cursor()
        class_query = class_cursor.execute("""SELECT package, coalesce(object_type,'<null>'),
            coalesce(export_class_name, import_class_name, '<null>'), coalesce(class_path,'<null>'),
            export_class_name, import_class_name,
            count(*), sum(object_path IS NOT NULL), sum(coalesce(default_property_count,0))
            FROM objects GROUP BY package, object_type, export_class_name, import_class_name, class_path
            ORDER BY package, object_type, export_class_name, import_class_name, class_path""")
        class_rows = 0
        for package, obj_type, label, class_path, export_label, import_label, count, path_count, default_count in class_query:
            samples = [x[0] for x in class_sample_cursor.execute("""SELECT object_path FROM objects WHERE package=?
                AND object_type IS ? AND export_class_name IS ? AND import_class_name IS ? AND class_path IS ?
                AND object_path IS NOT NULL ORDER BY package_index LIMIT 5""",
                (package, None if obj_type == "<null>" else obj_type,
                 export_label, import_label,
                 None if class_path == "<null>" else class_path))]
            class_writer.writerow({"package": package, "object_type": obj_type,
                "export_or_import_class_label": label, "class_path": class_path,
                "object_rows": count, "rows_with_object_path": path_count,
                "default_property_rows": default_count,
                "sample_object_paths": json.dumps(samples, ensure_ascii=False),
                "claim": "UELib initialized API object category; parser model only"})
            class_rows += 1
        class_stream.close()

        inheritance_fields = ["package", "object_path", "super_path", "object_type", "claim"]
        inheritance_stream, inheritance_writer = csv_writer(args.output_dir / "uelib-inheritance-relations.csv.gz", inheritance_fields, compressed=True)
        inheritance_query = db.execute("SELECT package, object_path, super_path, object_type FROM objects WHERE super_path IS NOT NULL ORDER BY package, package_index")
        inheritance_count = 0
        for package, object_path, super_path, obj_type in inheritance_query:
            inheritance_writer.writerow({"package": package, "object_path": object_path or "<null>",
                "super_path": super_path, "object_type": obj_type or "<null>",
                "claim": "UELib parsed Super relation; not runtime inheritance behavior"})
            inheritance_count += 1
        inheritance_stream.close()

        relation_fields = ["package", "source_object_path", "relation", "target_object_path", "claim"]
        relation_stream, relation_writer = csv_writer(args.output_dir / "uelib-initialized-object-relations.csv.gz", relation_fields, compressed=True)
        relation_count = 0
        edge_counts: Counter[str] = Counter()
        for package, package_index, source_path, class_path, outer_path, archetype_path, default_path, super_path, next_field, type_ref in db.execute("""SELECT package, package_index, object_path, class_path, outer_path,
            archetype_path, default_object_path, super_path, next_field_path, property_type_reference_path FROM objects ORDER BY package, package_index"""):
            for relation, target in (("class",class_path),("outer",outer_path),("archetype",archetype_path),
                ("default_object",default_path),("super",super_path),("next_field",next_field),
                ("property_type",type_ref)):
                if target:
                    relation_writer.writerow({"package":package,"source_object_path":source_path or "<null>",
                        "relation":relation,"target_object_path":target,
                        "claim":"UELib initialized object field relation; parser model only"})
                    relation_count += 1
                    edge_counts[relation] += 1
        relation_stream.close()

        prop_fields = ["object_type", "property_type_reference_path", "rows", "sample_object_paths", "claim"]
        prop_stream, prop_writer = csv_writer(args.output_dir / "uelib-property-type-reference-catalog.csv", prop_fields)
        prop_count = 0
        prop_cursor = db.cursor()
        prop_sample_cursor = db.cursor()
        for obj_type, target, count in prop_cursor.execute("""SELECT object_type, property_type_reference_path, count(*)
            FROM objects WHERE property_type_reference_path IS NOT NULL
            GROUP BY object_type, property_type_reference_path ORDER BY count(*) DESC, object_type, property_type_reference_path"""):
            samples = [x[0] for x in prop_sample_cursor.execute("SELECT object_path FROM objects WHERE object_type IS ? AND property_type_reference_path=? AND object_path IS NOT NULL ORDER BY package,package_index LIMIT 10", (obj_type,target))]
            prop_writer.writerow({"object_type":obj_type or "<null>","property_type_reference_path":target,
                "rows":count,"sample_object_paths":json.dumps(samples,ensure_ascii=False),
                "claim":"UELib structured property-type field"})
            prop_count += 1
        prop_stream.close()

        mention_fields = ["package", "owner_object_path", "property_name", "reference_class_label", "reference_object_path", "mentions", "same_package_path_rows", "matching_export_class_rows", "claim"]
        mention_stream, mention_writer = csv_writer(args.output_dir / "uelib-default-property-reference-mentions.csv", mention_fields)
        unmatched_fields = ["package", "owner_object_path", "property_name", "reference_class_label", "reference_object_path", "mentions", "claim"]
        unmatched_stream, unmatched_writer = csv_writer(args.output_dir / "uelib-unmatched-default-reference-mentions.csv", unmatched_fields)
        mention_counts: Counter[tuple[str,str,str,str,str]] = Counter()
        target_pairs: set[tuple[str,str]] = set()
        path_hit_mentions = 0
        class_hit_mentions = 0
        unmatched_distinct = 0
        for row in rows(args.run_dir / "default-property-reference-mentions.jsonl"):
            package=row["package"]; owner=row.get("ownerObjectPath") or "<null>"
            prop=row.get("propertyName") or "<null>"; label=row["referenceClassLabel"]
            target=row["referenceObjectPath"]
            mention_counts[(package,owner,prop,label,target)] += 1
        total_mentions=sum(mention_counts.values())
        for (package,owner,prop,label,target), count in sorted(mention_counts.items()):
            target_pairs.add((package,target))
            path_rows=int(db.execute("SELECT count(*) FROM objects WHERE package=? AND object_path_key=?",(package,target)).fetchone()[0])
            matching_class_path_rows=int(db.execute("SELECT count(*) FROM objects WHERE package=? AND object_path_key=? AND coalesce(export_class_name,import_class_name,'<null>')=?",(package,target,label)).fetchone()[0])
            if path_rows: path_hit_mentions += count
            if matching_class_path_rows: class_hit_mentions += count
            record={"package":package,"owner_object_path":owner,"property_name":prop,
                "reference_class_label":label,"reference_object_path":target,"mentions":count,
                "same_package_path_rows":path_rows,"matching_export_class_rows":matching_class_path_rows,
                "claim":"mention parsed from UELib formatted property text; not structured reference proof"}
            mention_writer.writerow(record)
            if not path_rows:
                unmatched_distinct += 1
                unmatched_writer.writerow({key: record[key] for key in unmatched_fields if key != "claim"} | {"claim":"formatted reference target path absent from same-package UELib object paths"})
        mention_stream.close(); unmatched_stream.close()

        # Verify edge source-index coverage and exact relation totals against the emitted edge JSONL.
        edge_rows=0; missing_edge_source=0; edge_unmatched_path=0; parsed_edge_counts:Counter[str]=Counter()
        for edge in rows(args.run_dir / "initialized-edges.jsonl"):
            edge_rows += 1; parsed_edge_counts[edge["relation"]]+=1
            found=db.execute("SELECT object_path FROM objects WHERE package=? AND package_index=?",(edge["package"],int(edge["fromPackageIndex"]))).fetchone()
            if found is None: missing_edge_source += 1
            elif found[0] != edge.get("fromObjectPath"): edge_unmatched_path += 1

        summary={"input_object_rows":object_count,"input_package_count":object_packages,
            "duplicate_package_indices":duplicate_index_count,"class_catalog_rows":class_rows,
            "inheritance_relation_rows":inheritance_count,"property_type_reference_rows":prop_count,
            "initialized_relation_rows_rebuilt_from_object_fields":relation_count,
            "initialized_relation_counts_rebuilt":dict(sorted(edge_counts.items())),
            "initialized_edge_jsonl_rows":edge_rows,"initialized_edge_jsonl_relation_counts":dict(sorted(parsed_edge_counts.items())),
            "initialized_edges_missing_source_package_index":missing_edge_source,
            "initialized_edges_source_path_mismatches":edge_unmatched_path,
            "default_property_reference_mentions":total_mentions,
            "distinct_formatted_reference_relation_rows":len(mention_counts),
            "distinct_package_reference_target_pairs":len(target_pairs),
            "reference_mentions_matching_same_package_object_path":path_hit_mentions,
            "reference_mentions_matching_same_package_path_and_export_class":class_hit_mentions,
            "distinct_unmatched_reference_relation_rows":unmatched_distinct,
            "limits":["UELib API/parser output only; no complete UE3 payload or runtime semantics claim.",
                "Default-property references are text mentions extracted from formatted values and are not structured serialized references.",
                "Same-package path and class counts are internal parser-output consistency checks; duplicate formatted paths are retained as counts."]}
        (args.output_dir / "uelib-object-graph-summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps(summary,indent=2,ensure_ascii=False))
        db.close()


if __name__ == "__main__":
    main()
