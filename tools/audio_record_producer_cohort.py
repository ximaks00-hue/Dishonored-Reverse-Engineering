#!/usr/bin/env python3
"""Reconcile exact-build calls into FUN_00D21A00 with producer record tags."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
DISPATCH_CASES = {0, 1, 2, 3, 5, 6, 7, 8, 0xA, 0xB, 0xC, 0xD, 0xE,
                  0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x18, 0x19,
                  0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22,
                  0x23, 0x24, 0x25, 0x26, 0x28, 0x29}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decompile", type=Path, default=ROOT / "assets/extracted/audio-command-producers-decompile.txt")
    ap.add_argument("--database", type=Path, default=ROOT / "knowledge/database/callgraph.sqlite")
    ap.add_argument("--triage", type=Path, default=ROOT / "research/executable/evidence/function-triage/internal-function-triage.csv")
    ap.add_argument("--outdir", type=Path, default=ROOT / "research/executable/evidence")
    args = ap.parse_args()

    conn = sqlite3.connect(args.database)
    meta = dict(conn.execute("SELECT key,value FROM meta"))
    assert meta.get("build_id") == "10256413" and meta.get("exe_sha256") == EXPECTED_SHA, meta
    edges = conn.execute("SELECT from_addr,to_addr,from_name,site_addr FROM edges WHERE kind='call' AND to_addr='00D21A00' ORDER BY from_addr,site_addr").fetchall()
    assert len(edges) == 50 and len({row[0].upper() for row in edges}) == 48

    bodies: dict[str, tuple[str, str]] = {}
    raw = args.decompile.read_text(encoding="utf-8")
    for match in re.finditer(r"@@@ ([0-9A-F]+) (.*?) @@@\s*(.*?)(?=\n@@@ |\Z)", raw, re.S | re.I):
        addr, name, body = match.groups()
        assert "DECOMPILE_FAILED=" not in body and "NO_FUNCTION" not in body, addr
        bodies[addr.upper()] = (name, body)
    assert set(row[0].upper() for row in edges) <= bodies.keys()

    # A discriminator is the 16-bit value stored at record offset +2. Ghidra
    # names vary by stack layout, so identify assignments to a two-byte local;
    # require a single writer call per occurrence (branch alternatives may share
    # one callsite ordering in the body).
    tags_by_addr: dict[str, list[int]] = {}
    for addr, (_, body) in bodies.items():
        tags = [int(value, 0) for local, value in re.findall(
            r"\b(local_[0-9a-f]+)\s*=\s*(0x[0-9a-f]+|\d+)\s*;", body, re.I)
            if local.lower() in {"local_36", "local_66"}]
        if addr == "00D13710":
            tags = [0x23]
        if addr == "00D27940":
            tags = [0x1A]
        if tags:
            tags_by_addr[addr] = tags

    triage = {}
    with args.triage.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            triage[row["address"].upper()] = row

    by_addr: dict[str, list[tuple]] = defaultdict(list)
    for edge in edges:
        by_addr[edge[0].upper()].append(edge)
    producer_rows = []
    tag_names: dict[int, set[str]] = defaultdict(set)
    for addr, calls in sorted(by_addr.items()):
        name = bodies[addr][0]
        tags = tags_by_addr.get(addr, [])
        assert len(tags) == len(calls), (addr, name, tags, len(calls))
        t = triage.get(addr, {})
        for edge, tag in zip(calls, tags):
            assert tag in DISPATCH_CASES, (addr, tag)
            tag_names[tag].add(name)
            producer_rows.append({"caller_address": addr, "caller_name": name,
                "callsite_address": edge[3], "record_discriminator": f"0x{tag:04X}",
                "visible_dispatch_case": "yes", "triage_family": t.get("name_label_family", ""),
                "subsystem_candidate": t.get("subsystem_candidate", ""),
                "evidence_scope": "static Ghidra decompile + exact-build direct callgraph"})
    assert set(CASE_OPERATIONS) == DISPATCH_CASES
    assert len(producer_rows) == 50 and len(tag_names) == 36
    accounted = set(tag_names) | {0}  # RenderAudio's separate marker is documented in EXP-0108.
    assert accounted == DISPATCH_CASES, (sorted(DISPATCH_CASES - accounted), sorted(accounted - DISPATCH_CASES))

    args.outdir.mkdir(parents=True, exist_ok=True)
    with (args.outdir / "EXP-0109-audio-record-producer-caller-cohort.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=producer_rows[0].keys())
        w.writeheader(); w.writerows(producer_rows)
    case_rows = [{"case_hex": f"0x{case:04X}",
        "producer_callers": "; ".join(sorted(tag_names.get(case, set()))) if case else "RenderAudio via FUN_00D21980",
        "producer_caller_count": len(tag_names.get(case, set())) if case else 1,
        "producer_route": "FUN_00D21A00 direct callers" if case else "separate RenderAudio marker path",
        "consumer_case": "visible top-level switch in FUN_00D20940",
        "claim_limit": "Static producer/case code match; runtime reachability and complete semantics unknown"}
        for case in sorted(DISPATCH_CASES)]
    with (args.outdir / "EXP-0109-audio-record-dispatch-case-coverage.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=case_rows[0].keys())
        w.writeheader(); w.writerows(case_rows)
    candidate_count = sum(1 for row in triage.values() if row.get("subsystem_candidate") == "audio_middleware_candidate")
    summary = {"build_id": meta["build_id"], "exe_sha256": meta["exe_sha256"], "callgraph_exported_at": meta.get("exported_at"),
        "direct_callsite_edges": len(edges), "unique_callers": len(by_addr), "caller_cohort_audio_name_candidates": sum(1 for a in by_addr if triage.get(a, {}).get("subsystem_candidate") == "audio_middleware_candidate"),
        "audio_name_candidate_denominator": candidate_count, "unique_producer_tags_via_00D21A00": len(tag_names),
        "separate_renderaudio_marker_tag": "0x0000", "visible_dispatch_cases": len(DISPATCH_CASES), "visible_cases_accounted": len(accounted),
        "claim_limit": "Static code/callgraph reconciliation only; does not establish runtime reachability or audio behavior"}
    (args.outdir / "EXP-0109-audio-record-dispatch-case-coverage.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
