#!/usr/bin/env python3
"""Validate report-derived role-specific vtable assessments (not the game binary)."""
import argparse, json, re
from pathlib import Path
ROLES = {"controller": 0x560, "powerwheel": 0x1F0}
STATUSES = {"needs_review", "deprioritized", "reported_excluded"}

def addr(s):
    if not isinstance(s, str) or re.fullmatch(r"0x[0-9a-fA-F]{1,8}", s) is None:
        raise ValueError(f"Invalid hex VA/slot: {s!r}")
    return int(s, 16)

def validate(d):
    assert d["evidence_level"] == "user_summary_only_not_independently_disassembled"
    assert addr(d["image_base"]) == 0x400000
    a = d["scan_summary"]
    assert a["raw_scan_available"] is False
    assert a["structurally_passing"] <= a["unique_candidate_addresses"]
    assert set(d["roles"]) == set(ROLES)
    assert all(addr(d["roles"][r]["slot_offset"]) == o for r,o in ROLES.items())
    seen = set()
    for x in d["candidates"]:
        va = addr(x["table_va"])
        assert va >= 0x400000 and va % 4 == 0 and va not in seen
        seen.add(va)
        assert set(x["evaluations"]) == set(ROLES)
        for role, y in x["evaluations"].items():
            assert y["status"] in STATUSES and y["observation"]
            if y["status"] == "reported_excluded":
                assert x.get("reported_owner"), "foreign owner must be named"
    return True

def report(d):
    validate(d)
    s = d["scan_summary"]
    out = ["# REV-0004 — EXP-0017 candidate ledger", "",
           "> Derived solely from user third-report summary; EXE, Ghidra, raw EXP-0017 not independently available.", "",
           f"Function entries: {s['index_functions']} vs previous {s['previous_ghidra_functions']} (difference {s['previous_ghidra_functions']-s['index_functions']}).",
           f"Pointer-write instructions: {s['vptr_store_instructions']}; candidates: {s['unique_candidate_addresses']}; structural passes: {s['structurally_passing']} ({s['structurally_passing']/s['unique_candidate_addresses']*100:.2f}%).", "",
           "| Table VA | Table RVA | Role | Status | Source observation |", "|---|---|---|---|---|"]
    for x in d["candidates"]:
        va = addr(x["table_va"])
        for role in ("powerwheel","controller"):
            y = x["evaluations"][role]
            out.append(f"| `{x['table_va']}` | `0x{va-0x400000:08X}` | {role} | {y['status']} | {y['observation'].replace('|','/')} |")
    out.extend(["", "A class owner is not established by structural matches. 'reported_excluded' must be rechecked against primary evidence."])
    return "\n".join(out)+"\n"

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("index", type=Path)
    parser.add_argument("--output", type=Path)
    opts=parser.parse_args()
    text=report(json.loads(opts.index.read_text(encoding="utf-8")))
    if opts.output:
        opts.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
