#!/usr/bin/env python3
"""Recover conservative static boundaries for unindexed Core token targets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_GRP_JUMP, CS_MODE_32, CS_OP_IMM, Cs


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
EXE = ROOT / "Dishonored RHCP/Binaries/Win32/Dishonored.exe"
FUNCTIONS = ROOT / "research/executable/functions.csv"
CATALOG = ROOT / "research/executable/evidence/native-token-dispatch-catalog.csv"
MANIFEST = BUILD / "files.csv"
OUTPUT = ROOT / "research/executable/evidence"
EXPECTED_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
PROLOGUE = bytes.fromhex("53 8B DC 83 EC 08 83 E4 F0 83 C4 04 55 8B 6B 04")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, default=EXE)
    parser.add_argument("--function-index", type=Path, default=FUNCTIONS)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()

    build_text = (BUILD / "build.md").read_text(encoding="utf-8")
    if "Steam build ID: `10256413`" not in build_text or EXPECTED_SHA256 not in build_text:
        raise SystemExit("build record does not match expected build identity")
    exe_path = args.executable.resolve(strict=True)
    actual_sha = sha256_file(exe_path)
    if actual_sha != EXPECTED_SHA256:
        raise SystemExit(f"executable SHA-256 mismatch: {actual_sha}")
    manifest_rows = read_csv(MANIFEST.resolve(strict=True))
    exe_row = next((row for row in manifest_rows
                    if row["relative_path"].replace("\\", "/").casefold()
                    == "binaries/win32/dishonored.exe"), None)
    if not exe_row or exe_row["sha256"].upper() != actual_sha:
        raise SystemExit("executable hash does not match the build file manifest")

    function_rows = read_csv(args.function_index.resolve(strict=True))
    starts = sorted(int(row["address"], 16) for row in function_rows)
    indexed_ranges = [
        (int(row["body_start"], 16), int(row["body_end"], 16))
        for row in function_rows
    ]
    catalog_rows = [
        row for row in read_csv(args.catalog.resolve(strict=True))
        if row["package"] == "Core.upk"
    ]
    by_target: dict[int, list[dict[str, str]]] = {}
    for row in catalog_rows:
        if row["target_exact_function_index"].lower() != "true":
            by_target.setdefault(int(row["adjacent_target_va"], 16), []).append(row)
    targets = sorted(by_target)
    distinct_target_tokens = {rows[0]["native_token"] for rows in by_target.values()}
    if len(catalog_rows) != 166 or len(targets) != 17 or len(distinct_target_tokens) != 17:
        raise SystemExit(
            f"Core catalog denominator changed: {len(catalog_rows)} rows, "
            f"{len(targets)} unindexed target addresses, "
            f"{len(distinct_target_tokens)} target tokens"
        )
    for va, rows in by_target.items():
        if any(start == va for start in starts) or any(lo <= va <= hi for lo, hi in indexed_ranges):
            raise SystemExit(f"target 0x{va:08X} is no longer outside the indexed function bodies")
        if len({row["native_token"] for row in rows}) != 1 or len({row["object_name"] for row in rows}) != 1:
            raise SystemExit(f"target 0x{va:08X} has ambiguous Core catalog labels")

    pe = pefile.PE(str(exe_path), fast_load=True)
    if pe.OPTIONAL_HEADER.Magic != 0x10B or pe.FILE_HEADER.Machine != 0x14C:
        raise SystemExit("expected x86 PE32 executable")
    image_base = int(pe.OPTIONAL_HEADER.ImageBase)
    image = exe_path.read_bytes()

    def raw_offset(va: int, size: int) -> tuple[str, int]:
        rva = va - image_base
        for section in pe.sections:
            start = int(section.VirtualAddress)
            end = start + int(section.SizeOfRawData)
            if start <= rva and rva + size <= end:
                name = section.Name.rstrip(b"\0").decode("ascii", errors="replace")
                return name, int(section.PointerToRawData) + rva - start
        raise ValueError(f"0x{va:08X}+0x{size:X} is not file-backed")

    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    disassembler.detail = True
    summary_rows: list[dict[str, object]] = []
    instruction_rows: list[dict[str, object]] = []

    for target in targets:
        next_indexed = next((start for start in starts if start > target), None)
        if next_indexed is None:
            raise SystemExit(f"no following indexed function after 0x{target:08X}")
        section, file_offset = raw_offset(target, len(PROLOGUE))
        if section != ".text" or image[file_offset:file_offset + len(PROLOGUE)] != PROLOGUE:
            raise SystemExit(f"entry prologue/section mismatch at 0x{target:08X}")
        region_section, region_offset = raw_offset(target, next_indexed - target)
        if region_section != ".text":
            raise SystemExit(f"candidate range crosses section at 0x{target:08X}")
        region = image[region_offset:region_offset + next_indexed - target]

        # A subsequent full compiler prologue can mark another unindexed entry
        # inside the gap before the next function-index row. Accept it as a
        # boundary only when the preceding candidate ends in RET imm16 and
        # any bytes between that return and prologue are INT3 padding.
        prologue_offsets: list[int] = []
        position = 1
        while (found := region.find(PROLOGUE, position)) >= 0:
            prologue_offsets.append(found)
            position = found + 1
        accepted_boundary: tuple[int, list, list[bytes]] | None = None
        for offset in prologue_offsets + [len(region)]:
            candidate = region[:offset]
            instructions = list(disassembler.disasm(candidate, target))
            if not instructions or instructions[0].address != target:
                continue
            if any(left.address + left.size != right.address for left, right in zip(instructions, instructions[1:])):
                continue
            returns = [ins for ins in instructions if ins.mnemonic == "ret"]
            if not returns or any(ins.op_str != "8" for ins in returns):
                continue
            code_end = max(ins.address + ins.size for ins in returns)
            padding = candidate[code_end - target:]
            if any(byte != 0xCC for byte in padding):
                continue
            entry = target + offset
            ins_by_address = {ins.address: ins for ins in instructions if ins.address < code_end}
            valid_flow = True
            for ins in ins_by_address.values():
                if CS_GRP_JUMP in ins.groups and ins.operands and ins.operands[0].type == CS_OP_IMM:
                    destination = ins.operands[0].imm & 0xFFFFFFFF
                    if not target <= destination < code_end or destination not in ins_by_address:
                        valid_flow = False
                        break
            if valid_flow:
                accepted_boundary = (entry, instructions, [ins.bytes for ins in returns])
                break
        if accepted_boundary is None:
            raise SystemExit(f"could not establish conservative boundary for 0x{target:08X}")

        entry, instructions, returns_bytes = accepted_boundary
        code_end = max(ins.address + ins.size for ins in instructions if ins.mnemonic == "ret")
        padding = image[region_offset + code_end - target:region_offset + entry - target]
        labels = by_target[target]
        first = labels[0]
        for ins in instructions:
            if ins.address >= code_end:
                break
            instruction_rows.append({
                "target_va": f"0x{target:08X}",
                "native_token": first["native_token"],
                "native_name": first["object_name"],
                "instruction_va": f"0x{ins.address:08X}",
                "bytes": ins.bytes.hex(" ").upper(),
                "mnemonic": ins.mnemonic,
                "operands": ins.op_str,
            })
        summary_rows.append({
            "build_id": "10256413",
            "exe_sha256": EXPECTED_SHA256,
            "native_token": first["native_token"],
            "native_name": first["object_name"],
            "catalog_rows_for_target": len(labels),
            "target_va": f"0x{target:08X}",
            "target_section": section,
            "indexed_function_start": False,
            "indexed_body_containing_target": False,
            "entry_prologue_hex": PROLOGUE.hex(" ").upper(),
            "body_end_exclusive_va": f"0x{code_end:08X}",
            "return_count": len(returns_bytes),
            "return_mnemonics": ";".join("ret 8" for _ in returns_bytes),
            "padding_size": len(padding),
            "padding_all_int3": all(byte == 0xCC for byte in padding),
            "next_prologue_va": f"0x{entry:08X}",
            "next_indexed_function_va": f"0x{next_indexed:08X}",
            "body_boundary_basis": "Core catalog target; full repeated x86 prologue; contiguous decode; ret 8 exit(s); local branch targets; INT3-only padding to next prologue",
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = args.output_dir / "EXP-0162-core-native-unindexed-target-boundaries.csv"
    disassembly_csv = args.output_dir / "EXP-0162-core-native-unindexed-target-disassembly.csv"
    manifest_json = args.output_dir / "EXP-0162-core-native-unindexed-target-boundaries.json"
    write_csv(summary_csv, summary_rows)
    write_csv(disassembly_csv, instruction_rows)
    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "build_id": "10256413",
        "exe_sha256": EXPECTED_SHA256,
        "inputs": {
            "function_index_sha256": sha256_file(args.function_index.resolve(strict=True)),
            "native_token_catalog_sha256": sha256_file(args.catalog.resolve(strict=True)),
            "build_file_manifest_sha256": sha256_file(MANIFEST),
            "build_record_sha256": sha256_file(BUILD / "build.md"),
            "executable_sha256": actual_sha,
        },
        "tool": {
            "path": "tools/recover_core_native_token_unindexed_targets.py",
            "sha256": sha256_file(Path(__file__)),
            "python": __import__("platform").python_version(),
            "pefile": pefile.__version__,
            "capstone": __import__("capstone").__version__,
            "command": "python tools/recover_core_native_token_unindexed_targets.py",
        },
        "counts": {
            "core_catalog_rows": len(catalog_rows),
            "core_unindexed_target_addresses": len(targets),
            "distinct_unindexed_target_tokens": len(distinct_target_tokens),
            "recovered_boundary_candidates": len(summary_rows),
            "all_have_ret8_and_local_control_flow": len(summary_rows),
            "all_have_int3_only_padding": sum(bool(row["padding_all_int3"]) for row in summary_rows),
            "decoded_instruction_rows": len(instruction_rows),
        },
        "outputs": {
            "boundaries_csv": {"path": summary_csv.name, "sha256": sha256_file(summary_csv), "rows": len(summary_rows)},
            "disassembly_csv": {"path": disassembly_csv.name, "sha256": sha256_file(disassembly_csv), "rows": len(instruction_rows)},
        },
        "limitations": [
            "Recovered entries remain outside the checked-in 72,437-row function index and are not Ghidra function definitions.",
            "Boundary recovery is static and does not establish runtime dispatch, concrete owner classes, or complete operator semantics.",
            "The compiler prologue is used only as a candidate boundary together with return, padding, and control-flow evidence.",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
