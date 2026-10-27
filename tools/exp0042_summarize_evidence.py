#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(
    csv.DictReader((ROOT / ".tmp" / "EXP-0042-owner-evidence.csv").open(encoding="utf-8"))
)
print("rows", len(rows))
by: dict[tuple[str, str], list] = defaultdict(list)
for r in rows:
    by[(r["kind"], r["subject"])].append(r)

interesting = (
    "BFAE60",
    "BFAFD0",
    "BF8C00",
    "BFC990",
    "BFE3C0",
    "CF34E0",
    "BF9A10",
    "BF8A20",
    "BE7580",
)
for (kind, subj), items in sorted(by.items()):
    if kind == "xref_to_func" and any(x in subj for x in interesting):
        print(f"\n## {kind} {subj} ({len(items)})")
        for r in items[:40]:
            print(f"  {r['from_addr']} {r['from_func']} [{r['ref_type']}]")
    if kind == "xref_to_slot":
        print(f"\n## slot {subj} n={len(items)}")
        print(f"   detail0={items[0].get('detail', '')[:120]}")
        for r in items[:20]:
            if r["from_addr"]:
                print(
                    f"  {r['from_addr']} {r['from_func']} [{r['ref_type']}] -> {r['to_func']}"
                )

print("\n## calls of interest from BFAE60 / BFAFD0 / BFC990")
for (kind, subj), items in sorted(by.items()):
    if kind != "call_from_func":
        continue
    if not any(x in subj for x in ("BFAE60", "BFAFD0", "BF8C00", "BFC990")):
        continue
    print(f"\n### from {subj}")
    for r in items:
        if any(
            x in (r["to_func"] or "")
            for x in ("BF8C00", "BFC990", "6539C0", "BECDF0", "BFAE", "BE8D60", "BFAB80")
        ):
            print(f"  {r['from_addr']} -> {r['to_addr']} {r['to_func']} [{r['ref_type']}]")
