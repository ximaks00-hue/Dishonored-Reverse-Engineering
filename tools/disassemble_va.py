"""Decode read-only x86 bytes from an RVA-mapped executable VA range."""

from __future__ import annotations

import argparse
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE = ROOT / "Dishonored RHCP" / "Binaries" / "Win32" / "Dishonored.exe"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--end", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--print-from", type=lambda value: int(value, 0))
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be >= --start")

    pe = pefile.PE(str(args.exe), fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    start_rva, end_rva = args.start - image_base, args.end - image_base
    sections = [
        section for section in pe.sections
        if section.VirtualAddress <= start_rva
        and end_rva < section.VirtualAddress + max(section.Misc_VirtualSize, section.SizeOfRawData)
    ]
    if len(sections) != 1:
        parser.error("VA range must fit inside one PE section")
    file_offset = pe.get_offset_from_rva(start_rva)
    raw = pe.__data__[file_offset : file_offset + args.end - args.start + 1]
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    for insn in decoder.disasm(raw, args.start):
        if args.print_from is not None and insn.address < args.print_from:
            continue
        print(f"0x{insn.address:08X}: {insn.bytes.hex(' ').upper():<24} {insn.mnemonic:<8} {insn.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
