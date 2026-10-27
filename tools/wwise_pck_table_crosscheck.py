#!/usr/bin/env python3
"""Parse AKPK tables in Python and compare all rows to the QuickBMS catalog."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import struct
from pathlib import Path, PurePosixPath


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def c_string(data: bytes, start: int, end: int) -> str:
    if start < 0 or start >= end or end > len(data):
        raise ValueError(f"string pointer out of bounds: {start:#x}..{end:#x}")
    if data[start] == 0 or (start + 1 < end and data[start + 1] == 0):
        cursor = start
        while cursor + 1 < end and data[cursor:cursor + 2] != b"\0\0":
            cursor += 2
        if cursor + 1 >= end:
            raise ValueError(f"unterminated UTF-16 language name at {start:#x}")
        return data[start:cursor].decode("utf-16le")
    terminator = data.find(b"\0", start, end)
    if terminator < 0:
        raise ValueError(f"unterminated UTF-8 language name at {start:#x}")
    return data[start:terminator].decode("utf-8")


def parse_language_section(data: bytes, start: int, size: int) -> dict[int, str]:
    if size == 0:
        return {0: "sfx"}
    end = start + size
    if start < 0 or end > len(data) or size < 4:
        raise ValueError("language section is out of bounds")
    count = struct.unpack_from("<I", data, start)[0]
    if 4 + count * 8 > size:
        raise ValueError("language directory exceeds section size")
    languages: dict[int, str] = {}
    cursor = start + 4
    for _ in range(count):
        relative_offset, language_id = struct.unpack_from("<II", data, cursor)
        if language_id in languages:
            raise ValueError(f"duplicate language ID {language_id}")
        languages[language_id] = c_string(data, start + relative_offset, end)
        cursor += 8
    languages.setdefault(0, "sfx")
    return languages


def parse_entry_section(
    data: bytes,
    start: int,
    section_size: int,
    kind: str,
    external: bool = False,
) -> tuple[list[dict[str, int | str | bool]], int, int]:
    if section_size == 0:
        return [], start, 0
    end = start + section_size
    if start < 0 or end > len(data) or section_size < 4:
        raise ValueError(f"{kind} section is out of bounds")
    count = struct.unpack_from("<I", data, start)[0]
    if count == 0:
        return [], end, 0
    if (section_size - 4) % count:
        raise ValueError(f"{kind} size/count are not evenly divisible")
    entry_size = (section_size - 4) // count
    if entry_size not in (20, 24):
        raise ValueError(f"unsupported {kind} entry width {entry_size}")
    entries: list[dict[str, int | str | bool]] = []
    cursor = start + 4
    for _ in range(count):
        if entry_size == 20:
            resource_id, block_size, size, offset, language_id = struct.unpack_from("<5I", data, cursor)
        elif external:
            low, high, block_size, size, offset, language_id = struct.unpack_from("<6I", data, cursor)
            resource_id = (high << 32) | low
        else:
            resource_id, block_size = struct.unpack_from("<II", data, cursor)
            size = struct.unpack_from("<Q", data, cursor + 8)[0]
            offset, language_id = struct.unpack_from("<II", data, cursor + 16)
        if block_size:
            offset *= block_size
        entries.append({
            "section": kind,
            "resource_id": resource_id,
            "block_size": block_size,
            "size": size,
            "offset": offset,
            "language_id": language_id,
            "external_id": external,
        })
        cursor += entry_size
    return entries, end, entry_size


def parse_pck(data: bytes, relative_path: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    if len(data) < 24 or data[:4] != b"AKPK":
        raise ValueError("missing AKPK magic or fixed header")
    header_size, flags, lang_size, bank_size, sound_size = struct.unpack_from("<5I", data, 4)
    cursor = 24
    external_size = 0
    if lang_size + bank_size + sound_size + 0x10 < header_size:
        if cursor + 4 > len(data):
            raise ValueError("missing external section length")
        external_size = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4

    languages = parse_language_section(data, cursor, lang_size)
    cursor += lang_size
    banks, cursor, bank_entry_size = parse_entry_section(data, cursor, bank_size, "bank")
    sounds, cursor, sound_entry_size = parse_entry_section(data, cursor, sound_size, "sound")
    externals, cursor, external_entry_size = parse_entry_section(
        data, cursor, external_size, "external", external=True,
    )
    entries = banks + sounds + externals

    bank_version = 0
    if banks:
        first_bank = banks[0]
        offset = int(first_bank["offset"])
        if offset + 12 > len(data) or data[offset:offset + 4] != b"BKHD":
            raise ValueError("first bank range does not begin with BKHD")
        bank_version = struct.unpack_from("<I", data, offset + 8)[0]
        if bank_version > 0x1000:
            bank_version = 62

    stem = PurePosixPath(relative_path).stem
    parsed_rows: list[dict[str, object]] = []
    for entry in entries:
        language_id = int(entry["language_id"])
        if language_id not in languages:
            raise ValueError(f"unknown language ID {language_id} in {relative_path}")
        language_name = languages[language_id]
        if language_id == 0:
            prefix = ""
        else:
            prefix = language_name + "/"
        resource_id = int(entry["resource_id"])
        offset = int(entry["offset"])
        size = int(entry["size"])
        kind = str(entry["section"])
        external_id = bool(entry["external_id"])
        extension = "bnk" if kind == "bank" else "wem"
        if kind == "sound" and bank_version < 62:
            if offset + 0x16 > len(data):
                raise ValueError(f"old-format sound header out of bounds in {relative_path}")
            codec = struct.unpack_from("<H", data, offset + 0x14)[0]
            extension = "xma" if codec in (0x0401, 0x0166) else ("ogg" if codec == 0xFFFF else "wav")
        if external_id:
            low = resource_id & 0xFFFFFFFF
            high = resource_id >> 32
            name = f"{stem}/externals/{prefix}{high:08x}{low:08x}.{extension}"
        else:
            name = f"{stem}/{prefix}{resource_id}.{extension}"
        if offset < 0 or size <= 0 or offset + size > len(data):
            raise ValueError(f"payload range out of bounds: {name} ({offset:#x}+{size:#x})")
        parsed_rows.append({
            "source_pck": relative_path,
            "section": kind,
            "resource_id": resource_id,
            "language_id": language_id,
            "language_name": language_name,
            "entry_offset_hex": f"0x{offset:08X}",
            "entry_bytes": size,
            "embedded_name": name,
            "entry_width_bytes": bank_entry_size if kind == "bank" else (external_entry_size if kind == "external" else sound_entry_size),
        })
    meta = {
        "header_size": header_size,
        "flags": flags,
        "language_section_bytes": lang_size,
        "bank_section_bytes": bank_size,
        "sound_section_bytes": sound_size,
        "external_section_bytes": external_size,
        "languages": languages,
        "bank_version": bank_version,
        "bank_entries": len(banks),
        "sound_entries": len(sounds),
        "external_entries": len(externals),
        "entry_widths": {"bank": bank_entry_size, "sound": sound_entry_size, "external": external_entry_size},
        "tables_end_offset": cursor,
    }
    return parsed_rows, meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--pck-catalog", required=True, type=Path)
    parser.add_argument("--build-record", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--entries-output", required=True, type=Path)
    parser.add_argument("--packages-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()

    root = args.game_root.resolve(strict=True)
    manifest = read_csv(args.manifest.resolve(strict=True))
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    exe_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    expected_exe_sha = exe_match.group(1).upper() if exe_match else ""
    if "10256413" not in build_text or not expected_exe_sha:
        raise SystemExit("Build record does not identify build 10256413 and EXE SHA-256")
    exe_rel = "Binaries/Win32/Dishonored.exe"
    exe_row = next((row for row in manifest if row["relative_path"].casefold() == exe_rel.casefold()), None)
    exe_path = root.joinpath(*PurePosixPath(exe_rel).parts)
    if exe_row is None or not exe_path.is_file():
        raise SystemExit("Build EXE missing from current tree or manifest")
    if sha256_file(exe_path) != expected_exe_sha or exe_row["sha256"].upper() != expected_exe_sha:
        raise SystemExit("Current EXE identity does not match build record and manifest")

    manifest_pcks = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in manifest
        if PurePosixPath(row["relative_path"].replace("\\", "/")).suffix.casefold() == ".pck"
    }
    catalog = read_csv(args.pck_catalog.resolve(strict=True))
    if len(manifest_pcks) != 503 or len(catalog) != 2411:
        raise SystemExit(f"Unexpected PCK/catalog denominators: {len(manifest_pcks)} PCKs, {len(catalog)} rows")
    catalog_sources = {row["source_pck"].replace("\\", "/").casefold() for row in catalog}
    if catalog_sources != set(manifest_pcks):
        raise SystemExit("PCK catalog paths do not reconcile with manifest PCK paths")

    expected = collections.Counter(
        (
            row["source_pck"].replace("\\", "/").casefold(),
            int(row["entry_offset_hex"], 16),
            int(row["entry_bytes"]),
            row["embedded_name"].replace("\\", "/"),
        )
        for row in catalog
    )
    actual_rows: list[dict[str, object]] = []
    package_rows: list[dict[str, object]] = []
    parser_errors: list[dict[str, str]] = []
    header_shapes: collections.Counter[str] = collections.Counter()
    entry_width_counts: collections.Counter[str] = collections.Counter()
    for relative_key, manifest_row in sorted(manifest_pcks.items()):
        relative = manifest_row["relative_path"].replace("\\", "/")
        package_path = root.joinpath(*PurePosixPath(relative).parts)
        if not package_path.is_file() or package_path.stat().st_size != int(manifest_row["bytes"]):
            raise SystemExit(f"PCK missing or size mismatch: {relative}")
        data = package_path.read_bytes()
        source_sha = sha256_bytes(data)
        if source_sha != manifest_row["sha256"].upper():
            raise SystemExit(f"PCK SHA-256 mismatch: {relative}")
        try:
            parsed, meta = parse_pck(data, relative)
            shape = tuple(meta[key] for key in (
                "header_size", "flags", "language_section_bytes", "bank_section_bytes",
                "sound_section_bytes", "external_section_bytes",
            ))
            header_shapes[str(shape)] += 1
            for section, width in meta["entry_widths"].items():
                if width:
                    entry_width_counts[f"{section}:{width}"] += meta[f"{section}_entries"]
            matched = 0
            for row in parsed:
                key = (
                    relative_key,
                    int(str(row["entry_offset_hex"]), 16),
                    int(row["entry_bytes"]),
                    str(row["embedded_name"]).replace("\\", "/"),
                )
                is_match = expected[key] > 0
                if is_match:
                    expected[key] -= 1
                    matched += 1
                else:
                    parser_errors.append({"source_pck": relative, "error": f"not in QuickBMS catalog: {key[1:]!r}"})
                actual_rows.append({**row, "source_pck_sha256": source_sha, "quickbms_catalog_exact_match": is_match})
            sorted_ranges = sorted(
                (int(row["entry_offset_hex"], 16), int(row["entry_offset_hex"], 16) + int(row["entry_bytes"]))
                for row in parsed
            )
            overlap_count = 0
            max_range_end = -1
            for range_start, range_end in sorted_ranges:
                if range_start < max_range_end:
                    overlap_count += 1
                max_range_end = max(max_range_end, range_end)
            first_payload_offset = min((start for start, _ in sorted_ranges), default=None)
            table_payload_separated = first_payload_offset is None or int(meta["tables_end_offset"]) <= first_payload_offset
            if overlap_count or not table_payload_separated:
                parser_errors.append({
                    "source_pck": relative,
                    "error": f"payload layout invariant failed: overlaps={overlap_count}, tables_end={meta['tables_end_offset']}, first_payload={first_payload_offset}",
                })
            package_rows.append({
                "source_pck": relative,
                "source_pck_sha256": source_sha,
                "status": "parsed",
                "header_size": meta["header_size"],
                "flags": meta["flags"],
                "language_section_bytes": meta["language_section_bytes"],
                "bank_section_bytes": meta["bank_section_bytes"],
                "sound_section_bytes": meta["sound_section_bytes"],
                "external_section_bytes": meta["external_section_bytes"],
                "bank_version": meta["bank_version"],
                "bank_entries": meta["bank_entries"],
                "sound_entries": meta["sound_entries"],
                "external_entries": meta["external_entries"],
                "tables_end_offset": meta["tables_end_offset"],
                "first_payload_offset": first_payload_offset if first_payload_offset is not None else "",
                "payload_begins_after_tables": table_payload_separated,
                "range_overlap_count": overlap_count,
                "parsed_entries": len(parsed),
                "exact_catalog_matches": matched,
                "error": "",
            })
        except (ValueError, UnicodeError, struct.error) as exc:
            parser_errors.append({"source_pck": relative, "error": str(exc)})
            package_rows.append({
                "source_pck": relative,
                "source_pck_sha256": source_sha,
                "status": "parse_error",
                "parsed_entries": 0,
                "exact_catalog_matches": 0,
                "error": str(exc),
            })

    unmatched_expected = [
        {"source_pck": key[0], "entry_offset": key[1], "entry_bytes": key[2], "embedded_name": key[3], "remaining_count": count}
        for key, count in expected.items() if count > 0
    ]
    args.entries_output.parent.mkdir(parents=True, exist_ok=True)
    entry_fields = [
        "source_pck", "source_pck_sha256", "section", "resource_id", "language_id",
        "language_name", "entry_offset_hex", "entry_bytes", "entry_width_bytes",
        "embedded_name", "quickbms_catalog_exact_match",
    ]
    with args.entries_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=entry_fields)
        writer.writeheader()
        writer.writerows(actual_rows)
    package_fields = list(dict.fromkeys(key for row in package_rows for key in row))
    with args.packages_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=package_fields)
        writer.writeheader()
        writer.writerows(package_rows)

    summary = {
        "build_id": "10256413",
        "exe_sha256": expected_exe_sha,
        "parser": "standalone Python AKPK section/table parser; QuickBMS output is used only as the comparison catalog",
        "manifest_pcks_hash_checked": len(manifest_pcks),
        "quickbms_catalog_rows": len(catalog),
        "python_parser_rows": len(actual_rows),
        "exact_row_matches": sum(1 for row in actual_rows if row["quickbms_catalog_exact_match"]),
        "unmatched_quickbms_rows": sum(row["remaining_count"] for row in unmatched_expected),
        "parser_errors": parser_errors,
        "unmatched_quickbms_examples": unmatched_expected[:20],
        "header_shape_count": len(header_shapes),
        "header_shapes": dict(header_shapes),
        "entry_width_counts": dict(entry_width_counts),
        "payload_ranges_before_table_end": sum(
            1 for row in package_rows if row.get("payload_begins_after_tables") is False
        ),
        "packages_with_entry_range_overlaps": sum(
            1 for row in package_rows if int(row.get("range_overlap_count", 0) or 0) > 0
        ),
        "bank_version_counts": dict(collections.Counter(
            str(row.get("bank_version", "error")) for row in package_rows
        )),
        "entries_csv": str(args.entries_output.resolve()),
        "packages_csv": str(args.packages_output.resolve()),
        "limitations": [
            "This parser reimplements the observed AKPK section/table layout; its field interpretation was informed by the pinned EXP-0065 QuickBMS script.",
            "Agreement with the QuickBMS-derived catalog is a second-implementation cross-check, not proof against an independent vendor specification.",
            "Matching offsets, sizes, and names does not establish event semantics or runtime loading.",
        ],
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if parser_errors or unmatched_expected or len(actual_rows) != len(catalog):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
