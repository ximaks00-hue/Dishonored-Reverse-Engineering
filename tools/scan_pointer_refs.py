"""Find raw PE occurrences of a 32-bit VA and map code references to functions."""

from __future__ import annotations

import argparse
import bisect
import csv
import struct
from pathlib import Path

import pefile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE = ROOT / "Dishonored RHCP" / "Binaries" / "Win32" / "Dishonored.exe"
DEFAULT_FUNCTIONS = ROOT / "research" / "executable" / "functions.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--va", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--functions", type=Path, default=DEFAULT_FUNCTIONS)
    parser.add_argument("--code-only", action="store_true", help="search executable sections only")
    args = parser.parse_args()

    rows: list[tuple[int, int, str, str]] = []
    with args.functions.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append((int(row["body_start"], 16), int(row["body_end"], 16), row["address"], row["name"]))
    rows.sort()
    starts = [row[0] for row in rows]

    pe = pefile.PE(str(args.exe), fast_load=True)
    needle = struct.pack("<I", args.va)
    hits = 0
    for section in pe.sections:
        if args.code_only and not (section.Characteristics & 0x20000000):
            continue
        data = section.get_data()
        offset = 0
        while True:
            offset = data.find(needle, offset)
            if offset < 0:
                break
            file_offset = section.PointerToRawData + offset
            ref_va = pe.OPTIONAL_HEADER.ImageBase + section.VirtualAddress + offset
            pos = bisect.bisect_right(starts, ref_va) - 1
            if section.Characteristics & 0x20000000 and pos >= 0 and ref_va <= rows[pos][1]:
                owner = f"{rows[pos][2]} {rows[pos][3]}"
            elif section.Characteristics & 0x20000000:
                owner = "unmapped-code"
            else:
                owner = "data"
            print(f"ref_va=0x{ref_va:08X} file_offset=0x{file_offset:X} section={section.Name.rstrip(bytes([0])).decode(errors='replace')} owner={owner}")
            hits += 1
            offset += 1
    print(f"target=0x{args.va:08X} occurrences={hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
