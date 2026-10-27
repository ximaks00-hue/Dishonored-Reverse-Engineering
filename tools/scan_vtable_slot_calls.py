"""Read-only x86 scan for load-then-indirect-call vtable slot candidates.

The output is heuristic: a matching displacement does not identify a receiver
class or prove that its vtable target is a particular function.
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--max-gap", type=int, default=8, help="maximum decoded instructions between slot load and call")
    parser.add_argument("--exe", type=Path, default=EXE)
    parser.add_argument("--functions", type=Path, default=FUNCTIONS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows: list[tuple[int, int, str, str]] = []
    with args.functions.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append((int(row["body_start"], 16), int(row["body_end"], 16), row["address"], row["name"]))
    rows.sort()
    starts = [row[0] for row in rows]

    pe = pefile.PE(str(args.exe), fast_load=True)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True
    candidates: list[tuple[int, int]] = []
    direct_calls: list[int] = []
    decoded = skipped = 0

    for section in pe.sections:
        if not (section.Characteristics & 0x20000000):
            continue
        pending: list[tuple[str, int, int]] = []
        for insn in decoder.disasm(section.get_data(), pe.OPTIONAL_HEADER.ImageBase + section.VirtualAddress):
            if insn.mnemonic == ".byte":
                skipped += insn.size
                continue
            decoded += 1
            next_pending: list[tuple[str, int, int]] = []
            _, written_regs = insn.regs_access()
            written_names = {decoder.reg_name(reg) for reg in written_regs}
            for register, load_va, remaining in pending:
                if insn.mnemonic == "call" and insn.op_str.strip() == register:
                    candidates.append((load_va, insn.address))
                elif remaining > 1 and register not in written_names:
                    next_pending.append((register, load_va, remaining - 1))
            pending = next_pending

            if (
                insn.mnemonic == "mov"
                and len(insn.operands) == 2
                and insn.operands[0].type == X86_OP_REG
                and insn.operands[1].type == X86_OP_MEM
                and insn.operands[1].mem.disp == args.slot
            ):
                pending.append((decoder.reg_name(insn.operands[0].reg), insn.address, args.max_gap + 1))
            if (
                insn.mnemonic == "call"
                and insn.operands
                and insn.operands[0].type == X86_OP_MEM
                and insn.operands[0].mem.disp == args.slot
            ):
                direct_calls.append(insn.address)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("load_va", "call_va", "function_entry", "function_name"))
        for load_va, call_va in candidates:
            pos = bisect.bisect_right(starts, call_va) - 1
            row = rows[pos] if pos >= 0 and call_va <= rows[pos][1] else None
            writer.writerow((f"0x{load_va:08X}", f"0x{call_va:08X}", row[2] if row else "", row[3] if row else ""))

    print(f"slot=0x{args.slot:X}")
    print(f"max_intervening_instructions={args.max_gap}")
    print(f"executable_instructions_decoded={decoded}")
    print(f"data_bytes_skipped={skipped}")
    print(f"load_then_call_candidates={len(candidates)}")
    print(f"direct_memory_call_candidates={len(direct_calls)}")
    print(f"csv={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
