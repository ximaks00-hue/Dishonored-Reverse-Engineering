#!/usr/bin/env python3
"""Prioritize native body review from published, build-scoped evidence.

No game executable or decompiler is needed. All outcomes are *candidates*.
Scores are heuristic ranking aids, NOT evidence or understanding coverage.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research/executable/evidence/function-triage/native-class-table-handler-candidates-EXP-0139.csv"
REVIEWS = ROOT / "research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0155.csv"

def address(value: str) -> str:
    v = value.strip().lower().removeprefix("0x")
    n = int(v, 16)
    if n < 0 or n > 0xffffffff:
        raise ValueError("address outside 32-bit range")
    return f"{n:08X}"

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def rank_candidates(candidates: list[dict[str, str]], reviews: list[dict[str, str]]) -> list[dict]:
    reviewed = {address(row["address"]) for row in reviews}
    result = []
    seen = set()
    for row in candidates:
        va = address(row["address"])
        if va in seen:
            raise ValueError(f"duplicate candidate address {va}")
        seen.add(va)
        methods = json.loads(row["source_class_methods_json"])
        if not isinstance(methods, list):
            raise ValueError(f"{va}: methods must be a list")
        edge_count = int(row["pointer_target_edge_count"])
        size = int(row["size_bytes"])
        if edge_count < 0 or size < 0:
            raise ValueError(f"{va}: negative count or size")
        if va in reviewed:
            continue
        families = sorted({str(m.get("uelib_function", "")).split("'")[0] for m in methods})
        # High fan-in creates leverage, but cap it to avoid central generic dispatch bias.
        fanin = min(edge_count, 10) * 4
        # Modest preference for tractable bodies; large ones are not inherently less important.
        effort = 6 if 0 < size <= 256 else (3 if size <= 768 else 0)
        ambiguity = 2 if len(methods) > 1 else 0
        score = fanin + effort + ambiguity
        result.append({
            "address": va, "name": row.get("name", ""), "size_bytes": size,
            "pointer_target_edge_count": edge_count, "linked_method_count": len(methods),
            "score": score, "review_status": "candidate_not_body_reviewed",
            "source": "EXP-0139", "method_examples": "; ".join(
                str(m.get("uelib_function", "")) for m in methods[:3]),
            "next_check": "Verify raw target bytes, class/receiver provenance, ABI, relevant callers and alternatives",
        })
    return sorted(result, key=lambda r: (-r["score"], -r["pointer_target_edge_count"], r["size_bytes"], r["address"]))

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["address","name","size_bytes","pointer_target_edge_count","linked_method_count",
              "score","review_status","source","method_examples","next_check"]
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates",type=Path,default=CANDIDATES)
    p.add_argument("--reviews",type=Path,default=REVIEWS)
    p.add_argument("--output",type=Path,default=ROOT/"reports/native-review-queue.csv")
    p.add_argument("--limit",type=int,default=50)
    args=p.parse_args()
    if args.limit < 1: p.error("--limit must be positive")
    candidates=read_csv(args.candidates)
    reviews=read_csv(args.reviews)
    rows=rank_candidates(candidates,reviews)
    write_csv(args.output,rows[:args.limit])
    print(json.dumps({"candidates":len(candidates),"previously_reviewed_in_candidate_pool":len(candidates)-len(rows),
                      "remaining":len(rows),"exported":min(args.limit,len(rows)),
                      "output":str(args.output)},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
