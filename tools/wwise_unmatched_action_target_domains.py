#!/usr/bin/env python3
"""Search non-ulID XML fields for exact IDs in the 92 unresolved Wwise action targets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
sys.path.insert(0, str(ROOT / "tools"))
import wwise_bank_hirc_census as census_tool  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", type=Path, default=ROOT / "research/builds/BUILD-STEAM-10256413/wwise-hirc-edges.csv")
    ap.add_argument("--pck-census", type=Path, default=ROOT / "research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv")
    ap.add_argument("--xml-dir", type=Path, default=ROOT / ".tmp/wwise-bank-hirc-xml-20261027")
    ap.add_argument("--init-xml", type=Path, default=ROOT / ".tmp/wwiser-init-bank.xml")
    ap.add_argument("--manifest", type=Path, default=ROOT / "research/builds/BUILD-STEAM-10256413/files.csv")
    ap.add_argument("--outdir", type=Path, default=ROOT / "research/builds/BUILD-STEAM-10256413")
    args = ap.parse_args()

    manifest = {r["relative_path"]: r for r in read_csv(args.manifest)}
    exe = manifest.get("Binaries/Win32/Dishonored.exe", {})
    assert exe.get("sha256", "").upper() == EXPECTED_SHA
    banks, _ = census_tool.read_census(args.pck_census)
    assert len(banks) == 503, len(banks)
    pck_paths = {r["source_pck"] for r in banks}
    bank_summaries = {r["source_pck"]: r for r in read_csv(ROOT / "research/builds/BUILD-STEAM-10256413/wwise-bank-hirc-summary.csv")
                      if r["status"] == "parsed" and r["source_pck"] in pck_paths}
    assert len(bank_summaries) == 503

    edge_rows = read_csv(args.edges)
    unresolved = [r for r in edge_rows if r["edge_type"] == "action_target"
                  and r["to_type"] == "unknown_or_cross_bank"
                  and r["to_id"] != "0" and r["global_candidate_count"] == "0"]
    targets = {r["to_id"] for r in unresolved}
    assert len(unresolved) == 92 and len(targets) == 27, (len(unresolved), len(targets))

    sources = [(args.xml_dir / f"{i:04d}.xml", row["source_pck"], bank_summaries[row["source_pck"]]["bank_id"])
               for i, row in enumerate(banks)]
    assert all(path.is_file() for path, _, _ in sources), "missing one or more PCK XML dumps"
    assert args.init_xml.is_file()
    sources.append((args.init_xml, "standalone:Init.bnk", ""))

    hits: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for xml_path, source_pck, expected_bank_id in sources:
        root = ET.parse(xml_path).getroot()
        if expected_bank_id:
            parsed = census_tool.parse_bank(xml_path)
            assert parsed["bank_id"] == expected_bank_id, (source_pck, expected_bank_id, parsed["bank_id"])
        parent = {child: node for node in root.iter() for child in node}
        for field in root.iter("field"):
            value = field.get("value", "")
            field_name = field.get("name", "")
            if value not in targets or field_name == "ulTargetID":
                continue
            ancestor = parent.get(field)
            owner = ""
            while ancestor is not None:
                if ancestor.tag == "object":
                    owner = ancestor.get("name", "")
                    break
                ancestor = parent.get(ancestor)
            hits[value].add((field_name, owner, source_pck))

    field_counts = Counter((field, owner) for fields in hits.values() for field, owner, _ in fields)
    target_rows = []
    occurrence_rows = []
    for target_id in sorted(targets, key=int):
        source_edges = [r for r in unresolved if r["to_id"] == target_id]
        occurrences = sorted(hits.get(target_id, set()))
        action_types = sorted({r["from_type"] for r in source_edges})
        target_rows.append({
            "target_id": target_id,
            "unresolved_action_edge_count": len(source_edges),
            "source_action_types": "; ".join(action_types),
            "distinct_field_owner_package_match_count": len(occurrences),
            "matched_field_names": "; ".join(sorted({f for f, _, _ in occurrences})),
            "matched_owner_types": "; ".join(sorted({o for _, o, _ in occurrences})),
            "matched_packages": "; ".join(sorted({p for _, _, p in occurrences})),
            "claim": "exact numeric equality in parsed XML field values; semantic/runtime relation unconfirmed",
        })
        for field, owner, source_pck in occurrences:
            occurrence_rows.append({"target_id": target_id, "field_name": field, "nearest_object_type": owner,
                                    "source_pck": source_pck,
                                    "claim": "exact numeric equality only; not proof of a reference"})

    edge_out = []
    edge_same_package = []
    for edge in unresolved:
        matches = sorted(hits.get(edge["to_id"], set()))
        same_package = [m for m in matches if m[2] == edge["source_pck"]]
        other_package = [m for m in matches if m[2] != edge["source_pck"]]
        if same_package:
            edge_same_package.append(edge)
        edge_out.append({
            "source_pck": edge["source_pck"], "bank_id": edge["bank_id"],
            "action_type": edge["from_type"], "action_id": edge["from_id"], "target_id": edge["to_id"],
            "same_pck_field_matches": "; ".join(f"{f}:{o}" for f, o, _ in same_package),
            "other_pck_field_matches": "; ".join(f"{f}:{o}@{p}" for f, o, p in other_package),
            "same_pck_other_field_match": "yes" if same_package else "no",
            "claim": "same numeric value in other parsed XML field(s), where present; relation remains a candidate",
        })

    args.outdir.mkdir(parents=True, exist_ok=True)
    def write(name: str, rows: list[dict[str, str]]) -> None:
        path = args.outdir / name
        fields = list(rows[0]) if rows else []
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    write("wwise-action-target-other-field-id-matches.csv", occurrence_rows)
    write("wwise-action-target-unmatched-domain-summary.csv", target_rows)
    write("wwise-action-target-unmatched-domain-edges.csv", edge_out)

    hit_ids = {tid for tid in targets if hits.get(tid)}
    matched_edges = [r for r in unresolved if r["to_id"] in hit_ids]
    unmatched_edges = [r for r in unresolved if r["to_id"] not in hit_ids]
    domain_ids = {
        "RTPCID|RTPC": {tid for tid in targets if any((f, owner) == ("RTPCID", "RTPC") for f, owner, _ in hits.get(tid, set()))},
        "RTPC_ID|RTPCRamping": {tid for tid in targets if any((f, owner) == ("RTPC_ID", "RTPCRamping") for f, owner, _ in hits.get(tid, set()))},
        "ulNodeID|AkSwitchNodeParams": {tid for tid in targets if any((f, owner) == ("ulNodeID", "AkSwitchNodeParams") for f, owner, _ in hits.get(tid, set()))},
    }
    edge_type_counts = lambda selected: dict(sorted(Counter(r["from_type"] for r in selected).items()))
    assert len(hit_ids) == 10 and len(targets - hit_ids) == 17
    assert len(matched_edges) == 57 and len(unmatched_edges) == 35
    cross_package_only = [r for r in matched_edges if r not in edge_same_package]
    assert len(edge_same_package) == 35 and len(cross_package_only) == 22
    assert edge_type_counts(edge_same_package) == {"CAkActionSetGameParameter": 17, "CAkActionStop": 18}
    assert edge_type_counts(cross_package_only) == {"CAkActionMute": 18, "CAkActionSetGameParameter": 4}
    assert edge_type_counts(matched_edges) == {"CAkActionMute": 18, "CAkActionSetGameParameter": 21, "CAkActionStop": 18}
    assert edge_type_counts(unmatched_edges) == {"CAkActionPause": 1, "CAkActionResume": 1,
                                                 "CAkActionSetAkProp": 10, "CAkActionStop": 23}
    assert {"RTPCID|RTPC": 6, "RTPC_ID|RTPCRamping": 6,
            "ulNodeID|AkSwitchNodeParams": 4} == {key: len(value) for key, value in domain_ids.items()}
    summary = {
        "build_id": "10256413", "exe_sha256": EXPECTED_SHA,
        "parsed_pck_banks": len(banks), "parsed_xml_sources_including_init": len(sources),
        "unresolved_nonzero_action_edges": len(unresolved), "distinct_target_ids": len(targets),
        "target_ids_matching_at_least_one_non_ulTargetID_field": len(hit_ids),
        "target_ids_with_no_other_field_match": len(targets - hit_ids),
        "unresolved_edges_with_other_field_matches": len(matched_edges),
        "unresolved_edges_with_no_other_field_match": len(unresolved) - len(matched_edges),
        "edges_with_same_pck_other_field_match": len(edge_same_package),
        "edges_with_only_other_pck_field_match": len(cross_package_only),
        "same_pck_match_edges_by_action_type": edge_type_counts(edge_same_package),
        "only_other_pck_match_edges_by_action_type": edge_type_counts(cross_package_only),
        "distinct_field_owner_package_match_tuples": {f"{field}|{owner}": count for (field, owner), count in sorted(field_counts.items())},
        "target_id_count_and_action_edges_by_field_domain": {
            domain: {"target_ids": len(ids), "action_edges": sum(1 for r in unresolved if r["to_id"] in ids)}
            for domain, ids in domain_ids.items()},
        "matched_action_edges_by_type": edge_type_counts(matched_edges),
        "no_other_field_match_action_edges_by_type": edge_type_counts(unmatched_edges),
        "claim_limit": "Exact numeric matches in parser XML only; no target-domain semantics, references, or runtime resolution established",
    }
    (args.outdir / "wwise-action-target-unmatched-domain-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
