"""Read-only heuristic scan for x86 indirect calls through vtable slot +0x13C.

This finds instruction-pattern candidates only; it does not identify dynamic
receiver classes or prove that a target is Blink's update method.
"""

from __future__ import annotations

import argparse
import bisect
import csv
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_MEM, X86_OP_REG


ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "Dishonored RHCP" / "Binaries" / "Win32" / "Dishonored.exe"
FUNCTIONS = ROOT / "research" / "executable" / "functions.csv"
DEFAULT_OUT = ROOT / "research" / "executable" / "evidence" / "EXP-0046-slot13c-candidates.csv"
SLOT = 0x13C


def function_index(path: Path) -> tuple[list[int], list[tuple[int, int, str, str]]]:
    rows: list[tuple[int, int, str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append(
                (
                    int(row["body_start"], 16),
                    int(row["body_end"], 16),
                    row["address"],
                    row["name"],
                )
            )
    rows.sort()
    return [row[0] for row in rows], rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=EXE)
    parser.add_argument("--functions", type=Path, default=FUNCTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    starts, rows = function_index(args.functions)
    pe = pefile.PE(str(args.exe), fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True

    candidates: list[tuple[int, int]] = []
    direct_calls: list[int] = []
    decoded_instructions = 0
    skipped_bytes = 0

    for section in pe.sections:
        if not (section.Characteristics & 0x20000000):
            continue
        pending: list[tuple[str, int, int]] = []
        section_va = image_base + section.VirtualAddress
        for insn in decoder.disasm(section.get_data(), section_va):
            if insn.mnemonic == ".byte":
                skipped_bytes += insn.size
                continue
            decoded_instructions += 1

            still_pending: list[tuple[str, int, int]] = []
            for register, load_va, remaining in pending:
                if insn.mnemonic == "call" and insn.op_str.strip() == register:
                    candidates.append((load_va, insn.address))
                elif remaining > 1:
                    still_pending.append((register, load_va, remaining - 1))
            pending = still_pending

            if (
                insn.mnemonic == "mov"
                and len(insn.operands) == 2
                and insn.operands[0].type == X86_OP_REG
                and insn.operands[1].type == X86_OP_MEM
                and insn.operands[1].mem.disp == SLOT
            ):
                pending.append((insn.reg_name(insn.operands[0].reg), insn.address, 3))

            if (
                insn.mnemonic == "call"
                and insn.operands
                and insn.operands[0].type == X86_OP_MEM
                and insn.operands[0].mem.disp == SLOT
            ):
                direct_calls.append(insn.address)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("load_va", "call_va", "function_entry", "function_name"))
        for load_va, call_va in candidates:
            pos = bisect.bisect_right(starts, call_va) - 1
            if pos >= 0 and call_va <= rows[pos][1]:
                entry, name = rows[pos][2], rows[pos][3]
            else:
                entry, name = "", ""
            writer.writerow((f"0x{load_va:08X}", f"0x{call_va:08X}", entry, name))

    print(f"executable_sections_decoded={decoded_instructions}")
    print(f"skipped_data_bytes={skipped_bytes}")
    print(f"load_then_call_candidates={len(candidates)}")
    print(f"direct_memory_call_candidates={len(direct_calls)}")
    print(f"csv={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
