#!/usr/bin/env python3
"""Per-function scan for lea/add +0x60 followed by stores to [reg]/[reg+4]/[reg+8].

Maps results to Blink vtable methods vs other vs Swarm-excluded (EXP-0042).
"""

from __future__ import annotations

import csv
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_EBP, X86_REG_ESP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mcp_servers.common.config import get_settings

IMAGE = 0x00400000
BLINK_VT = 0x01168698
BLINK_END = 0x01168870
SWARM = {0x00BF8C00, 0x00BFAE60, 0x00BFAFD0, 0x00BFE3C0}


def pe_sections(data: bytes):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    off = e + 24 + opt
    out = []
    for i in range(n):
        o = off + i * 40
        name = data[o : o + 8].split(b"\0", 1)[0].decode("latin1", "replace")
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", data, o + 8)
        out.append((name, va, vsize, raw_ptr, raw_size))
    return out


def va_to_off(secs, va: int) -> int | None:
    rva = va - IMAGE
    for _n, va0, _vs, rp, rs in secs:
        if va0 <= rva < va0 + rs:
            return rp + (rva - va0)
    return None


def read_u32(data, secs, va: int) -> int | None:
    o = va_to_off(secs, va)
    if o is None:
        return None
    return struct.unpack_from("<I", data, o)[0]


def load_funcs():
    rows = []
    with (ROOT / "research/executable/functions.csv").open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append((int(row["address"], 16), int(row["body_end"], 16) + 1, row["name"]))
    rows.sort()
    return rows


def follow_stores(insns, idx: int, dest_reg: int) -> list[str]:
    stores: list[str] = []
    for j in range(idx + 1, min(idx + 32, len(insns))):
        nxt = insns[j]
        ops = nxt.operands or []
        if not ops:
            continue
        # redefine dest as register dest of lea/mov/add/xor/...
        if ops[0].type == X86_OP_REG and ops[0].reg == dest_reg:
            if nxt.mnemonic.startswith("mov") and ops[0].type == X86_OP_REG:
                break
            if nxt.mnemonic in {"lea", "add", "sub", "xor", "or", "and", "pop"}:
                break
        if nxt.mnemonic.startswith("mov") and ops[0].type == X86_OP_MEM:
            mem = ops[0].mem
            if mem.base == dest_reg and mem.index == 0 and mem.disp in (0, 4, 8):
                stores.append(f"0x{nxt.address:08X}:{nxt.mnemonic} {nxt.op_str}")
        if nxt.mnemonic in {"ret", "retn"}:
            break
    return stores


def scan_func(md: Cs, data: bytes, secs, start: int, end: int) -> list[dict]:
    off = va_to_off(secs, start)
    if off is None:
        return []
    size = min(max(0, end - start), 0x10000)
    if size < 4:
        return []
    code = data[off : off + size]
    try:
        insns = list(md.disasm(code, start))
    except Exception:
        return []
    hits = []
    for idx, insn in enumerate(insns):
        ops = insn.operands or []
        # lea reg, [base+0x60]
        if (
            insn.mnemonic == "lea"
            and len(ops) >= 2
            and ops[0].type == X86_OP_REG
            and ops[1].type == X86_OP_MEM
        ):
            mem = ops[1].mem
            if mem.disp == 0x60 and mem.index == 0 and mem.base not in (0, X86_REG_ESP, X86_REG_EBP):
                stores = follow_stores(insns, idx, ops[0].reg)
                hits.append(
                    {
                        "kind": "lea_plus_60",
                        "site": f"0x{insn.address:08X}",
                        "insn": f"{insn.mnemonic} {insn.op_str}",
                        "stores": ";".join(stores),
                        "store_count": len(stores),
                    }
                )
        # add reg, 0x60
        if (
            insn.mnemonic == "add"
            and len(ops) >= 2
            and ops[0].type == X86_OP_REG
            and ops[1].type == X86_OP_IMM
            and ops[1].imm == 0x60
        ):
            stores = follow_stores(insns, idx, ops[0].reg)
            hits.append(
                {
                    "kind": "add_plus_60",
                    "site": f"0x{insn.address:08X}",
                    "insn": f"{insn.mnemonic} {insn.op_str}",
                    "stores": ";".join(stores),
                    "store_count": len(stores),
                }
            )
        # direct store [reg+0x60/64/68]
        if insn.mnemonic.startswith("mov") and ops and ops[0].type == X86_OP_MEM:
            mem = ops[0].mem
            if (
                mem.index == 0
                and mem.disp in (0x60, 0x64, 0x68)
                and mem.base not in (0, X86_REG_ESP, X86_REG_EBP)
            ):
                hits.append(
                    {
                        "kind": "store_disp",
                        "site": f"0x{insn.address:08X}",
                        "insn": f"{insn.mnemonic} {insn.op_str}",
                        "stores": f"0x{insn.address:08X}:{insn.mnemonic} {insn.op_str}",
                        "store_count": 1,
                        "disp": f"0x{mem.disp:X}",
                    }
                )
    return hits


def main() -> int:
    data = get_settings().game_exe.read_bytes()
    secs = pe_sections(data)
    funcs = load_funcs()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    blink_methods: dict[int, str] = {}
    for slot in range(0, BLINK_END - BLINK_VT, 4):
        v = read_u32(data, secs, BLINK_VT + slot)
        if v and v >= IMAGE:
            blink_methods[v] = f"0x{slot:X}"

    rows = []
    for start, end, name in funcs:
        hits = scan_func(md, data, secs, start, end)
        if not hits:
            continue
        if start in SWARM:
            scope = "swarm_excluded"
        elif start in blink_methods:
            scope = "blink_vtable"
        else:
            scope = "other"
        for h in hits:
            rows.append(
                {
                    "scope": scope,
                    "func": name,
                    "func_entry": f"0x{start:08X}",
                    "slot": blink_methods.get(start, ""),
                    "kind": h["kind"],
                    "site": h["site"],
                    "insn": h["insn"],
                    "store_count": h["store_count"],
                    "stores": h["stores"],
                    "disp": h.get("disp", ""),
                }
            )

    out = ROOT / ".tmp" / "EXP-0043-lea60-all.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        fields = [
            "scope",
            "func",
            "func_entry",
            "slot",
            "kind",
            "site",
            "insn",
            "store_count",
            "stores",
            "disp",
        ]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"sites={len(rows)} -> {out}")
    for scope in ("blink_vtable", "other", "swarm_excluded"):
        subset = [r for r in rows if r["scope"] == scope]
        # Prefer true writers (store_count>=1 for lea/add, or store_disp)
        writers = [
            r
            for r in subset
            if (r["kind"] in {"lea_plus_60", "add_plus_60"} and int(r["store_count"]) >= 1)
            or r["kind"] == "store_disp"
        ]
        print(f"\n## {scope}: evidence={len(subset)} writers={len(writers)}")
        shown = writers if writers else subset[:20]
        for r in shown[:40]:
            print(
                f"  {r['func']} entry={r['func_entry']} slot={r['slot']} "
                f"{r['kind']}@{r['site']} stores={r['store_count']}"
            )
            if r["stores"]:
                print(f"      {r['stores'][:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
