#!/usr/bin/env python3
"""Find writers of object+0x60 vector (direct stores or lea/add +0x60 then store).

Prioritize Blink vtable methods (0x01168698 .. 0x01168870). Exclude treating
DevouringSwarm FUN_00BF8C00 as a Blink writer (EXP-0042).
"""

from __future__ import annotations

import csv
import struct
import sys
from collections import defaultdict
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_EBP, X86_REG_ESP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mcp_servers.common.config import get_settings

IMAGE_BASE = 0x00400000
BLINK_VT = 0x01168698
BLINK_VT_END = 0x01168870  # DarkVision table start (EXP-0027)
SWARM_EXCLUDE = {0x00BF8C00, 0x00BFAE60, 0x00BFAFD0, 0x00BFE3C0}
OFFSETS = {0x60, 0x64, 0x68}


def pe_sections(data: bytes):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, e + 6)[0]
    opt = struct.unpack_from("<H", data, e + 20)[0]
    off = e + 24 + opt
    secs = []
    for i in range(n):
        o = off + i * 40
        name = data[o : o + 8].split(b"\0", 1)[0].decode("latin1", "replace")
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", data, o + 8)
        secs.append((name, va, vsize, raw_ptr, raw_size))
    return secs


def va_to_off(secs, va: int) -> int | None:
    rva = va - IMAGE_BASE
    for _n, va0, vs, rp, rs in secs:
        if va0 <= rva < va0 + rs:
            return rp + (rva - va0)
    return None


def read_u32(data, secs, va: int) -> int | None:
    o = va_to_off(secs, va)
    if o is None or o + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, o)[0]


