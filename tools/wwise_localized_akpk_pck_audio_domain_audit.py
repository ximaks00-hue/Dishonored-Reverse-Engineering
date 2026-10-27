#!/usr/bin/env python3
"""Audit localized AKPK HIRC media IDs against exact-build PCK audio catalogs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
GAME_ROOT = ROOT / "Dishonored RHCP"
EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
PCK_WEM_RE = re.compile(r"(?:^|/)(\d+)\.wem$", re.IGNORECASE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


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


def safe_source(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative.replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts:
        raise SystemExit(f"source path escapes game root: {relative}")
    return root.joinpath(*pure.parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=BUILD / "files.csv")
    parser.add_argument("--game-root", type=Path, default=GAME_ROOT)
    parser.add_argument("--pck-entries", type=Path, default=BUILD / "wwise-pck-entry-census.csv")
    parser.add_argument("--pck-banks", type=Path, default=BUILD / "wwise-bank-hirc-summary.csv")
    parser.add_argument("--pck-wem-decodes", type=Path, default=BUILD / "wwise-wem-decode-audit.csv")
    parser.add_argument("--pck-wem-summary", type=Path, default=BUILD / "wwise-wem-decode-summary.json")
    parser.add_argument("--akpk-banks", type=Path, default=BUILD / "wwise-localized-akpk-hirc-unique.csv")
    parser.add_argument("--akpk-hirc-wem-join", type=Path, default=BUILD / "wwise-localized-akpk-hirc-media-join.csv")
    parser.add_argument("--akpk-hirc-summary", type=Path, default=BUILD / "wwise-localized-akpk-hirc-summary.json")
    parser.add_argument("--akpk-join-summary", type=Path, default=BUILD / "wwise-localized-akpk-hirc-media-join-summary.json")
    parser.add_argument("--output-dir", type=Path, default=BUILD)
    parser.add_argument("--prefix", default="wwise-localized-akpk-pck-domain")
    args = parser.parse_args()

    manifest = read_csv(args.manifest.resolve(strict=True))
    manifest_by_path = {r["relative_path"].replace("\\", "/").casefold(): r for r in manifest}
    build_text = (BUILD / "build.md").read_text(encoding="utf-8")
    if EXE_SHA256 not in build_text:
        raise SystemExit("build record does not contain the expected exact-build EXE hash")
    exe = safe_source(args.game_root.resolve(strict=True), "Binaries/Win32/Dishonored.exe")
    if sha256_file(exe) != EXE_SHA256:
        raise SystemExit("current executable does not match the exact-build hash")
    exe_record = manifest_by_path.get("binaries/win32/dishonored.exe")
    if not exe_record or exe_record["sha256"].upper() != EXE_SHA256:
        raise SystemExit("executable is absent from or mismatched with the build manifest")

    pck_entries = read_csv(args.pck_entries.resolve(strict=True))
    pck_bank_rows = [r for r in pck_entries if r["embedded_name"].lower().endswith(".bnk")]
    pck_wem_rows = [r for r in pck_entries if r["embedded_name"].lower().endswith(".wem")]
    pck_bank_catalog = [r for r in read_csv(args.pck_banks.resolve(strict=True)) if r["source_pck"].lower().endswith(".pck")]
    pck_wem_decodes = read_csv(args.pck_wem_decodes.resolve(strict=True))
    pck_wem_summary = json.loads(args.pck_wem_summary.resolve(strict=True).read_text(encoding="utf-8"))
    akpk_banks = read_csv(args.akpk_banks.resolve(strict=True))
    akpk_join = read_csv(args.akpk_hirc_wem_join.resolve(strict=True))
    akpk_hirc_summary = json.loads(args.akpk_hirc_summary.resolve(strict=True).read_text(encoding="utf-8"))
    akpk_join_summary = json.loads(args.akpk_join_summary.resolve(strict=True).read_text(encoding="utf-8"))

    if len(pck_bank_rows) != 503 or len(pck_bank_catalog) != 503 or len(pck_wem_rows) != 1908:
        raise SystemExit("PCK catalog denominator mismatch")
    if pck_wem_summary.get("pck_sources_hash_checked") != 503 or pck_wem_summary.get("outcomes", {}).get("decoded") != 1908:
        raise SystemExit("PCK WEM summary does not show complete successful source/decode coverage")
    if akpk_hirc_summary.get("parse_failures") != 0 or akpk_join_summary.get("wem_occurrence_keys_joined_one_to_one") != 12112:
        raise SystemExit("localized AKPK HIRC/WEM inputs do not show complete successful coverage")
    if akpk_hirc_summary.get("exe_sha256") != EXE_SHA256 or akpk_join_summary.get("exe_sha256") != EXE_SHA256:
        raise SystemExit("localized AKPK catalogs have a different executable hash")

    # Hash every PCK source file and independently re-read the WEM/BNK ranges used
    # for the candidate comparison.
    pck_sources = sorted({r["source_pck"] for r in pck_entries})
    for source_rel in pck_sources:
        record = manifest_by_path.get(source_rel.replace("\\", "/").casefold())
        source = safe_source(args.game_root.resolve(strict=True), source_rel).resolve(strict=True)
        if not record or source.stat().st_size != int(record["bytes"]):
            raise SystemExit(f"PCK source size differs from manifest: {source_rel}")
        actual_sha = sha256_file(source)
        if actual_sha != record["sha256"].upper():
            raise SystemExit(f"PCK source hash differs from manifest: {source_rel}")
        for row in [x for x in pck_entries if x["source_pck"] == source_rel]:
            if int(row["pck_bytes"]) != source.stat().st_size:
                raise SystemExit(f"PCK catalog size mismatch: {source_rel}")

    bank_catalog_by_source = {r["source_pck"]: r for r in pck_bank_catalog}
    akpk_bank_hashes = {r["bank_payload_sha256"] for r in akpk_banks}
    pck_bank_crosswalk: list[dict[str, object]] = []
    pck_bank_sha_set: set[str] = set()
    for row in pck_bank_rows:
        source = safe_source(args.game_root.resolve(), row["source_pck"])
        offset, size = int(row["entry_offset_hex"], 16), int(row["entry_bytes"])
        with source.open("rb") as stream:
            stream.seek(offset)
            payload = stream.read(size)
        if len(payload) != size:
            raise SystemExit(f"short PCK BNK range read: {row['source_pck']}")
        digest = sha256_bytes(payload)
        prior = bank_catalog_by_source.get(row["source_pck"])
        if not prior or prior["status"] != "parsed" or prior["extracted_sha256"].upper() != digest:
            raise SystemExit(f"PCK BNK hash disagrees with EXP-0077 catalog: {row['source_pck']}")
        pck_bank_sha_set.add(digest)
        matches = [r["representative_source_path"] for r in akpk_banks if r["bank_payload_sha256"] == digest]
        pck_bank_crosswalk.append({
            "source_pck": row["source_pck"], "embedded_name": row["embedded_name"],
            "bank_id": row["embedded_name"].rsplit("/", 1)[-1].removesuffix(".bnk"),
            "pck_payload_sha256": digest, "pck_payload_bytes": size,
            "akpk_exact_payload_hash_match": bool(matches),
            "akpk_representative_path_candidates": json.dumps(matches, ensure_ascii=False, separators=(",", ":")),
        })

    decode_by_key = {
        (r["source_pck"], r["embedded_name"], r["entry_offset_hex"], r["entry_bytes"]): r
        for r in pck_wem_decodes
    }
    pck_wem_ids: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pck_wem_rows:
        key = (row["source_pck"], row["embedded_name"], row["entry_offset_hex"], row["entry_bytes"])
        decode = decode_by_key.get(key)
        if not decode or decode["status"] != "decoded":
            raise SystemExit(f"PCK WEM catalog entry lacks successful EXP-0119 decode: {key}")
        match = PCK_WEM_RE.search(row["embedded_name"].replace("\\", "/"))
        if not match:
            raise SystemExit(f"cannot derive numeric resource ID from PCK WEM path: {row['embedded_name']}")
        resource_id = match.group(1)
        source = safe_source(args.game_root.resolve(), row["source_pck"])
        with source.open("rb") as stream:
            stream.seek(int(row["entry_offset_hex"], 16))
            payload = stream.read(int(row["entry_bytes"]))
        if len(payload) != int(row["entry_bytes"]) or sha256_bytes(payload) != decode["payload_sha256"].upper():
            raise SystemExit(f"PCK WEM range hash disagrees with EXP-0119 decode catalog: {key}")
        pck_wem_ids[resource_id].append({**row, "payload_sha256": decode["payload_sha256"], "decode_status": decode["status"]})
    decode_keys = set(decode_by_key)
    catalog_wem_keys = {(r["source_pck"], r["embedded_name"], r["entry_offset_hex"], r["entry_bytes"]) for r in pck_wem_rows}
    if len(pck_wem_decodes) != 1908 or decode_keys != catalog_wem_keys:
        raise SystemExit("PCK WEM decode and entry catalogs do not reconcile one-to-one")

    unmatched = [r for r in akpk_join if r["join_status"] == "no_wem_resource_id_match"]
    unmatched_edges = {(r["bank_payload_sha256"], r["sound_id"], r["media_id"], r["file_id"]) for r in unmatched}
    if len(unmatched_edges) != 24205:
        raise SystemExit(f"expected 24,205 unique AKPK HIRC unmatched edge keys; found {len(unmatched_edges)}")
    edge_counts: Counter[str] = Counter()
    file_counts: Counter[str] = Counter()
    for bank_sha, sound_id, media_id, file_id in unmatched_edges:
        edge_counts[media_id] += 1
        file_counts[file_id] += 1
    media_id_rows = []
    for media_id, count in sorted(edge_counts.items(), key=lambda x: int(x[0])):
        candidates = pck_wem_ids.get(media_id, [])
        media_id_rows.append({
            "akpk_media_id": media_id, "unmatched_unique_hirc_edge_keys": count,
            "pck_wem_id_candidate_count": len(candidates),
            "pck_wem_candidate_sources": json.dumps(sorted({r["source_pck"] for r in candidates}), ensure_ascii=False, separators=(",", ":")),
            "pck_wem_candidate_payload_sha256": json.dumps(sorted({r["payload_sha256"] for r in candidates}), separators=(",", ":")),
        })
    media_id_matches = {media_id for media_id in edge_counts if media_id in pck_wem_ids}
    file_id_matches = {file_id for file_id in file_counts if file_id in pck_wem_ids}

    args.output_dir.resolve().mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir.resolve() / f"{args.prefix}-unmatched-media-ids.csv", media_id_rows)
    write_csv(args.output_dir.resolve() / f"{args.prefix}-pck-bank-hashes.csv", pck_bank_crosswalk)
    summary = {
        "build_id": "10256413", "exe_sha256": EXE_SHA256,
        "pck_entry_catalog_sha256": sha256_file(args.pck_entries.resolve(strict=True)),
        "pck_bank_catalog_sha256": sha256_file(args.pck_banks.resolve(strict=True)),
        "pck_wem_decode_catalog_sha256": sha256_file(args.pck_wem_decodes.resolve(strict=True)),
        "akpk_bank_catalog_sha256": sha256_file(args.akpk_banks.resolve(strict=True)),
        "akpk_hirc_wem_join_sha256": sha256_file(args.akpk_hirc_wem_join.resolve(strict=True)),
        "pck_source_paths_rehashed": len(pck_sources),
        "pck_bank_ranges_rehashed": len(pck_bank_rows),
        "pck_bank_unique_payload_hashes": len(pck_bank_sha_set),
        "pck_bank_payload_hashes_matching_akpk": len(pck_bank_sha_set & akpk_bank_hashes),
        "pck_wem_entry_rows_rehashed_and_decode_hash_checked": len(pck_wem_rows),
        "pck_wem_unique_numeric_ids": len(pck_wem_ids),
        "pck_wem_ids_with_multiple_occurrences": sum(len(rows) > 1 for rows in pck_wem_ids.values()),
        "akpk_hirc_unmatched_unique_edge_keys": len(unmatched_edges),
        "akpk_hirc_unmatched_distinct_media_ids": len(edge_counts),
        "unmatched_media_ids_with_pck_wem_id_candidates": len(media_id_matches),
        "unmatched_unique_edges_with_pck_wem_id_candidates": sum(edge_counts[i] for i in media_id_matches),
        "unmatched_file_ids_with_pck_wem_id_candidates": len(file_id_matches),
        "limitations": [
            "PCK filename-ID equality is a cross-container numeric candidate check and does not establish ownership or runtime resolution.",
            "Exact bank payload hashes establish byte identity only; no PCK bank payload hash matched a localized AKPK bank in this cohort.",
            "The scan covers only the saved 503-PCK WEM/BNK catalogs and the localized AKPK HIRC/WEM cohort; other media domains and runtime loading remain open.",
        ],
    }
    summary_path = args.output_dir.resolve() / f"{args.prefix}-summary.json"
    temp = summary_path.with_suffix(summary_path.suffix + ".part")
    temp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temp.replace(summary_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
