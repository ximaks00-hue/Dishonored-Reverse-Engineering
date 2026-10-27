#!/usr/bin/env python3
"""Validate raw PE name/target pairs at class-table pointer symbols from EXP-0137."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
GAME_ROOT = ROOT / "Dishonored RHCP"
EXPECTED_BUILD_ID = "10256413"
EXPECTED_EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
INPUT = ROOT / "research/executable/evidence/EXP-0137-native-class-registration-group-uelib-join.csv"
FUNCTION_INDEX = ROOT / "research/executable/functions.csv"
OUTPUT_DIR = ROOT / "research/executable/evidence"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    build_text = (BUILD / "build.md").read_text(encoding="utf-8")
    if "Steam build ID: `10256413`" not in build_text or EXPECTED_EXE_SHA256 not in build_text:
        raise SystemExit("build record identity does not match expected build")

    executable = (GAME_ROOT / "Binaries/Win32/Dishonored.exe").resolve(strict=True)
    manifest = read_csv(BUILD / "files.csv")
    exe_row = next((row for row in manifest if row["relative_path"].replace("\\", "/").casefold()
                    == "binaries/win32/dishonored.exe"), None)
    actual_exe_sha = sha256_file(executable)
    if actual_exe_sha != EXPECTED_EXE_SHA256 or not exe_row or exe_row["sha256"].upper() != EXPECTED_EXE_SHA256:
        raise SystemExit("local executable, build record, and manifest SHA-256 do not agree")

    sources = read_csv(INPUT)
    if len(sources) != 332 or any(row["build_id"] != EXPECTED_BUILD_ID
                                  or row["exe_sha256"].upper() != EXPECTED_EXE_SHA256
                                  for row in sources):
        raise SystemExit("EXP-0137 input denominator or build identity differs")
    if len({(row["registration_address"], row["class_key"]) for row in sources}) != len(sources):
        raise SystemExit("EXP-0137 input contains duplicate function/key rows")

    pe = pefile.PE(str(executable), fast_load=True)
    if pe.OPTIONAL_HEADER.Magic != 0x10B:
        raise SystemExit("expected a 32-bit PE image")
    image = executable.read_bytes()

    def section_offset(va: int, size: int) -> tuple[str, int | None]:
        rva = va - pe.OPTIONAL_HEADER.ImageBase
        for section in pe.sections:
            start = section.VirtualAddress
            if start <= rva and rva + size <= start + section.SizeOfRawData:
                name = section.Name.rstrip(b"\0").decode("ascii", errors="replace")
                return name, section.PointerToRawData + rva - start
        return "", None

    def read_u32(va: int) -> tuple[str, int | None]:
        section, offset = section_offset(va, 4)
        if offset is None:
            return section, None
        return section, int.from_bytes(image[offset:offset + 4], "little")

    def read_ascii_z(va: int) -> tuple[str, str]:
        section, offset = section_offset(va, 1)
        if offset is None:
            return section, ""
        limit = min(offset + 512, len(image))
        end = image.find(b"\0", offset, limit)
        if end < 0:
            return section, ""
        try:
            return section, image[offset:end].decode("ascii")
        except UnicodeDecodeError:
            return section, ""

    index_rows = read_csv(FUNCTION_INDEX)
    exact_functions = {int(row["address"], 16): row for row in index_rows}
    function_ranges = [
        (int(row["body_start"], 16), int(row["body_end"], 16), row)
        for row in index_rows if row.get("body_start") and row.get("body_end")
    ]

    output_rows: list[dict[str, object]] = []
    for source in sources:
        symbol_va = int(source["table_pointer_symbol_address"], 16)
        name_section, name_va = read_u32(symbol_va)
        target_va = read_u32(symbol_va + 4)[1]
        if name_va is None or target_va is None:
            raise SystemExit(f"table pair outside raw PE sections: {source['table_pointer_symbol']}")
        string_section, native_name = read_ascii_z(name_va)
        target_section, _ = section_offset(target_va, 1)
        if name_section != ".data" or string_section != ".rdata" or target_section != ".text" or not native_name:
            raise SystemExit(
                f"unexpected raw pair sections/content at {source['table_pointer_symbol']}: "
                f"{name_section}, {string_section}, {target_section}, {native_name!r}"
            )
        class_key = source["class_key"]
        owner_prefix_match = any(native_name.startswith(prefix + class_key)
                                 for prefix in ("", "A", "U"))
        target_function = exact_functions.get(target_va)
        containing = [row for start, end, row in function_ranges if start <= target_va <= end]
        if not owner_prefix_match:
            raise SystemExit(f"native exec string does not start with class key: {class_key} / {native_name}")
        output_rows.append({
            "build_id": EXPECTED_BUILD_ID,
            "exe_sha256": EXPECTED_EXE_SHA256,
            "registration_address": source["registration_address"],
            "class_key": class_key,
            "table_pointer_symbol": source["table_pointer_symbol"],
            "table_pointer_symbol_address": f"0x{symbol_va:08X}",
            "name_pointer_slot_section": name_section,
            "raw_name_pointer": f"0x{name_va:08X}",
            "name_string_section": string_section,
            "decoded_native_exec_name": native_name,
            "native_name_starts_with_class_key": owner_prefix_match,
            "handler_pointer_slot_va": f"0x{symbol_va + 4:08X}",
            "raw_handler_target_va": f"0x{target_va:08X}",
            "handler_target_section": target_section,
            "exact_function_index_start": bool(target_function),
            "indexed_function_name": target_function["name"] if target_function else "",
            "containing_indexed_function_start": containing[0]["address"] if len(containing) == 1 else "",
            "containing_indexed_function_count": len(containing),
            "claim": "raw .data name pointer and adjacent .text address observed; runtime dispatch unproved",
        })

    counts = Counter()
    by_registration: dict[str, Counter[str]] = defaultdict(Counter)
    for row in output_rows:
        status = "exact_function_index_start" if row["exact_function_index_start"] else "unindexed_text_target"
        counts[status] += 1
        by_registration[str(row["registration_address"])][status] += 1
    unmatched = [row for row in output_rows if not row["exact_function_index_start"]]

    output = OUTPUT_DIR / "EXP-0138-native-class-table-raw-pointer-validation.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "build_id": EXPECTED_BUILD_ID,
        "exe_sha256": EXPECTED_EXE_SHA256,
        "exp_0137_source_sha256": sha256_file(INPUT),
        "function_index_sha256": sha256_file(FUNCTION_INDEX),
        "input_rows": len(sources),
        "raw_name_pointer_slots_in_data": sum(row["name_pointer_slot_section"] == ".data" for row in output_rows),
        "decoded_name_strings_in_rdata": sum(row["name_string_section"] == ".rdata" for row in output_rows),
        "adjacent_handler_targets_in_text": sum(row["handler_target_section"] == ".text" for row in output_rows),
        "names_start_with_class_key": sum(bool(row["native_name_starts_with_class_key"]) for row in output_rows),
        "exact_function_index_start_targets": counts["exact_function_index_start"],
        "text_targets_without_exact_function_index_start": counts["unindexed_text_target"],
        "unindexed_targets_inside_indexed_function_ranges": sum(
            int(row["containing_indexed_function_count"]) > 0 for row in unmatched
        ),
        "unindexed_targets": [
            {
                "registration_address": row["registration_address"],
                "class_key": row["class_key"],
                "native_exec_name": row["decoded_native_exec_name"],
                "target_va": row["raw_handler_target_va"],
            }
            for row in unmatched
        ],
        "counts_by_registration": {address: dict(value) for address, value in sorted(by_registration.items())},
        "limitations": [
            "This checks only the one raw name/target pair at each EXP-0137 pointer-symbol address; it does not infer table extent or enumerate sibling entries.",
            "A target in .text is not thereby proved to execute or to be a complete function; exact starts and ranges are limited to the current function index.",
            "The static pointer/name relation does not establish runtime table consumption, NativeToken conversion, or dispatch.",
        ],
    }
    summary_path = OUTPUT_DIR / "EXP-0138-native-class-table-raw-pointer-validation-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "input_rows", "raw_name_pointer_slots_in_data", "decoded_name_strings_in_rdata",
        "adjacent_handler_targets_in_text", "names_start_with_class_key",
        "exact_function_index_start_targets", "text_targets_without_exact_function_index_start",
        "unindexed_targets_inside_indexed_function_ranges", "unindexed_targets",
    )}, indent=2))


if __name__ == "__main__":
    main()
