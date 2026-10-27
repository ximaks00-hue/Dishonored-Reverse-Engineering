#!/usr/bin/env python3
"""Read-only probe: which tables contain candidate producer/consumer methods?"""

from __future__ import annotations

import csv
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp_servers.common.config import get_settings

IMAGE_BASE = 0x00400000
TARGETS = {
    "FUN_00BFAE60": 0x00BFAE60,
    "FUN_00BFAFD0": 0x00BFAFD0,
    "FUN_00BF8C00": 0x00BF8C00,
    "FUN_00BFC990": 0x00BFC990,
    "FUN_00BFE3C0": 0x00BFE3C0,
    "FUN_00BF8DD0": 0x00BF8DD0,
    "FUN_00BE7580": 0x00BE7580,
    "FUN_00BFC5D0": 0x00BFC5D0,
}

TABLES = {
    "Blink_01168698": 0x01168698,
    "ActivePowerBase_01167F60": 0x01167F60,
    "CandidateRegion_01168380": 0x01168380,
}


def pe_sections(data: bytes):
    assert data[:2] == b"MZ"
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew : e_lfanew + 4] == b"PE\0\0"
    coff = e_lfanew + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    sec_off = coff + 20 + opt_size
    sections = []
    for i in range(nsec):
        off = sec_off + i * 40
        name = data[off : off + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
        sections.append((name, va, vsize, raw_ptr, raw_size))
    return sections


def va_to_file(sections, va: int) -> int | None:
    rva = va - IMAGE_BASE
    for _name, sec_va, vsize, raw_ptr, raw_size in sections:
        if sec_va <= rva < sec_va + max(vsize, raw_size):
            return raw_ptr + (rva - sec_va)
    return None


def read_u32(data: bytes, sections, va: int) -> int | None:
    off = va_to_file(sections, va)
    if off is None or off + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, off)[0]


def main() -> int:
    settings = get_settings()
    exe = settings.game_exe
    data = exe.read_bytes()
    sections = pe_sections(data)
    out_dir = ROOT / ".tmp"
    out_dir.mkdir(exist_ok=True)

    # 1) Scan known tables for target function pointers.
    rows = []
    for table_name, start in TABLES.items():
        size = 0x800 if "Candidate" in table_name or "Active" in table_name else 0x400
        for slot in range(0, size, 4):
            va = start + slot
            val = read_u32(data, sections, va)
            if val is None:
                continue
            for name, target in TARGETS.items():
                if val == target:
                    rows.append(
                        {
                            "table": table_name,
                            "slot_va": f"0x{va:08X}",
                            "slot_off": f"0x{slot:X}",
                            "target": name,
                            "target_va": f"0x{target:08X}",
                        }
                    )
    csv_path = out_dir / "EXP-0042-table-hits.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["table", "slot_va", "slot_off", "target", "target_va"]
        )
        writer.writeheader()
        writer.writerows(rows)

    # 2) Absolute image scan for each target VA as little-endian DWORD.
    abs_hits = []
    for name, target in TARGETS.items():
        needle = struct.pack("<I", target)
        start = 0
        while True:
            idx = data.find(needle, start)
            if idx < 0:
                break
            # Map file offset back to VA for .rdata/.data mostly.
            for sec_name, sec_va, vsize, raw_ptr, raw_size in sections:
                if raw_ptr <= idx < raw_ptr + raw_size:
                    rva = sec_va + (idx - raw_ptr)
                    abs_hits.append(
                        {
                            "target": name,
                            "file_off": f"0x{idx:X}",
                            "section": sec_name,
                            "ptr_va": f"0x{IMAGE_BASE + rva:08X}",
                        }
                    )
                    break
            start = idx + 1

    abs_path = out_dir / "EXP-0042-absolute-ptr-hits.csv"
    with abs_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["target", "file_off", "section", "ptr_va"]
        )
        writer.writeheader()
        writer.writerows(abs_hits)

    # 3) Blink constructor installs — dump first slots of Blink table for sanity.
    blink_slots = []
    for slot in range(0, 0x200, 4):
        va = 0x01168698 + slot
        val = read_u32(data, sections, va)
        blink_slots.append((f"0x{slot:X}", f"0x{va:08X}", f"0x{val:08X}" if val else ""))

    print(f"exe={exe}")
    print(f"table_hits={len(rows)} -> {csv_path}")
    for row in rows:
        print(
            f"  {row['table']} {row['slot_off']} @ {row['slot_va']} -> {row['target']}"
        )
    print(f"absolute_hits={len(abs_hits)} -> {abs_path}")
    for hit in abs_hits:
        if hit["target"] in {
            "FUN_00BFAE60",
            "FUN_00BFAFD0",
            "FUN_00BF8C00",
            "FUN_00BFC990",
        }:
            print(f"  {hit['target']} ptr @ {hit['ptr_va']} ({hit['section']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
