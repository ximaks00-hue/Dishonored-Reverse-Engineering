#!/usr/bin/env python3
"""Inventory and parse AKPK containers stored under localized CookedPC/DLC paths."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from wwise_pck_table_crosscheck import parse_pck, read_csv


EXTENSIONS = {".int", ".rus", ".deu", ".esn", ".fra", ".ita", ".jpn"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_target(relative_path: str) -> bool:
    rel = PurePosixPath(relative_path.replace("\\", "/"))
    lower = rel.as_posix().casefold()
    return (
        rel.suffix.casefold() in EXTENSIONS
        and (
            lower.startswith("dishonoredgame/cookedpcconsole/")
            or lower.startswith("dishonoredgame/dlc/pcconsole/")
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--build-record", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--packages-output", required=True, type=Path)
    parser.add_argument("--entries-output", required=True, type=Path)
    parser.add_argument("--variants-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()

    manifest = read_csv(args.manifest.resolve(strict=True))
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    build_id_match = re.search(r"Steam build ID:\s*`?(\d+)", build_text)
    exe_hash_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if not build_id_match or not exe_hash_match:
        raise SystemExit("build record lacks Steam build ID or executable SHA-256")
    root = args.game_root.resolve(strict=True)
    selected = sorted(
        (row for row in manifest if is_target(row["relative_path"])),
        key=lambda row: row["relative_path"].casefold(),
    )
    if not selected:
        raise SystemExit("no localized AKPK candidates found in manifest")

    package_rows: list[dict[str, object]] = []
    entry_rows: list[dict[str, object]] = []
    package_lookup: dict[tuple[str, str], list[dict[str, object]]] = collections.defaultdict(list)
    summary: dict[str, object] = {
        "build_id": build_id_match.group(1),
        "exe_sha256": exe_hash_match.group(1).upper(),
        "parser": "EXP-0120 Python AKPK table parser reused; no QuickBMS table cross-check was available for this extension cohort",
        "manifest_candidate_files": len(selected),
        "manifest_candidate_bytes": sum(int(row["bytes"]) for row in selected),
        "extensions": {},
        "empty_files": 0,
        "parsed_nonempty_files": 0,
        "parser_errors": 0,
        "manifest_size_mismatches": 0,
        "manifest_sha256_mismatches": 0,
        "container_magic_counts": {},
        "bank_entries": 0,
        "sound_entries": 0,
        "external_entries": 0,
        "packages_with_bank_entries": 0,
        "all_bank_payloads_start_with_BKHD": 0,
        "bank_versions": {},
        "internal_languages_by_extension": {},
        "embedded_bank_magic_counts": {},
        "embedded_sound_magic_counts": {},
        "tables_after_first_payload_files": 0,
        "payload_overlap_pairs": 0,
        "variant_group_count": 0,
        "variant_group_sizes": {},
        "same_hash_variant_groups": 0,
    }
    ext_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    version_counts: collections.Counter[str] = collections.Counter()
    language_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    bank_magics: collections.Counter[str] = collections.Counter()
    sound_magics: collections.Counter[str] = collections.Counter()
    container_magics: collections.Counter[str] = collections.Counter()
    parser_errors: list[dict[str, str]] = []
    range_issues: list[dict[str, str]] = []

    for row in selected:
        rel = PurePosixPath(row["relative_path"].replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts:
            raise SystemExit(f"manifest path escapes game root: {row['relative_path']}")
        path = root.joinpath(*rel.parts)
        data = path.read_bytes()
        digest = sha256(data)
        ext = rel.suffix.upper()
        ext_counts[ext]["files"] += 1
        ext_counts[ext]["bytes"] += len(data)
        size_match = len(data) == int(row["bytes"])
        hash_match = digest == row["sha256"].upper()
        if not size_match:
            summary["manifest_size_mismatches"] = int(summary["manifest_size_mismatches"]) + 1
        if not hash_match:
            summary["manifest_sha256_mismatches"] = int(summary["manifest_sha256_mismatches"]) + 1

        parsed: list[dict[str, object]] = []
        meta: dict[str, object] = {}
        status = "empty_file" if not data else "parsed"
        error_text = ""
        if not data:
            summary["empty_files"] = int(summary["empty_files"]) + 1
            ext_counts[ext]["empty_files"] += 1
        else:
            container_magics[data[:4].decode("ascii", errors="replace")] += 1
            try:
                parsed, meta = parse_pck(data, rel.as_posix())
                summary["parsed_nonempty_files"] = int(summary["parsed_nonempty_files"]) + 1
                ext_counts[ext]["parsed_nonempty_files"] += 1
            except Exception as exc:  # record per-file format failures; keep the cohort complete
                status = "parser_error"
                error_text = f"{type(exc).__name__}: {exc}"
                summary["parser_errors"] = int(summary["parser_errors"]) + 1
                ext_counts[ext]["parser_errors"] += 1
                parser_errors.append({"relative_path": rel.as_posix(), "error": error_text})

        bank_count = int(meta.get("bank_entries", 0))
        sound_count = int(meta.get("sound_entries", 0))
        external_count = int(meta.get("external_entries", 0))
        summary["bank_entries"] = int(summary["bank_entries"]) + bank_count
        summary["sound_entries"] = int(summary["sound_entries"]) + sound_count
        summary["external_entries"] = int(summary["external_entries"]) + external_count
        bank_versions = meta.get("bank_version", 0)
        if bank_count:
            version_counts[str(bank_versions)] += 1
            summary["packages_with_bank_entries"] = int(summary["packages_with_bank_entries"]) + 1
            if bank_count == sum(
                1
                for entry in parsed
                if entry["section"] == "bank"
                and data[int(str(entry["entry_offset_hex"]), 16) : int(str(entry["entry_offset_hex"]), 16) + 4] == b"BKHD"
            ):
                summary["all_bank_payloads_start_with_BKHD"] = int(summary["all_bank_payloads_start_with_BKHD"]) + 1
        if meta:
            language_key = ",".join(sorted(set(meta.get("languages", {}).values())))
            language_counts[ext][language_key] += 1

        ranges: list[tuple[int, int, str]] = []
        bank_magic_ok = True
        for entry in parsed:
            offset = int(str(entry["entry_offset_hex"]), 16)
            size = int(entry["entry_bytes"])
            kind = str(entry["section"])
            sig = data[offset : offset + 4].decode("ascii", errors="replace")
            if kind == "bank":
                bank_magics[sig] += 1
                bank_magic_ok = bank_magic_ok and sig == "BKHD"
            elif kind == "sound":
                sound_magics[sig] += 1
            ranges.append((offset, offset + size, kind))
            entry_rows.append(
                {
                    "source_path": rel.as_posix(),
                    "source_sha256": digest,
                    "extension": ext,
                    "section": kind,
                    "resource_id": entry["resource_id"],
                    "language_id": entry["language_id"],
                    "language_name": entry["language_name"],
                    "entry_offset_hex": entry["entry_offset_hex"],
                    "entry_bytes": size,
                    "embedded_name": entry["embedded_name"],
                    "entry_width_bytes": entry["entry_width_bytes"],
                    "payload_magic4": sig,
                }
            )

        ranges.sort()
        tables_end = int(meta.get("tables_end_offset", 0))
        first_payload = min((start for start, _, _ in ranges), default=0)
        tables_before_payload = bool(ranges) and tables_end <= first_payload
        if ranges and not tables_before_payload:
            summary["tables_after_first_payload_files"] = int(summary["tables_after_first_payload_files"]) + 1
            range_issues.append({"relative_path": rel.as_posix(), "issue": "tables_end_after_first_payload"})
        for left, right in zip(ranges, ranges[1:]):
            if left[1] > right[0]:
                summary["payload_overlap_pairs"] = int(summary["payload_overlap_pairs"]) + 1
                range_issues.append(
                    {
                        "relative_path": rel.as_posix(),
                        "issue": f"overlap_{left[2]}_{left[0]:#x}_{right[2]}_{right[0]:#x}",
                    }
                )

        package_rows.append(
            {
                "relative_path": rel.as_posix(),
                "extension": ext,
                "manifest_bytes": int(row["bytes"]),
                "actual_bytes": len(data),
                "manifest_sha256": row["sha256"].upper(),
                "actual_sha256": digest,
                "manifest_size_match": size_match,
                "manifest_sha256_match": hash_match,
                "magic4": data[:4].decode("ascii", errors="replace"),
                "parser_status": status,
                "parser_error": error_text,
                "flags": meta.get("flags", ""),
                "bank_version": bank_versions if bank_count else "",
                "internal_languages": json.dumps(meta.get("languages", {}), sort_keys=True),
                "bank_entries": bank_count,
                "sound_entries": sound_count,
                "external_entries": external_count,
                "tables_end_offset": tables_end if meta else "",
                "first_payload_offset": first_payload if ranges else "",
                "tables_before_first_payload": tables_before_payload if ranges else "",
                "all_bank_payloads_start_with_BKHD": bank_magic_ok if bank_count else "",
            }
        )

        group_key = (rel.parent.as_posix().casefold(), rel.stem.casefold())
        package_lookup[group_key].append(
            {
                "path": rel.as_posix(),
                "extension": ext,
                "sha256": digest,
                "status": status,
                "language_names": ",".join(sorted(set(meta.get("languages", {}).values()))) if meta else "",
                "bank_entries": bank_count,
                "sound_entries": sound_count,
            }
        )

    variant_rows: list[dict[str, object]] = []
    size_counts: collections.Counter[str] = collections.Counter()
    for (parent, stem), variants in sorted(package_lookup.items()):
        if len(variants) < 2:
            continue
        hashes: dict[str, list[str]] = collections.defaultdict(list)
        for variant in variants:
            hashes[str(variant["sha256"])].append(str(variant["extension"]))
        size_counts[str(len(variants))] += 1
        variant_rows.append(
            {
                "relative_parent": parent,
                "package_stem": stem,
                "variant_count": len(variants),
                "extensions": ";".join(sorted(str(v["extension"]) for v in variants)),
                "unique_sha256_count": len(hashes),
                "identical_content_extensions": ";".join(
                    ",".join(sorted(exts)) for _, exts in sorted(hashes.items())
                ),
                "parsed_variant_count": sum(v["status"] == "parsed" for v in variants),
                "bank_entry_counts": ";".join(f"{v['extension']}:{v['bank_entries']}" for v in sorted(variants, key=lambda v: str(v["extension"]))),
                "sound_entry_counts": ";".join(f"{v['extension']}:{v['sound_entries']}" for v in sorted(variants, key=lambda v: str(v["extension"]))),
                "internal_languages_by_extension": ";".join(
                    f"{v['extension']}:{v['language_names']}" for v in sorted(variants, key=lambda v: str(v["extension"]))
                ),
            }
        )
        if len(hashes) == 1:
            summary["same_hash_variant_groups"] = int(summary["same_hash_variant_groups"]) + 1

    summary["extensions"] = {
        ext: dict(counts) for ext, counts in sorted(ext_counts.items())
    }
    summary["bank_versions"] = dict(sorted(version_counts.items()))
    summary["internal_languages_by_extension"] = {
        ext: dict(sorted(counts.items())) for ext, counts in sorted(language_counts.items())
    }
    summary["container_magic_counts"] = dict(sorted(container_magics.items()))
    summary["embedded_bank_magic_counts"] = dict(sorted(bank_magics.items()))
    summary["embedded_sound_magic_counts"] = dict(sorted(sound_magics.items()))
    summary["variant_group_count"] = len(variant_rows)
    summary["variant_group_sizes"] = dict(sorted(size_counts.items(), key=lambda item: int(item[0])))
    summary["parser_error_rows"] = parser_errors
    summary["range_issue_rows"] = range_issues

    write_csv(args.packages_output, package_rows)
    write_csv(args.entries_output, entry_rows)
    write_csv(args.variants_output, variant_rows)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        "files={manifest_candidate_files} parsed={parsed_nonempty_files} empty={empty_files} "
        "entries={entries} parser_errors={parser_errors} size_mismatches={manifest_size_mismatches} "
        "sha256_mismatches={manifest_sha256_mismatches} variants={variant_group_count}".format(
            **summary,
            entries=int(summary["bank_entries"]) + int(summary["sound_entries"]),
        )
    )
    return int(
        bool(summary["parser_errors"])
        or bool(summary["manifest_size_mismatches"])
        or bool(summary["manifest_sha256_mismatches"])
        or bool(summary["tables_after_first_payload_files"])
        or bool(summary["payload_overlap_pairs"])
    )


if __name__ == "__main__":
    raise SystemExit(main())
