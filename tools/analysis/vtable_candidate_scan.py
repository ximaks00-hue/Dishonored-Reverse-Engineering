#!/usr/bin/env python3
"""List aligned PE data runs containing pointers into the executable section.

The output is a candidate list only. Adjacent tables and unrelated pointer arrays
can merge into the same run; a run is not a vtable until code xrefs and object
construction establish that interpretation.
"""

from __future__ import annotations

import argparse
import csv
import struct
import sys
from pathlib import Path

import pefile


TARGET_SLOTS = {
    "powerwheel_on_selection_changed": 0x1F0,
    "controller_dis_select_power": 0x560,
}


def pointer_runs(image: bytes, pe: pefile.PE, text_start: int, text_end: int):
    image_base = pe.OPTIONAL_HEADER.ImageBase
    for section in pe.sections:
        section_name = section.Name.rstrip(b"\0").decode("ascii", errors="replace")
        if section_name not in {".rdata", ".data"}:
            continue

        section_va = image_base + section.VirtualAddress
        raw_start = section.PointerToRawData
        raw_size = section.SizeOfRawData
        blob = image[raw_start : raw_start + raw_size]

        # Align relative to the loaded section address, not the file offset.
        first = (-section_va) & 3
        run_start: int | None = None
        run_count = 0
        last_va = 0

        for offset in range(first, len(blob) - 3, 4):
            target = struct.unpack_from("<I", blob, offset)[0]
            current_va = section_va + offset
            points_into_text = text_start <= target < text_end

            if points_into_text:
                if run_start is None:
                    run_start = current_va
                    run_count = 1
                elif current_va == last_va + 4:
                    run_count += 1
                else:
                    yield section_name, run_start, last_va + 4, run_count
                    run_start = current_va
                    run_count = 1
                last_va = current_va
            elif run_start is not None:
                yield section_name, run_start, last_va + 4, run_count
                run_start = None
                run_count = 0

        if run_start is not None:
            yield section_name, run_start, last_va + 4, run_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--minimum-pointers", type=int, default=8)
    parser.add_argument("--output", type=Path, help="CSV destination; defaults to stdout")
    args = parser.parse_args()

    if args.minimum_pointers < 1:
        parser.error("--minimum-pointers must be positive")

    image_path = args.executable.resolve()
    image = image_path.read_bytes()
    pe = pefile.PE(data=image, fast_load=True)
    text = next(
        (section for section in pe.sections if section.Name.rstrip(b"\0") == b".text"),
        None,
    )
    if text is None:
        parser.error("PE image has no .text section")

    text_start = pe.OPTIONAL_HEADER.ImageBase + text.VirtualAddress
    text_end = text_start + max(text.Misc_VirtualSize, text.SizeOfRawData)
    rows = []
    for section, start, end, count in pointer_runs(image, pe, text_start, text_end):
        if count < args.minimum_pointers:
            continue
        row = {
            "section": section,
            "start_va": f"0x{start:08X}",
            "end_va_exclusive": f"0x{end:08X}",
            "pointer_count": count,
            "byte_length": count * 4,
        }
        for label, byte_offset in TARGET_SLOTS.items():
            row[f"covers_{label}"] = count * 4 > byte_offset
        rows.append(row)

    rows.sort(key=lambda row: (-row["pointer_count"], row["section"], row["start_va"]))
    fields = [
        "section",
        "start_va",
        "end_va_exclusive",
        "pointer_count",
        "byte_length",
        *(f"covers_{label}" for label in TARGET_SLOTS),
    ]

    output = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output:
            output.close()

    print(
        f"PE image base 0x{pe.OPTIONAL_HEADER.ImageBase:08X}; "
        f".text 0x{text_start:08X}–0x{text_end - 1:08X}; "
        f"candidate runs: {len(rows)} (minimum {args.minimum_pointers} pointers)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
