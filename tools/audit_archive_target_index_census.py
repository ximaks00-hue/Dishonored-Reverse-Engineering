#!/usr/bin/env python3
"""Build a provenance-preserving census of archived UpdateTaskTarget records.

This reads browser/editor CSV exports only. It does not open or parse UPKs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ACTION_CLASS = "DisSeqAct_UpdateTaskTarget"
PROPERTIES = ("m_TargetName", "m_TargetIndex", "m_pTargetActor")
LINK_PROPERTIES = ("InputLinks", "OutputLinks", "VariableLinks")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, required=True)
    parser.add_argument("--links-dir", type=Path, required=True)
    parser.add_argument("--csv-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    actions: dict[tuple[str, str], dict[str, str]] = {}
    inputs: dict[tuple[str, str], dict[str, list[str]]] = {}
    task_definitions: dict[tuple[str, str, str], dict[str, str]] = {}
    task_definitions_by_package_leaf: dict[tuple[str, str], list[dict[str, str]]] = {}
    index_counts: Counter[str] = Counter()
    property_counts: Counter[str] = Counter()
    source_inventory: list[dict[str, str]] = []
    source_links: list[dict[str, str]] = []

    for inventory_path in sorted(args.inventory_dir.glob("*_Script.csv")):
        rows = read_csv(inventory_path)
        action_rows = [row for row in rows if row.get("object_class") == ACTION_CLASS]
        if not action_rows:
            continue
        source_inventory.append({"path": str(inventory_path), "sha256": sha256(inventory_path)})
        package = action_rows[0].get("package", inventory_path.stem.removesuffix("_Script"))
        for row in rows:
            if row.get("object_class") != "DisSeqVar_Task":
                continue
            leaf = row.get("object_path", "").rsplit(".", 1)[-1].rstrip("'")
            key = (package, row.get("sequence_path", ""), leaf)
            definition = task_definitions.setdefault(key, {
                "package": package,
                "sequence_path": row.get("sequence_path", ""),
                "variable": leaf,
            })
            definition[row.get("property_name", "")] = row.get("property_value", "")
        for row in action_rows:
            key = (package, row["object_path"])
            record = actions.setdefault(key, {
                "package": package,
                "object_path": row["object_path"],
                "sequence_path": row.get("sequence_path", ""),
                "inventory_csv": str(inventory_path),
            })
            prop = row.get("property_name", "")
            property_counts[prop] += 1
            if prop in PROPERTIES:
                record[prop] = row.get("property_value", "")

    for package, object_path in sorted(actions):
        action = actions[(package, object_path)]
        link_path = args.links_dir / f"{package}_links.csv"
        if not link_path.is_file():
            continue
        if str(link_path) not in {entry["path"] for entry in source_links}:
            source_links.append({"path": str(link_path), "sha256": sha256(link_path)})
            for row in read_csv(link_path):
                if row.get("object_class") != ACTION_CLASS:
                    continue
                key = (row.get("package", ""), row.get("object_path", ""))
                if key not in actions or row.get("property_name") not in LINK_PROPERTIES:
                    continue
                inputs.setdefault(key, {}).setdefault(row["property_name"], []).append(
                    row.get("serialized_value", "")
                )

    for (package, _sequence_path, variable), definition in task_definitions.items():
        task_definitions_by_package_leaf.setdefault((package, variable), []).append(definition)

    out_rows: list[dict[str, str]] = []
    for key, action in sorted(actions.items()):
        if action.get("m_TargetIndex"):
            index_counts[action["m_TargetIndex"]] += 1
        link_values = inputs.get(key, {})
        task_refs: list[str] = []
        for serialized in link_values.get("VariableLinks", []):
            if not re.search(r'LinkDesc="Task"', serialized):
                continue
            match = re.search(r"LinkedVariables=\(([^)]*)\)", serialized)
            if match:
                task_refs.extend(
                    name.strip() for name in match.group(1).split(",")
                    if name.strip() and name.strip().lower() != "none"
                )
        same_sequence_candidates = [
            task_definitions[(action["package"], action["sequence_path"], variable)]
            for variable in task_refs
            if (action["package"], action["sequence_path"], variable) in task_definitions
        ]
        package_scope_candidates = [
            definition
            for variable in task_refs
            for definition in task_definitions_by_package_leaf.get((action["package"], variable), [])
        ]
        out_rows.append({
            "package": action["package"],
            "object_path": action["object_path"],
            "sequence_path": action["sequence_path"],
            "m_TargetName": action.get("m_TargetName", ""),
            "m_TargetIndex": action.get("m_TargetIndex", ""),
            "m_pTargetActor": action.get("m_pTargetActor", ""),
            "InputLinks": json.dumps(link_values.get("InputLinks", []), ensure_ascii=False),
            "OutputLinks": json.dumps(link_values.get("OutputLinks", []), ensure_ascii=False),
            "VariableLinks": json.dumps(link_values.get("VariableLinks", []), ensure_ascii=False),
            "task_variable_refs": json.dumps(task_refs, ensure_ascii=False),
            "same_sequence_task_definition_candidates": json.dumps(same_sequence_candidates, ensure_ascii=False),
            "package_scope_task_definition_candidates": json.dumps(package_scope_candidates, ensure_ascii=False),
            "inventory_csv": action["inventory_csv"],
        })

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "package", "object_path", "sequence_path", *PROPERTIES, *LINK_PROPERTIES,
        "task_variable_refs", "same_sequence_task_definition_candidates",
        "package_scope_task_definition_candidates", "inventory_csv",
    ]
    with args.csv_out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    presence = Counter(
        "+".join(name for name in PROPERTIES if row.get(name)) or "none"
        for row in out_rows
    )
    indexed_task_refs: list[tuple[str, str, str]] = []
    indexed_same_sequence_resolution_count = 0
    indexed_task_refs_unresolved_same_sequence = 0
    for key, action in actions.items():
        if not action.get("m_TargetIndex"):
            continue
        link_values = inputs.get(key, {})
        for serialized in link_values.get("VariableLinks", []):
            if not re.search(r'LinkDesc="Task"', serialized):
                continue
            match = re.search(r"LinkedVariables=\(([^)]*)\)", serialized)
            if not match:
                continue
            names = [name.strip() for name in match.group(1).split(",")
                     if name.strip() and name.strip().lower() != "none"]
            for variable in names:
                indexed_task_refs.append((action["package"], action["sequence_path"], variable))
                candidates = task_definitions.get((action["package"], action["sequence_path"], variable))
                indexed_same_sequence_resolution_count += int(candidates is not None)
                indexed_task_refs_unresolved_same_sequence += int(candidates is None)
    report = {
        "scope": "browser/editor CSV exports only; no UPK parsing or retail projection",
        "task_reference_limit": "VariableLinks export linked variable leaf names but not their object paths/indices; task-definition joins by exact package and sequence_path are scoped candidates, not serialized pointer identity.",
        "action_class": ACTION_CLASS,
        "unique_actions": len(actions),
        "property_rows": dict(sorted(property_counts.items())),
        "property_presence_sets": dict(sorted(presence.items())),
        "target_index_values": dict(sorted(index_counts.items())),
        "indexed_task_variable_link_occurrences": len(indexed_task_refs),
        "indexed_unique_task_variable_instances": len(set(indexed_task_refs)),
        "indexed_task_links_with_same_sequence_definition_candidate": indexed_same_sequence_resolution_count,
        "indexed_task_links_without_same_sequence_definition_candidate": indexed_task_refs_unresolved_same_sequence,
        "inventory_sources": source_inventory,
        "link_sources": source_links,
        "generated_csv_sha256": sha256(args.csv_out),
    }
    args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "unique_actions", "property_rows", "property_presence_sets", "target_index_values",
        "indexed_task_variable_link_occurrences", "indexed_unique_task_variable_instances",
        "indexed_task_links_with_same_sequence_definition_candidate",
        "indexed_task_links_without_same_sequence_definition_candidate", "generated_csv_sha256",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
