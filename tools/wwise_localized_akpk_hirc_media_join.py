#!/usr/bin/env python3
"""Join parsed AKPK HIRC media IDs to the localized AKPK WEM occurrence catalog.

Exact bank payload identity and equal media/resource IDs establish a static
same-container candidate only. IDs found in another bank are reported separately
and never promoted to a bank-local or runtime relationship.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from itertools import combinations
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".part")
    try:
        with temp.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", type=Path, default=BUILD / "wwise-localized-akpk-hirc-edges.csv")
    parser.add_argument("--bank-occurrences", type=Path, default=BUILD / "wwise-localized-akpk-hirc-occurrences.csv")
    parser.add_argument("--wems", type=Path, default=BUILD / "wwise-localized-wem-decode-occurrences.csv")
    parser.add_argument("--decode-results", type=Path, default=BUILD / "wwise-localized-wem-decode-unique.csv")
    parser.add_argument("--entries", type=Path, default=BUILD / "wwise-localized-akpk-entries.csv")
    parser.add_argument("--hirc-summary", type=Path, default=BUILD / "wwise-localized-akpk-hirc-summary.json")
    parser.add_argument("--wem-summary", type=Path, default=BUILD / "wwise-localized-wem-decode-summary.json")
    parser.add_argument("--output-dir", type=Path, default=BUILD)
    parser.add_argument("--prefix", default="wwise-localized-akpk-hirc-media-join")
    args = parser.parse_args()

    edges_path = args.edges.resolve(strict=True)
    banks_path = args.bank_occurrences.resolve(strict=True)
    wems_path = args.wems.resolve(strict=True)
    decodes_path = args.decode_results.resolve(strict=True)
    entries_path = args.entries.resolve(strict=True)
    hirc_summary_path = args.hirc_summary.resolve(strict=True)
    wem_summary_path = args.wem_summary.resolve(strict=True)
    hirc_summary = json.loads(hirc_summary_path.read_text(encoding="utf-8"))
    wem_summary = json.loads(wem_summary_path.read_text(encoding="utf-8"))

    # Ensure the catalogs being joined are the exact files reported by their runs.
    if hirc_summary.get("source_files_checked") != 4056 or hirc_summary.get("parse_failures") != 0:
        raise SystemExit("HIRC input summary does not show complete successful source coverage")
    if hirc_summary.get("unique_static_edge_rows") != len(read_csv(edges_path)):
        raise SystemExit("HIRC edge CSV row count disagrees with HIRC run summary")
    if hirc_summary.get("bank_entry_occurrences") != len(read_csv(banks_path)):
        raise SystemExit("bank occurrence CSV row count disagrees with HIRC run summary")
    if wem_summary.get("akpk_source_hashes_checked") != 4056 or wem_summary.get("outcomes", {}).get("decoded") != 7213:
        raise SystemExit("WEM input summary does not show complete successful source/decode coverage")
    if wem_summary.get("akpk_sound_entry_rows") != len(read_csv(wems_path)):
        raise SystemExit("WEM occurrence CSV row count disagrees with WEM run summary")
    if wem_summary.get("unique_payload_hash_size_pairs") != len(read_csv(decodes_path)):
        raise SystemExit("WEM unique decoder CSV row count disagrees with WEM run summary")
    if hirc_summary.get("exe_sha256") != wem_summary.get("exe_sha256"):
        raise SystemExit("HIRC and WEM catalogs identify different exact-build executables")
    if hirc_summary.get("entries_table_sha256") != sha256_file(entries_path):
        raise SystemExit("HIRC catalog does not match the current EXP-0130 AKPK entry table")
    akpk_entries = read_csv(entries_path)
    if len(akpk_entries) != wem_summary.get("akpk_entry_rows") or sum(r["section"] == "sound" for r in akpk_entries) != wem_summary.get("akpk_sound_entry_rows"):
        raise SystemExit("EXP-0130 AKPK entry table counts disagree with WEM decode summary")

    bank_occurrences = read_csv(banks_path)
    wem_occurrences = read_csv(wems_path)
    decode_rows = read_csv(decodes_path)
    edges = read_csv(edges_path)

    bank_occ_by_sha: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bank_occurrences:
        bank_occ_by_sha[row["bank_payload_sha256"]].append(row)
    wem_by_resource: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in wem_occurrences:
        wem_by_resource[row["resource_id"]].append(row)
    decode_by_key = {(r["payload_sha256"], r["payload_bytes"]): r for r in decode_rows}

    relations: list[dict[str, object]] = []
    summary_keys: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    candidate_counts: dict[str, int] = defaultdict(int)
    file_id_without_media_candidate: set[tuple[str, str, str, str]] = set()
    for edge in edges:
        if edge["edge_type"] != "sound_media" or not edge["media_id"]:
            continue
        bank_sha = edge["bank_payload_sha256"]
        bank_sources = bank_occ_by_sha.get(bank_sha, [])
        if not bank_sources:
            raise SystemExit(f"edge bank payload absent from occurrence map: {bank_sha}")
        media_id = edge["media_id"]
        # Bank resource IDs identify banks; WEM resource IDs identify sounds. Join
        # by the parser-reported media ID and the exact containing source path.
        global_rows = wem_by_resource.get(media_id, [])
        edge_key = (bank_sha, edge["from_id"], media_id)
        for occurrence in bank_sources:
            local_rows = [r for r in global_rows if r["source_path"] == occurrence["source_path"]]
            if edge["file_id"] and edge["file_id"] != media_id and wem_by_resource.get(edge["file_id"]):
                file_id_without_media_candidate.add((bank_sha, edge["from_id"], media_id, edge["file_id"]))
            if local_rows:
                state = "same_source_resource_id_candidate"
                candidate_class = "same_source_container_id_candidate"
                selected = local_rows
            elif global_rows:
                state = "id_only_other_container_candidate"
                candidate_class = "cross_container_id_candidate"
                selected = global_rows
            else:
                state = "no_wem_resource_id_match"
                candidate_class = "unmatched"
                selected = []
            summary_keys[state].add(edge_key)
            candidate_counts[state] += len(selected)
            if not selected:
                relations.append({
                    "bank_payload_sha256": bank_sha,
                    "bank_source_path": occurrence["source_path"],
                    "bank_resource_id": occurrence["resource_id"],
                    "bank_extension": occurrence["extension"],
                    "sound_id": edge["from_id"],
                    "media_id": media_id,
                    "file_id": edge["file_id"],
                    "stream_type": edge["stream_type"],
                    "external_flag": edge["external_flag"],
                    "join_status": state,
                    "candidate_class": candidate_class,
                    "candidate_source_path": "",
                    "candidate_resource_id": "",
                    "candidate_extension": "",
                    "candidate_entry_offset_hex": "",
                    "payload_sha256": "",
                    "payload_bytes": "",
                    "decode_status": "",
                })
                continue
            for candidate in selected:
                decode = decode_by_key.get((candidate["payload_sha256"], candidate["entry_bytes"]))
                relations.append({
                    "bank_payload_sha256": bank_sha,
                    "bank_source_path": occurrence["source_path"],
                    "bank_resource_id": occurrence["resource_id"],
                    "bank_extension": occurrence["extension"],
                    "sound_id": edge["from_id"],
                    "media_id": media_id,
                    "file_id": edge["file_id"],
                    "stream_type": edge["stream_type"],
                    "external_flag": edge["external_flag"],
                    "join_status": state,
                    "candidate_class": candidate_class,
                    "candidate_source_path": candidate["source_path"],
                    "candidate_resource_id": candidate["resource_id"],
                    "candidate_extension": candidate["extension"],
                    "candidate_entry_offset_hex": candidate["entry_offset_hex"],
                    "payload_sha256": candidate["payload_sha256"],
                    "payload_bytes": candidate["entry_bytes"],
                    "decode_status": decode["status"] if decode else "missing_decode_record",
                })
    if not relations:
        raise SystemExit("no CAkSound-to-media rows found")
    expected_wem_keys = {(r["source_path"], r["resource_id"]) for r in wem_occurrences}
    candidate_wem_keys = {(r["candidate_source_path"], r["candidate_resource_id"])
                          for r in relations if r["candidate_source_path"]}
    if candidate_wem_keys != expected_wem_keys:
        raise SystemExit(
            f"same-container joins cover {len(candidate_wem_keys)}/{len(expected_wem_keys)} "
            "WEM occurrence keys; refusing incomplete or extra mapping"
        )
    if sum(bool(r["candidate_source_path"]) for r in relations) != len(expected_wem_keys):
        raise SystemExit("WEM occurrence mapping has duplicate candidate rows")
    if any(summary_keys[a] & summary_keys[b] for a, b in combinations(summary_keys, 2)):
        raise SystemExit("unique HIRC edge status groups overlap")
    if any(r["candidate_source_path"] and r["decode_status"] != "decoded" for r in relations):
        raise SystemExit("a joined WEM occurrence lacks a successful decode result")
    write_csv(args.output_dir.resolve() / f"{args.prefix}.csv", relations)

    summary = {
        "build_id": hirc_summary["build_id"],
        "exe_sha256": hirc_summary["exe_sha256"],
        "akpk_entries_table_sha256": hirc_summary["entries_table_sha256"],
        "akpk_entries_table_sha256_verified": sha256_file(entries_path),
        "hirc_edges_sha256": sha256_file(edges_path),
        "hirc_bank_occurrences_sha256": sha256_file(banks_path),
        "wem_occurrences_sha256": sha256_file(wems_path),
        "wem_decode_results_sha256": sha256_file(decodes_path),
        "hirc_sound_media_edge_rows": sum(1 for r in edges if r["edge_type"] == "sound_media" and r["media_id"]),
        "distinct_hirc_bank_payloads_with_edges": len({r["bank_payload_sha256"] for r in edges if r["edge_type"] == "sound_media" and r["media_id"]}),
        "unique_bank_sound_media_edges_by_status": {status: len(keys) for status, keys in sorted(summary_keys.items())},
        "candidate_output_rows_by_status": dict(sorted(candidate_counts.items())),
        "wem_occurrence_keys": len(expected_wem_keys),
        "wem_occurrence_keys_joined_one_to_one": len(candidate_wem_keys),
        "distinct_wem_resource_ids": len({r["resource_id"] for r in wem_occurrences}),
        "distinct_wem_payloads_joined": len({r["payload_sha256"] for r in relations if r["payload_sha256"]}),
        "unmatched_media_edges_with_file_id_matching_any_wem_id": len(file_id_without_media_candidate),
        "output_rows": len(relations),
        "interpretation_limit": "Equal resource/media IDs in an exact source container are static parser/catalog candidates only. Cross-container ID matches are separately labeled; no result establishes original Wwise semantics, runtime bank selection, event execution, or playback.",
    }
    summary_path = args.output_dir.resolve() / f"{args.prefix}-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    temp = summary_path.with_suffix(summary_path.suffix + ".part")
    temp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temp.replace(summary_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