def load_functions_csv() -> list[tuple[int, int, str]]:
    path = ROOT / "research" / "executable" / "functions.csv"
    rows: list[tuple[int, int, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            start = int(row["address"], 16)
            end = int(row["body_end"], 16) + 1
            rows.append((start, end, row.get("name") or f"FUN_{start:08X}"))
    rows.sort()
    return rows


def containing(funcs: list[tuple[int, int, str]], va: int) -> tuple[int, int, str] | None:
    lo, hi = 0, len(funcs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s, e, n = funcs[mid]
        if va < s:
            hi = mid - 1
        elif va >= e:
            lo = mid + 1
        else:
            return s, e, n
    return None


def scan_function(md: Cs, data: bytes, secs, start: int, end: int) -> list[dict]:
    """Return write/lea evidence for +0x60 vector inside [start,end)."""
    off = va_to_off(secs, start)
    if off is None:
        return []
    size = min(end - start, 0x10000)
    code = data[off : off + size]
    hits: list[dict] = []
    # Track registers that currently hold ptr to obj+0x60 (approx, local linear scan).
    vec_regs: dict[int, int] = {}  # reg_id -> site that defined it

    for insn in md.disasm(code, start):
        mne = insn.mnemonic.lower()
        ops = insn.operands or []

        # Invalidate regs overwritten as destinations (rough).
        if ops and ops[0].type == X86_OP_REG and mne not in {"push", "pop"}:
            # lea/mov that redefine tracked reg handled below
            pass

        if mne == "lea" and len(ops) >= 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_MEM:
            mem = ops[1].mem
            if mem.index == 0 and mem.disp == 0x60 and mem.base not in (0, X86_REG_ESP, X86_REG_EBP):
                vec_regs[ops[0].reg] = insn.address
                hits.append(
                    {
                        "kind": "lea_plus_60",
                        "site": f"0x{insn.address:08X}",
                        "disp": "0x60",
                        "insn": f"{insn.mnemonic} {insn.op_str}",
                    }
                )
            else:
                # lea redefined without +0x60 — drop that dest reg
                vec_regs.pop(ops[0].reg, None)

        if mne == "add" and len(ops) >= 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_IMM:
            if ops[1].imm == 0x60:
                vec_regs[ops[0].reg] = insn.address
                hits.append(
                    {
                        "kind": "add_plus_60",
                        "site": f"0x{insn.address:08X}",
                        "disp": "0x60",
                        "insn": f"{insn.mnemonic} {insn.op_str}",
                    }
                )

        if mne.startswith("mov") and ops and ops[0].type == X86_OP_MEM:
            mem = ops[0].mem
            if mem.index != 0:
                continue
            if mem.base in (0, X86_REG_ESP, X86_REG_EBP):
                continue
            # Direct [reg+0x60/64/68]
            if mem.disp in OFFSETS:
                hits.append(
                    {
                        "kind": "store_disp",
                        "site": f"0x{insn.address:08X}",
                        "disp": f"0x{mem.disp:X}",
                        "insn": f"{insn.mnemonic} {insn.op_str}",
                    }
                )
            # Store through pointer previously LEA'd to +0x60: [reg]/[reg+4]/[reg+8]
            elif mem.base in vec_regs and mem.disp in (0, 4, 8):
                hits.append(
                    {
                        "kind": "store_via_lea60",
                        "site": f"0x{insn.address:08X}",
                        "disp": f"0x{0x60 + mem.disp:X}",
                        "insn": f"{insn.mnemonic} {insn.op_str}",
                        "lea_site": f"0x{vec_regs[mem.base]:08X}",
                    }
                )

        # Simple kill: mov reg, ... clears vector tracking for that reg
        if mne.startswith("mov") and ops and ops[0].type == X86_OP_REG:
            if not (mne == "lea"):
                # lea handled above
                if ops[0].reg in vec_regs and not (
                    len(ops) > 1 and ops[1].type == X86_OP_MEM and ops[1].mem.disp == 0x60
                ):
                    # keep if this mov is storing through it (dest was mem) — already handled
                    if ops[0].type == X86_OP_REG and mne.startswith("mov"):
                        # destination reg redefined
                        if not (len(ops) > 1 and ops[1].type == X86_OP_MEM and ops[1].mem.disp == 0x60):
                            vec_regs.pop(ops[0].reg, None)

    return hits


def main() -> int:
    settings = get_settings()
    data = settings.game_exe.read_bytes()
    secs = pe_sections(data)
    funcs = load_functions_csv()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    blink_methods: dict[int, str] = {}
    for slot in range(0, BLINK_VT_END - BLINK_VT, 4):
        val = read_u32(data, secs, BLINK_VT + slot)
        if val is None or val < IMAGE_BASE:
            continue
        hit = containing(funcs, val)
        name = hit[2] if hit else f"FUN_{val:08X}"
        blink_methods[val] = f"0x{slot:X}"

    out_dir = ROOT / ".tmp"
    out_dir.mkdir(exist_ok=True)

    rows = []
    # 1) Blink vtable methods
    for entry, slot in sorted(blink_methods.items()):
        hit = containing(funcs, entry)
        if not hit:
            continue
        start, end, name = hit
        for ev in scan_function(md, data, secs, start, end):
            rows.append(
                {
                    "scope": "blink_vtable",
                    "func": name,
                    "func_entry": f"0x{start:08X}",
                    "slot": slot,
                    **ev,
                }
            )

    # 2) Scan FUN_00BF* / FUN_00BE* bodies that are NOT swarm-excluded, for lea/store patterns
    #    Also include known move-path helpers.
    extra_entries = set()
    for start, end, name in funcs:
        if name.startswith("FUN_00BF") or name.startswith("FUN_00BE"):
            if start in SWARM_EXCLUDE:
                continue
            if start in blink_methods:
                continue
            extra_entries.add((start, end, name))
    # Always include move-path related known funcs
    for addr in (
        0x00BFC160,
        0x00BFC5D0,
        0x00BECDF0,
        0x00BE89E0,
        0x00BE7580,
        0x00BF9A10,
        0x00CF34E0,
        0x00CF3360,
        0x00CF3540,
        0x00BE9520,
        0x00BE9310,
    ):
        hit = containing(funcs, addr)
        if hit and hit[0] not in SWARM_EXCLUDE:
            extra_entries.add(hit)

    for start, end, name in sorted(extra_entries):
        for ev in scan_function(md, data, secs, start, end):
            # Only keep if evidence looks like a vector write, not mere lea without store
            rows.append(
                {
                    "scope": "blink_family_scan",
                    "func": name,
                    "func_entry": f"0x{start:08X}",
                    "slot": "",
                    **ev,
                }
            )

    # Collapse: functions with any store_via_lea60 or store_disp covering the triple
    by_func: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_func[r["func"]].append(r)

    writers = []
    for func, evs in by_func.items():
        kinds = {e["kind"] for e in evs}
        disps = {e.get("disp") for e in evs if e["kind"] in {"store_disp", "store_via_lea60"}}
        if "store_via_lea60" in kinds or len(disps) >= 2 or disps & {"0x60", "0x64", "0x68"}:
            scope = "blink_vtable" if any(e["scope"] == "blink_vtable" for e in evs) else "blink_family_scan"
            writers.append((func, scope, sorted(disps), evs))

    csv_path = out_dir / "EXP-0043-field60-write-evidence.csv"
    flat_fields = [
        "scope",
        "func",
        "func_entry",
        "slot",
        "kind",
        "site",
        "disp",
        "insn",
        "lea_site",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=flat_fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r.setdefault("lea_site", "")
            w.writerow(r)

    print(f"blink_vtable_methods={len(blink_methods)}")
    print(f"evidence_rows={len(rows)} -> {csv_path}")
    print("candidate writers:")
    for func, scope, disps, evs in sorted(writers, key=lambda x: (x[1] != "blink_vtable", x[0])):
        entry = next(e["func_entry"] for e in evs)
        slot = next((e["slot"] for e in evs if e.get("slot")), "")
        print(f"  [{scope}] {func} {entry} slot={slot} disps={disps}")
        for e in evs:
            if e["kind"] in {"lea_plus_60", "add_plus_60", "store_disp", "store_via_lea60"}:
                extra = f" lea@{e['lea_site']}" if e.get("lea_site") else ""
                print(f"      {e['kind']} {e['site']} {e['disp']} :: {e['insn']}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
