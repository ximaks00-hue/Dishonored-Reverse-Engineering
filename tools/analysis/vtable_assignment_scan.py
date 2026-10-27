#!/usr/bin/env python3
"""Find constructor-installed object-base pointers and score selected slots.

This is a candidate generator, not a vtable recognizer. It disassembles the
function ranges in a Ghidra CSV index, records 32-bit immediate stores into
PE .rdata/.data, and checks configured offsets for exact function-start hits.
Adjacent tables, constants, and unrelated object tables can still score well;
each result requires constructor and target-function validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import struct
import sys
from collections import defaultdict
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM


DEFAULT_OFFSETS = (
    0x1F0,
    0x4F8,
    0x4FC,
    0x500,
    0x504,
    0x508,
    0x50C,
    0x510,
    0x514,
    0x518,
    0x560,
)


def parse_offsets(value: str) -> list[int]:
    try:
        offsets = [int(item.strip(), 0) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid offset list: {exc}") from exc
    if not offsets or any(offset < 0 for offset in offsets):
        raise argparse.ArgumentTypeError("at least one nonnegative offset is required")
    return offsets


def load_function_index(path: Path) -> tuple[dict[int, dict[str, str]], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    required = {"address", "name", "signature", "body_start", "body_end"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"function index must include columns: {', '.join(sorted(required))}")
    by_address = {int(row["address"], 16): row for row in rows}
    return by_address, rows


def section_map(pe: pefile.PE):
    base = pe.OPTIONAL_HEADER.ImageBase
    return [
        (
            base + section.VirtualAddress,
            base + section.VirtualAddress + max(section.Misc_VirtualSize, section.SizeOfRawData),
            section.PointerToRawData,
            section.SizeOfRawData,
            section.Name.rstrip(b"\0").decode("ascii", errors="replace"),
        )
        for section in pe.sections
    ]


def map_address(address: int, sections):
    for start, end, raw_start, raw_size, name in sections:
        if start <= address < min(end, start + raw_size):
            return raw_start + address - start, name
    return None, None


def find_assignments(
    image: bytes,
    sections,
    functions: list[dict[str, str]],
    member_offset: int,
):
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    assignments: dict[int, list[tuple[int, int, str]]] = defaultdict(list)

    for function in functions:
        start = int(function["body_start"], 16)
        end = int(function["body_end"], 16)
        raw_start, _ = map_address(start, sections)
        if raw_start is None or end <= start:
            continue
        code = image[raw_start : raw_start + end - start]
        for instruction in decoder.disasm(code, start):
            if instruction.mnemonic != "mov" or len(instruction.operands) < 2:
                continue
            destination, source = instruction.operands[:2]
            if (
                destination.type != X86_OP_MEM
                or destination.size != 4
                or destination.mem.base == 0
                or destination.mem.index != 0
                or destination.mem.disp != member_offset
                or source.type != X86_OP_IMM
            ):
                continue
            address = source.imm & 0xFFFFFFFF
            _, section_name = map_address(address, sections)
            if section_name not in {".rdata", ".data"}:
                continue
            if address & 3:
                continue
            assignments[address].append(
                (instruction.address, int(function["address"], 16), function["name"])
            )
    return assignments


def score_candidates(image: bytes, sections, function_index, assignments, offsets, minimum):
    results = []
    for address, references in assignments.items():
        matches = []
        slot_values = []
        for offset in offsets:
            raw, section_name = map_address(address + offset, sections)
            value = struct.unpack_from("<I", image, raw)[0] if raw is not None else 0
            function = function_index.get(value)
            slot_values.append((offset, value, function["name"] if function else ""))
            if function:
                matches.append(offset)
        if len(matches) < minimum:
            continue
        _, section_name = map_address(address, sections)
        results.append(
            {
                "address": f"0x{address:08X}",
                "section": section_name,
                "assignment_count": len(references),
                "function_start_slots": len(matches),
                "tested_slots": len(offsets),
                "matched_offsets": ";".join(f"0x{x:X}" for x in matches),
                "slot_targets": ";".join(
                    f"0x{offset:X}=0x{value:08X}:{name}"
                    for offset, value, name in slot_values
                ),
                "assignments": ";".join(
                    f"0x{instruction:08X}:{function_name}"
                    for instruction, _, function_name in references
                ),
            }
        )
    results.sort(
        key=lambda row: (
            -int(row["function_start_slots"]),
            -int(row["assignment_count"]),
            row["address"],
        )
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("function_index", type=Path)
    parser.add_argument("--offsets", type=parse_offsets, default=list(DEFAULT_OFFSETS))
    parser.add_argument(
        "--member-offset",
        type=lambda value: int(value, 0),
        default=0,
        help="destination field offset of the assigned pointer (default: object base, 0)",
    )
    parser.add_argument("--minimum-function-slots", type=int, default=8)
    parser.add_argument("--output", type=Path, help="CSV path; defaults to stdout")
    args = parser.parse_args()
    if args.minimum_function_slots < 1 or args.minimum_function_slots > len(args.offsets):
        parser.error("--minimum-function-slots must be within 1..number of offsets")

    image_path = args.executable.resolve()
    image = image_path.read_bytes()
    pe = pefile.PE(data=image, fast_load=True)
    function_index, functions = load_function_index(args.function_index)
    sections = section_map(pe)
    assignments = find_assignments(image, sections, functions, args.member_offset)
    results = score_candidates(
        image, sections, function_index, assignments, args.offsets, args.minimum_function_slots
    )

    fields = [
        "address",
        "section",
        "assignment_count",
        "function_start_slots",
        "tested_slots",
        "matched_offsets",
        "slot_targets",
        "assignments",
    ]
    output = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    finally:
        if args.output:
            output.close()

    print(
        f"EXE SHA-256: {hashlib.sha256(image).hexdigest().upper()}; "
        f"input: {image_path}; indexed functions: {len(functions)}; "
        f"direct object-base pointer assignments: {sum(map(len, assignments.values()))}; "
        f"unique assigned addresses: {len(assignments)}; candidates with "
        f">={args.minimum_function_slots}/{len(args.offsets)} slot targets at indexed "
        f"function starts: {len(results)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
