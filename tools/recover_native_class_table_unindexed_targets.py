#!/usr/bin/env python3
"""Audit exact-build code boundaries for the three EXP-0138 unindexed targets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
GAME_ROOT = ROOT / "Dishonored RHCP"
EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
RAW_ROWS = ROOT / "research/executable/evidence/EXP-0138-native-class-table-raw-pointer-validation.csv"
JOIN_ROWS = ROOT / "research/executable/evidence/EXP-0139-native-class-table-uelib-zero-token-join.csv"
FUNCTION_INDEX = ROOT / "research/executable/functions.csv"
EXPECTED = {
    0x005D0B60: "URB_HandleexecGetOrientation",
    0x005D3120: "URB_ConstraintInstanceexecMoveKinActorTransform",
    0x005C64F0: "UUISceneClientexecGetInverseCanvasToScreen",
}
COMMON_PROLOGUE = bytes.fromhex("53 8B DC 83 EC 08 83 E4 F0 83 C4 04 55 8B 6B 04")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path,
                        default=GAME_ROOT / "Binaries/Win32/Dishonored.exe")
    parser.add_argument("--manifest", type=Path, default=BUILD / "files.csv")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    build_text = (BUILD / "build.md").read_text(encoding="utf-8")
    if "Steam build ID: `10256413`" not in build_text or EXE_SHA256 not in build_text:
        raise SystemExit("build record does not match the expected identity")
    executable = args.executable.resolve(strict=True)
    manifest_rows = read_csv(args.manifest.resolve(strict=True))
    exe_manifest = next((row for row in manifest_rows if row["relative_path"].replace("\\", "/").casefold()
                         == "binaries/win32/dishonored.exe"), None)
    if sha256_file(executable) != EXE_SHA256 or not exe_manifest \
            or exe_manifest["sha256"].upper() != EXE_SHA256:
        raise SystemExit("executable, manifest, and build record identity do not agree")

    raw_rows = read_csv(RAW_ROWS)
    join_rows = read_csv(JOIN_ROWS)
    targets = {int(row["raw_handler_target_va"], 16): row for row in raw_rows
               if not row["exact_function_index_start"].lower() == "true"}
    joined_by_target = {int(row["raw_handler_target_va"], 16): row for row in join_rows
                        if row["exact_function_index_start"].lower() != "true"}
    if set(targets) != set(EXPECTED) or len(join_rows) != 332 or any(int(row["containing_indexed_function_count"]) != 0 for row in targets.values()):
        raise SystemExit("EXP-0138 unresolved target set or EXP-0139 denominator changed")

    pe = pefile.PE(str(executable), fast_load=True)
    if pe.OPTIONAL_HEADER.Magic != 0x10B:
        raise SystemExit("expected PE32 executable")
    image_base = int(pe.OPTIONAL_HEADER.ImageBase)
    image = executable.read_bytes()

    def raw_section(va: int, size: int) -> tuple[str, int]:
        rva = va - image_base
        for section in pe.sections:
            start = int(section.VirtualAddress)
            end = start + int(section.SizeOfRawData)
            if start <= rva and rva + size <= end:
                name = section.Name.rstrip(b"\0").decode("ascii", errors="replace")
                return name, int(section.PointerToRawData) + rva - start
        raise ValueError(f"VA 0x{va:08X} is not fully backed by a raw PE section")

    indexed = sorted(int(row["address"], 16) for row in read_csv(FUNCTION_INDEX))
    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    summary_rows: list[dict[str, object]] = []
    instruction_rows: list[dict[str, object]] = []

    for target_va, expected_name in sorted(EXPECTED.items()):
        raw_row = targets[target_va]
        joined = joined_by_target.get(target_va)
        if not joined or joined["decoded_native_exec_name"] != expected_name \
                or raw_row["decoded_native_exec_name"] != expected_name:
            raise SystemExit(f"table name/export join differs for 0x{target_va:08X}")
        if joined["uelib_native_flag"].lower() != "true" or int(joined["uelib_native_token"]) != 0:
            raise SystemExit(f"UELib native metadata differs for {expected_name}")
        if raw_row["handler_target_section"] != ".text":
            raise SystemExit(f"target is not in .text: 0x{target_va:08X}")
        _, raw_offset = raw_section(target_va, len(COMMON_PROLOGUE))
        if image[raw_offset:raw_offset + len(COMMON_PROLOGUE)] != COMMON_PROLOGUE:
            raise SystemExit(f"common x86 entry prologue differs at 0x{target_va:08X}")

        next_indexed = next((address for address in indexed if address > target_va), None)
        if next_indexed is None:
            raise SystemExit(f"no following indexed entry for 0x{target_va:08X}")
        _, raw_to_next = raw_section(target_va, next_indexed - target_va)
        region = image[raw_to_next:raw_to_next + next_indexed - target_va]
        instructions = list(disassembler.disasm(region, target_va))
        if not instructions or instructions[0].address != target_va:
            raise SystemExit(f"Capstone did not decode entry 0x{target_va:08X}")
        ret = next((ins for ins in instructions if ins.mnemonic == "ret" and ins.op_str == "8"), None)
        if ret is None:
            raise SystemExit(f"no ret 8 found before next indexed function at 0x{target_va:08X}")
        code_end = ret.address + ret.size
        padding_size = next_indexed - code_end
        if padding_size < 0 or any(byte != 0xCC for byte in region[code_end - target_va:]):
            raise SystemExit(f"post-return region is not all int3 padding before 0x{next_indexed:08X}")
        function_instructions = [ins for ins in instructions if ins.address < code_end]
        if any(left.address + left.size != right.address
               for left, right in zip(function_instructions, function_instructions[1:])):
            raise SystemExit(f"Capstone left a decode gap in candidate body 0x{target_va:08X}")
        for ins in function_instructions:
            if ins.mnemonic.startswith("j") and ins.mnemonic not in ("jmp", "jecxz"):
                destination = int(ins.op_str, 16) if ins.op_str.startswith("0x") else None
                if destination is not None and not target_va <= destination < code_end:
                    raise SystemExit(f"conditional branch leaves candidate body: {ins.address:08X}")
            instruction_rows.append({
                "target_va": f"0x{target_va:08X}",
                "instruction_va": f"0x{ins.address:08X}",
                "bytes": ins.bytes.hex(" ").upper(),
                "mnemonic": ins.mnemonic,
                "operands": ins.op_str,
            })
        next_row = next(row for row in read_csv(FUNCTION_INDEX)
                        if int(row["address"], 16) == next_indexed)
        summary_rows.append({
            "build_id": "10256413",
            "exe_sha256": EXE_SHA256,
            "target_va": f"0x{target_va:08X}",
            "native_exec_name": expected_name,
            "uelib_function_object_path": joined["uelib_function_object_path"],
            "native_token": joined["uelib_native_token"],
            "native_declaration": joined["uelib_native_declaration"],
            "prologue_hex": COMMON_PROLOGUE.hex(" ").upper(),
            "ret_va": f"0x{ret.address:08X}",
            "ret_mnemonic": ret.mnemonic,
            "ret_operands": ret.op_str,
            "decoded_code_size": code_end - target_va,
            "int3_padding_bytes": padding_size,
            "next_indexed_function_va": f"0x{next_indexed:08X}",
            "next_indexed_function_name": next_row["name"],
            "body_boundary_claim": "candidate function boundary supported by table target, common prologue, ret 8, int3 padding, and following indexed entry",
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = args.output_dir / "EXP-0141-native-class-table-unindexed-target-boundaries.csv"
    instructions_csv = args.output_dir / "EXP-0141-native-class-table-unindexed-target-disassembly.csv"
    with summary_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary_rows)
    with instructions_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(instruction_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(instruction_rows)
    summary = {
        "build_id": "10256413",
        "exe_sha256": EXE_SHA256,
        "manifest_sha256": sha256_file(args.manifest.resolve(strict=True)),
        "exp_0138_input_sha256": sha256_file(RAW_ROWS),
        "exp_0139_input_sha256": sha256_file(JOIN_ROWS),
        "function_index_sha256": sha256_file(FUNCTION_INDEX),
        "capstone_version": __import__("capstone").__version__,
        "pefile_version": pefile.__version__,
        "candidate_targets": len(summary_rows),
        "common_prologue_matches": len(summary_rows),
        "ret_8_boundaries": sum(row["ret_mnemonic"] == "ret" and row["ret_operands"] == "8"
                                 for row in summary_rows),
        "targets_with_int3_only_post_return_padding": sum(row["int3_padding_bytes"] > 0 for row in summary_rows),
        "total_int3_post_return_padding_bytes": sum(int(row["int3_padding_bytes"]) for row in summary_rows),
        "summary_csv": summary_csv.name,
        "instruction_csv": instructions_csv.name,
        "limitations": [
            "The recovered entries are not added to the 72,437-row Ghidra function index.",
            "The entry boundary is supported by an exact table pointer target, repeated x86 prologue, ret 8, int3 padding, and the next indexed function entry; it is not a saved Ghidra function definition.",
            "Linear disassembly and UELib declaration matches do not establish runtime dispatch, concrete ownership, or behavior beyond the observed static body operations.",
        ],
    }
    summary_path = args.output_dir / "EXP-0141-native-class-table-unindexed-target-boundaries-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "candidate_targets", "common_prologue_matches", "ret_8_boundaries",
        "targets_with_int3_only_post_return_padding", "total_int3_post_return_padding_bytes", "summary_csv", "instruction_csv",
    )}, indent=2))


if __name__ == "__main__":
    main()

