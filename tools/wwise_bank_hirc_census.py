#!/usr/bin/env python3
"""Extract and inspect Wwise BNKs embedded in the exact-build PCK catalog.

Output records are parser-derived static relations. They do not establish game
runtime loading, playback, or event invocation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PCK_CENSUS = ROOT / "research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv"
GAME_ROOT = ROOT / "Dishonored RHCP"
QUICKBMS_DEFAULT = ROOT / "third_party/quickbms-0.12.0/quickbms.exe"
BMS_DEFAULT = ROOT / ".tmp/wwise_pck_extractor.bms"
WWISER_DEFAULT = ROOT / ".tmp/wwiser-current/wwiser.py"
OUTPUT_DEFAULT = ROOT / "research/builds/BUILD-STEAM-10256413"
EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
QUICKBMS_SHA256 = "FF812D38E22AEA0CC2CDC13C5C91CA34FAE4443AB12987002105BE6BAB3F4948"
BMS_SHA256 = "4459C0A4C354A92DCAD335599C389E8296908BD8B38FB128BD4C505AEAEE6B5D"
WWISER_COMMIT = "08e937b649bc7007c234bbd59e34a41d5eef3b38"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def object_fields(node: ET.Element) -> dict[str, str]:
    """Return first value for each field name inside one parsed object."""
    found: dict[str, str] = {}
    for field in node.iter("field"):
        key, value = field.get("name"), field.get("value")
        if key and value is not None:
            found.setdefault(key, value)
    return found


def parse_bank(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    header = next((n for n in root.iter("object") if n.get("name") == "AkBankHeader"), None)
    header_fields = object_fields(header) if header is not None else {}
    bank_id = header_fields.get("dwSoundBankID", "")
    bank_version = header_fields.get("dwBankGeneratorVersion", "")

    hirc = next((n for n in root.iter("object") if n.get("name") == "HircChunk"), None)
    hirc_objects = []
    if hirc is not None:
        loaded = next((n for n in hirc if n.tag == "list" and n.get("name") == "listLoadedItem"), None)
        if loaded is not None:
            hirc_objects = [n for n in loaded if n.tag == "object"]
    type_counts = Counter(n.get("name", "") for n in hirc_objects)
    objects_by_id: dict[str, str] = {}
    object_rows: list[dict[str, str]] = []
    for obj in hirc_objects:
        fields = object_fields(obj)
        object_id = fields.get("ulID")
        if object_id:
            objects_by_id[object_id] = obj.get("name", "")
            object_rows.append({"object_id": object_id, "object_type": obj.get("name", "")})

    media_ids: list[str] = []
    for obj in root.iter("object"):
        if obj.get("name") == "MediaHeader":
            value = object_fields(obj).get("id")
            if value is not None:
                media_ids.append(value)

    edge_rows: list[dict[str, str]] = []
    for obj in hirc_objects:
        obj_type = obj.get("name", "")
        fields = object_fields(obj)
        object_id = fields.get("ulID", "")
        if obj_type == "CAkEvent" and object_id:
            for action in obj.iter("object"):
                if action.get("name") != "Action":
                    continue
                action_id = object_fields(action).get("ulActionID", "")
                if action_id:
                    edge_rows.append({
                        "edge_type": "event_action", "from_type": "CAkEvent", "from_id": object_id,
                        "to_type": "Action", "to_id": action_id, "media_id": "", "file_id": "",
                        "stream_type": "", "external_flag": "",
                    })
        if obj_type.startswith("CAkAction") and object_id:
            target_id = fields.get("ulTargetID", "")
            if target_id:
                edge_rows.append({
                    "edge_type": "action_target", "from_type": obj_type, "from_id": object_id,
                    "to_type": (
                        "zero_id_value" if target_id == "0"
                        else objects_by_id.get(target_id, "unknown_or_cross_bank")
                    ), "to_id": target_id,
                    "media_id": "", "file_id": fields.get("fileID", ""), "stream_type": "",
                    "external_flag": "",
                })
        if object_id:
            for child_field in obj.iter("field"):
                child_id = child_field.get("value", "")
                if child_field.get("name") != "ulChildID" or not child_id or child_id == "0":
                    continue
                edge_rows.append({
                    "edge_type": "container_child", "from_type": obj_type, "from_id": object_id,
                    "to_type": objects_by_id.get(child_id, "unknown_or_cross_bank"), "to_id": child_id,
                    "media_id": "", "file_id": "", "stream_type": "", "external_flag": "",
                })
        if obj_type == "CAkSound" and object_id:
            media = next((n for n in obj.iter("object") if n.get("name") == "AkMediaInformation"), None)
            source = object_fields(media) if media is not None else {}
            edge_rows.append({
                "edge_type": "sound_media", "from_type": "CAkSound", "from_id": object_id,
                "to_type": "media_source", "to_id": source.get("sourceID", ""),
                "media_id": source.get("sourceID", ""), "file_id": source.get("uFileID", ""),
                "stream_type": fields.get("StreamType", source.get("StreamType", "")),
                "external_flag": source.get("bExternallySupplied", ""),
            })
    return {
        "bank_id": bank_id,
        "bank_version": bank_version,
        "hirc_object_count": len(hirc_objects),
        "hirc_type_counts": json.dumps(dict(sorted(type_counts.items())), ensure_ascii=False, separators=(",", ":")),
        "event_count": type_counts.get("CAkEvent", 0),
        "action_count": sum(n for name, n in type_counts.items() if name.startswith("CAkAction")),
        "sound_count": type_counts.get("CAkSound", 0),
        "media_index_count": len(media_ids),
        "media_index_ids": json.dumps(media_ids, separators=(",", ":")),
        "_media_id_set": set(media_ids),
        "_objects": object_rows,
        "edges": edge_rows,
    }


def read_census(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    banks = [r for r in rows if r["embedded_name"].lower().endswith(".bnk")]
    wems = [r for r in rows if r["embedded_name"].lower().endswith(".wem")]
    return banks, wems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quickbms", type=Path, default=QUICKBMS_DEFAULT)
    parser.add_argument("--bms", type=Path, default=BMS_DEFAULT)
    parser.add_argument("--wwiser", type=Path, default=WWISER_DEFAULT)
    parser.add_argument("--game-root", type=Path, default=GAME_ROOT)
    parser.add_argument("--census", type=Path, default=PCK_CENSUS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--extract-dir", type=Path, default=ROOT / "assets/extracted/wwise-bank-hirc-20261027")
    parser.add_argument("--xml-dir", type=Path, default=ROOT / ".tmp/wwise-bank-hirc-xml-20261027")
    parser.add_argument("--init-bank", type=Path, default=GAME_ROOT / "DishonoredGame/CookedPCConsole/Init.bnk")
    parser.add_argument("--init-xml", type=Path, default=ROOT / ".tmp/wwiser-init-bank.xml")
    parser.add_argument("--limit", type=int, default=0, help="debug limit; zero means all banks")
    parser.add_argument("--reuse-xml", action="store_true", help="reuse XML dumps already present at their numbered paths")
    args = parser.parse_args()

    expected = args.game_root / "Binaries/Win32/Dishonored.exe"
    if not expected.is_file() or sha256(expected) != EXE_SHA256:
        raise SystemExit("game executable is absent or does not match build 10256413 hash")
    for tool in (args.quickbms, args.bms, args.wwiser, args.census):
        if not tool.is_file():
            raise SystemExit(f"required input is missing: {tool}")
    if sha256(args.quickbms) != QUICKBMS_SHA256 or sha256(args.bms) != BMS_SHA256:
        raise SystemExit("QuickBMS executable or Wwise BMS extractor hash does not match the recorded toolchain")
    try:
        wwiser_commit = subprocess.check_output(
            ["git", "-C", str(args.wwiser.resolve().parent), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit("could not verify the wwiser checkout commit")
    if wwiser_commit != WWISER_COMMIT:
        raise SystemExit(f"wwiser checkout commit mismatch: {wwiser_commit}")
    banks, wems = read_census(args.census)
    manifest_rows = list(csv.DictReader((ROOT / "research/builds/BUILD-STEAM-10256413/files.csv").open(encoding="utf-8-sig", newline="")))
    manifest_by_path = {row["relative_path"]: row for row in manifest_rows}
    per_pck_banks = Counter(r["source_pck"] for r in banks)
    if any(count != 1 for count in per_pck_banks.values()):
        raise SystemExit("expected exactly one embedded BNK per listed PCK")
    if len(banks) != 503:
        raise SystemExit(f"expected the recorded 503-bank denominator; found {len(banks)}")

    args.extract_dir.mkdir(parents=True, exist_ok=True)
    args.xml_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, str]] = []
    edge_rows: list[dict[str, str]] = []
    sound_rows: list[dict[str, str]] = []
    direct_path_rows: list[dict[str, str]] = []
    container_path_rows: list[dict[str, str]] = []
    object_rows: list[dict[str, str]] = []
    limit = args.limit or len(banks)

    for i, bank in enumerate(banks[:limit]):
        source_pck = bank["source_pck"]
        pck = args.game_root / Path(source_pck)
        manifest_record = manifest_by_path.get(source_pck)
        if manifest_record is None or not pck.is_file() or pck.stat().st_size != int(bank["pck_bytes"]) or pck.stat().st_size != int(manifest_record["bytes"]):
            summary_rows.append({"source_pck": source_pck, "embedded_name": bank["embedded_name"], "status": "pck_missing_or_size_mismatch", "error": f"expected={bank['pck_bytes']}"})
            continue
        pck_sha = sha256(pck)
        if pck_sha != manifest_record["sha256"].upper():
            summary_rows.append({"source_pck": source_pck, "embedded_name": bank["embedded_name"], "status": "pck_hash_mismatch", "error": f"actual={pck_sha};manifest={manifest_record['sha256']}"})
            continue
        work_dir = args.extract_dir / f"{i:04d}"
        work_dir.mkdir(parents=True, exist_ok=True)
        expected_rel = Path(bank["embedded_name"].replace("/", "\\"))
        bnk_path = work_dir / expected_rel
        if not bnk_path.is_file():
            result = subprocess.run(
                [str(args.quickbms), "-f", "{}.bnk", "-o", str(args.bms), str(pck), str(work_dir)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if result.returncode != 0 or not bnk_path.is_file():
                summary_rows.append({"source_pck": source_pck, "embedded_name": bank["embedded_name"], "status": "extract_error", "error": (result.stderr + result.stdout)[-1200:]})
                continue
        if bnk_path.stat().st_size != int(bank["entry_bytes"]):
            summary_rows.append({"source_pck": source_pck, "embedded_name": bank["embedded_name"], "status": "size_mismatch", "error": f"actual={bnk_path.stat().st_size};catalog={bank['entry_bytes']}"})
            continue
        xml_path = args.xml_dir / f"{i:04d}.xml"
        dump_name = xml_path.with_suffix("")
        if not (args.reuse_xml and xml_path.is_file()):
            xml_path.unlink(missing_ok=True)
            result = subprocess.run(
                [sys.executable, str(args.wwiser), "-d", "xml", "-dn", str(dump_name), str(bnk_path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if result.returncode != 0 or not xml_path.is_file():
                summary_rows.append({"source_pck": source_pck, "embedded_name": bank["embedded_name"], "status": "parse_error", "error": (result.stderr + result.stdout)[-1200:]})
                continue
        try:
            parsed = parse_bank(xml_path)
        except Exception as exc:  # preserve per-file failure and continue the census
            summary_rows.append({"source_pck": source_pck, "embedded_name": bank["embedded_name"], "status": "xml_error", "error": repr(exc)})
            continue
        bank_row = {
            "source_pck": source_pck,
            "embedded_name": bank["embedded_name"],
            "pck_bytes": bank["pck_bytes"],
            "pck_sha256": pck_sha,
            "entry_bytes": bank["entry_bytes"],
            "entry_offset_hex": bank["entry_offset_hex"],
            "extracted_sha256": sha256(bnk_path),
            "status": "parsed",
            "error": "",
            **{k: str(parsed[k]) for k in (
                "bank_id", "bank_version", "hirc_object_count", "hirc_type_counts",
                "event_count", "action_count", "sound_count", "media_index_count", "media_index_ids",
            )},
        }
        summary_rows.append(bank_row)
        object_rows.extend({"source_pck": source_pck, "bank_id": parsed["bank_id"], **obj} for obj in parsed["_objects"])
        for edge in parsed["edges"]:
            edge_rows.append({"source_pck": source_pck, "bank_id": parsed["bank_id"], "bank_version": parsed["bank_version"], **edge})
        # Sound/media IDs are matched only within the same source PCK; keep exact
        # and global candidate counts distinct to expose package-context limits.
        pck_wems = [r for r in wems if r["source_pck"] == source_pck]
        for edge in parsed["edges"]:
            if edge["edge_type"] != "sound_media":
                continue
            media_id = edge["media_id"]
            exact = [r["embedded_name"] for r in pck_wems if re.search(rf"/{re.escape(media_id)}\.wem$", r["embedded_name"], re.I)] if media_id else []
            global_matches = [r for r in wems if media_id and re.search(rf"/{re.escape(media_id)}\.wem$", r["embedded_name"], re.I)]
            same_bank = media_id in parsed["_media_id_set"]
            sound_rows.append({
                "source_pck": source_pck,
                "bank_id": parsed["bank_id"],
                "sound_id": edge["from_id"],
                "media_source_id": media_id,
                "file_id": edge["file_id"],
                "stream_type": edge["stream_type"],
                "external_flag": edge["external_flag"],
                "same_bank_media_index": str(same_bank).lower(),
                "same_pck_wem_matches": len(exact),
                "same_pck_wem_paths": " | ".join(exact),
                "global_wem_match_count": len(global_matches),
                "global_wem_sample_paths": " | ".join(sorted({r["embedded_name"] for r in global_matches})[:5]),
            })
        if (i + 1) % 25 == 0 or i + 1 == limit:
            print(f"processed {i + 1}/{limit} banks; parsed={sum(r.get('status') == 'parsed' for r in summary_rows)}", flush=True)

    # Init.bnk is a standalone installed bank, not one of the 503 PCK entries.
    init_rel = "DishonoredGame/CookedPCConsole/Init.bnk"
    init_record = manifest_by_path.get(init_rel)
    if init_record is None or not args.init_bank.is_file():
        raise SystemExit("Init.bnk is missing from the manifest or local install")
    if args.init_bank.stat().st_size != int(init_record["bytes"]) or sha256(args.init_bank) != init_record["sha256"].upper():
        raise SystemExit("Init.bnk does not match the saved manifest size/SHA-256")
    if not (args.reuse_xml and args.init_xml.is_file()):
        args.init_xml.parent.mkdir(parents=True, exist_ok=True)
        args.init_xml.unlink(missing_ok=True)
        result = subprocess.run(
            [sys.executable, str(args.wwiser), "-d", "xml", "-dn", str(args.init_xml.with_suffix("")), str(args.init_bank)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode != 0 or not args.init_xml.is_file():
            raise SystemExit(f"Init.bnk parse failed: {(result.stderr + result.stdout)[-1200:]}")
    init_parsed = parse_bank(args.init_xml)
    summary_rows.append({
        "source_pck": "standalone:" + init_rel,
        "embedded_name": "Init.bnk",
        "pck_bytes": "",
        "entry_bytes": str(args.init_bank.stat().st_size),
        "entry_offset_hex": "",
        "extracted_sha256": sha256(args.init_bank),
        "status": "parsed",
        "error": "",
        **{k: str(init_parsed[k]) for k in (
            "bank_id", "bank_version", "hirc_object_count", "hirc_type_counts",
            "event_count", "action_count", "sound_count", "media_index_count", "media_index_ids",
        )},
    })
    object_rows.extend({"source_pck": "standalone:" + init_rel, "bank_id": init_parsed["bank_id"], **obj} for obj in init_parsed["_objects"])

    # Add global ID context for static action targets without collapsing local
    # bank references or claiming runtime resolution.
    global_objects: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in object_rows:
        global_objects[row["object_id"]].append(row)
    target_candidate_rows: list[dict[str, str]] = []
    for edge in edge_rows:
        if edge["edge_type"] not in ("action_target", "container_child"):
            continue
        candidates = global_objects.get(edge["to_id"], [])
        target_banks = sorted({candidate["source_pck"] for candidate in candidates})
        edge["global_candidate_count"] = str(len(candidates))
        edge["global_candidate_types"] = " | ".join(sorted({candidate["object_type"] for candidate in candidates}))
        edge["global_candidate_bank_count"] = str(len(target_banks))
        edge["init_bank_candidate"] = str(any(candidate["source_pck"].startswith("standalone:") for candidate in candidates)).lower()
        if edge["edge_type"] == "action_target" and edge["to_type"] == "unknown_or_cross_bank":
            for candidate in candidates:
                target_candidate_rows.append({
                    "source_pck": edge["source_pck"],
                    "source_bank_id": edge["bank_id"],
                    "action_type": edge["from_type"],
                    "action_id": edge["from_id"],
                    "target_id": edge["to_id"],
                    "local_target_type": edge["to_type"],
                    "candidate_pck": candidate["source_pck"],
                    "candidate_bank_id": candidate["bank_id"],
                    "candidate_object_type": candidate["object_type"],
                    "global_id_occurrence_count": str(len(candidates)),
                    "global_candidate_bank_count": str(len(target_banks)),
                    "init_bank_candidate": str(any(c["source_pck"].startswith("standalone:") for c in candidates)).lower(),
                    "claim": "exact parser ID equality across bank records; cross-bank semantic link remains candidate",
                })
    global_media_index: dict[str, set[str]] = defaultdict(set)
    for bank_row in summary_rows:
        if bank_row.get("status") != "parsed":
            continue
        for media_id in json.loads(bank_row.get("media_index_ids", "[]") or "[]"):
            global_media_index[media_id].add(bank_row["source_pck"])
    for sound in sound_rows:
        candidate_banks = sorted(global_media_index.get(sound["media_source_id"], set()))
        sound["global_media_index_bank_count"] = str(len(candidate_banks))
        sound["global_media_index_sample_banks"] = " | ".join(candidate_banks[:5])

    def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    write_csv(args.output_dir / "wwise-bank-hirc-summary.csv", summary_rows, [
        "source_pck", "embedded_name", "pck_bytes", "entry_bytes", "entry_offset_hex", "extracted_sha256",
        "pck_sha256", "status", "error", "bank_id", "bank_version", "hirc_object_count", "hirc_type_counts",
        "event_count", "action_count", "sound_count", "media_index_count", "media_index_ids",
    ])
    edge_fields = [
        "source_pck", "bank_id", "bank_version", "edge_type", "from_type", "from_id", "to_type", "to_id",
        "media_id", "file_id", "stream_type", "external_flag", "global_candidate_count", "global_candidate_types",
        "global_candidate_bank_count", "init_bank_candidate",
    ]
    write_csv(args.output_dir / "wwise-hirc-edges.csv", [edge for edge in edge_rows if edge["edge_type"] != "container_child"], edge_fields)
    write_csv(args.output_dir / "wwise-hirc-edges-with-container-children.csv", edge_rows, edge_fields)
    write_csv(args.output_dir / "wwise-hirc-objects.csv", object_rows, ["source_pck", "bank_id", "object_id", "object_type"])
    write_csv(args.output_dir / "wwise-action-target-global-id-candidates.csv", target_candidate_rows, [
        "source_pck", "source_bank_id", "action_type", "action_id", "target_id", "local_target_type",
        "candidate_pck", "candidate_bank_id", "candidate_object_type", "global_id_occurrence_count",
        "global_candidate_bank_count", "init_bank_candidate", "claim",
    ])
    write_csv(args.output_dir / "wwise-sound-media-joins.csv", sound_rows, [
        "source_pck", "bank_id", "sound_id", "media_source_id", "file_id", "stream_type", "external_flag",
        "same_bank_media_index", "same_pck_wem_matches", "same_pck_wem_paths", "global_wem_match_count", "global_wem_sample_paths",
        "global_media_index_bank_count", "global_media_index_sample_banks",
    ])
    event_actions: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    action_targets: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    sound_media: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    container_children: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    object_types = {(row["source_pck"], row["bank_id"], row["object_id"]): row["object_type"] for row in object_rows}
    for edge in edge_rows:
        group = (edge["source_pck"], edge["bank_id"], edge["from_id"])
        if edge["edge_type"] == "event_action":
            event_actions[group].append(edge["to_id"])
        elif edge["edge_type"] == "action_target":
            action_targets[group].append(edge["to_id"])
        elif edge["edge_type"] == "container_child":
            container_children[group].append(edge["to_id"])
        elif edge["edge_type"] == "sound_media":
            sound_media[group].append(edge)
    sound_join_by_id = {(row["source_pck"], row["bank_id"], row["sound_id"]): row for row in sound_rows}
    for (source_pck, bank_id, event_id), action_ids in event_actions.items():
        for action_id in action_ids:
            for target_id in action_targets.get((source_pck, bank_id, action_id), []):
                direct_sound = object_types.get((source_pck, bank_id, target_id)) == "CAkSound"
                def visit(node_id: str, chain: list[str], ancestors: set[str]) -> None:
                    if node_id in ancestors:
                        return
                    ancestors = ancestors | {node_id}
                    node_type = object_types.get((source_pck, bank_id, node_id), "")
                    if node_type == "CAkSound":
                        for media in sound_media.get((source_pck, bank_id, node_id), []):
                            joined = sound_join_by_id.get((source_pck, bank_id, node_id), {})
                            row = {
                                "source_pck": source_pck,
                                "bank_id": bank_id,
                                "event_id": event_id,
                                "action_id": action_id,
                                "sound_id": node_id,
                                "media_source_id": media["media_id"],
                                "file_id": media["file_id"],
                                "stream_type": media["stream_type"],
                                "same_bank_media_index": joined.get("same_bank_media_index", ""),
                                "same_pck_wem_matches": joined.get("same_pck_wem_matches", ""),
                                "same_pck_wem_paths": joined.get("same_pck_wem_paths", ""),
                            }
                            if direct_sound:
                                direct_path_rows.append({
                                    **row,
                                    "claim": "parser-derived direct same-bank ID path; runtime invocation unproved",
                                })
                            container_path_rows.append({
                                **row,
                                "object_id_chain": " > ".join(chain),
                                "object_type_chain": " > ".join(object_types.get((source_pck, bank_id, item), "unknown") for item in chain),
                                "claim": "parser-derived same-bank object-ID chain via ulChildID fields; runtime invocation unproved",
                            })
                        return
                    for child_id in container_children.get((source_pck, bank_id, node_id), []):
                        visit(child_id, [*chain, child_id], ancestors)

                visit(target_id, [target_id], set())
    write_csv(args.output_dir / "wwise-event-direct-sound-paths.csv", direct_path_rows, [
        "source_pck", "bank_id", "event_id", "action_id", "sound_id", "media_source_id", "file_id",
        "stream_type", "same_bank_media_index", "same_pck_wem_matches", "same_pck_wem_paths", "claim",
    ])
    write_csv(args.output_dir / "wwise-event-hirc-sound-paths.csv", container_path_rows, [
        "source_pck", "bank_id", "event_id", "action_id", "sound_id", "media_source_id", "file_id",
        "stream_type", "same_bank_media_index", "same_pck_wem_matches", "same_pck_wem_paths",
        "object_id_chain", "object_type_chain", "claim",
    ])
    parsed_count = sum(r.get("status") == "parsed" for r in summary_rows)
    print(f"summary: {parsed_count}/{len(summary_rows)} parsed; base HIRC edges={sum(edge['edge_type'] != 'container_child' for edge in edge_rows)}; extended edges={len(edge_rows)}; target ID candidates={len(target_candidate_rows)}; sound/media rows={len(sound_rows)}; direct paths={len(direct_path_rows)}; container paths={len(container_path_rows)}")
    return 0 if parsed_count == len(summary_rows) and len(summary_rows) == limit + 1 else 2


if __name__ == "__main__":
    raise SystemExit(main())
