#!/usr/bin/env python3
"""Join direct internal callees of the audio API candidate cohort to decompiles."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"

# These brief operation notes are manually checked against the corresponding
# exact-build pseudocode. They describe visible operations, not recovered source
# semantics. Other rows intentionally remain unmapped at this level.
REVIEWED_HELPER_OPERATIONS = {
    "00D16810": "Takes a critical section; selects key modulo 0xC1 bucket; walks linked entries and compares key; increments the matched entry's count field before return; releases lock.",
    "00D27810": "Takes lock at this+0x30; checks helper results/flags; may signal event at this+0x28; releases lock and returns helper-derived integer.",
    "00D13590": "Branches on param_2: when 1, waits indefinitely on handle at param_1[1], closes/clears it, returns *param_1; otherwise closes/clears without waiting and returns param_2.",
    "00D15260": "Bounds a local string copy to 0x104 bytes, truncates at the first period, calls GetIDFromString on the result, then calls FUN_00D27480 and returns the ID.",
    "00A1F950": "Returns literal 0x18.",
    "00D2CB40": "Qualified signature is CAkRegistryMgr::GetObjAndAddref; selects bucket key modulo 0xC1, walks collision nodes, and increments the returned object's field at +0x54.",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decompile", type=Path, default=ROOT / "assets/extracted/audio-api-callee-decompile.txt")
    ap.add_argument("--database", type=Path, default=ROOT / "knowledge/database/callgraph.sqlite")
    ap.add_argument("--triage", type=Path, default=ROOT / "research/executable/evidence/function-triage/internal-function-triage.csv")
    ap.add_argument("--outdir", type=Path, default=ROOT / "research/executable/evidence")
    ap.add_argument("--list-addresses", action="store_true", help="print the direct internal callee addresses and exit")
    args = ap.parse_args()

    triage = {}
    with args.triage.open(encoding="utf-8-sig", newline="") as f:
        triage = {r["address"].upper(): r for r in csv.DictReader(f)}
    candidates = {addr for addr, row in triage.items() if row["subsystem_candidate"] == "audio_middleware_candidate"}
    assert len(candidates) == 181

    conn = sqlite3.connect(args.database)
    meta = dict(conn.execute("SELECT key,value FROM meta"))
    assert meta.get("build_id") == "10256413" and meta.get("exe_sha256") == EXPECTED_SHA, meta
    edges = conn.execute("SELECT from_addr,from_name,to_addr,to_name,site_addr FROM edges WHERE kind='call'").fetchall()
    grouped = defaultdict(list)
    caller_to_target = defaultdict(set)
    for src, src_name, dst, dst_name, site in edges:
        if src.upper() in candidates and not dst.upper().startswith("EXTERNAL:"):
            grouped[dst.upper()].append((src.upper(), src_name, site))
            caller_to_target[src.upper()].add(dst.upper())
    assert len(grouped) == 126 and sum(map(len, grouped.values())) == 401
    if args.list_addresses:
        print("\n".join(sorted(grouped)))
        return

    bodies = {}
    for m in re.finditer(r"@@@ ([0-9A-F]+) (.*?) @@@\s*(.*?)(?=\n@@@ |\Z)", args.decompile.read_text(encoding="utf-8"), re.S | re.I):
        addr, header_name, body = m.groups()
        bodies[addr.upper()] = (header_name, body)
    assert set(grouped) == set(bodies), (len(grouped), len(bodies), set(grouped) - set(bodies), set(bodies) - set(grouped))

    rows = []
    namespace_counts = Counter()
    exact_label_count = 0
    for addr in sorted(grouped):
        header_name, body = bodies[addr]
        assert "DECOMPILE_FAILED=" not in body and "NO_FUNCTION" not in body, addr
        label = triage.get(addr, {}).get("name", header_name)
        header = body.split("\n{", 1)[0]
        qualified = {(f"{owner.rstrip(':')}", method) for owner, method in re.findall(
            r"([A-Za-z_][A-Za-z_0-9]*(?:::[A-Za-z_][A-Za-z_0-9]*)*)::([A-Za-z_][A-Za-z_0-9]*)\s*\(", header)}
        matches = {(owner, method) for owner, method in qualified if method == label}
        assert len(matches) <= 1, (addr, label, matches)
        exact = bool(matches)
        owner = next(iter(matches))[0] if exact else "no_matching_qualified_signature"
        if exact:
            exact_label_count += 1
            namespace_counts[owner] += 1
        t = triage.get(addr, {})
        callers = sorted({src for src, _, _ in grouped[addr]})
        callsites = sorted(f"{src_name}@{site}" for _, src_name, site in grouped[addr])
        rows.append({
            "callee_address": addr,
            "callee_index_name": label,
            "callee_decompiler_name": header_name,
            "callee_qualified_signature_owner": owner,
            "signature_name_matches_index_label": "yes" if exact else "not_observed",
            "triage_candidate": t.get("subsystem_candidate", "unindexed"),
            "name_label_family": t.get("name_label_family", ""),
            "unique_candidate_callers": len(callers),
            "direct_call_edges_from_candidate_cohort": len(grouped[addr]),
            "candidate_callers": "; ".join(f"{src}:{triage.get(src, {}).get('name', '?')}" for src in callers),
            "call_sites": "; ".join(callsites),
            "selected_visible_operation": REVIEWED_HELPER_OPERATIONS.get(addr, ""),
            "decompile_status": "completed",
            "claim_limit": "Exact-build decompiler and indexed direct-call edges only; no runtime reachability or semantics inferred from name alone",
        })

    candidate_bucket_counts = Counter(triage.get(addr, {}).get("subsystem_candidate", "unindexed") for addr in grouped)
    assert exact_label_count == 29, exact_label_count
    assert candidate_bucket_counts == Counter({"unknown": 96, "audio_middleware_candidate": 27,
                                               "runtime_library_candidate": 2,
                                               "runtime_or_object_lifecycle_candidate": 1}), candidate_bucket_counts
    assert sum(1 for src, targets in caller_to_target.items() if "00D21A00" in targets) == 41

    args.outdir.mkdir(parents=True, exist_ok=True)
    csv_path = args.outdir / "EXP-0111-audio-api-direct-callee-cohort.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "build_id": meta["build_id"], "exe_sha256": meta["exe_sha256"], "callgraph_exported_at": meta.get("exported_at"),
        "audio_api_candidate_callers": len(candidates), "indexed_direct_internal_call_edges": 401,
        "distinct_indexed_direct_internal_callees": len(grouped), "callee_decompiles_completed": len(bodies),
        "callee_candidate_bucket_counts": dict(sorted(candidate_bucket_counts.items())),
        "callee_matching_qualified_signature_count": exact_label_count,
        "qualified_signature_owner_counts": dict(sorted(namespace_counts.items())),
        "writer_callers_in_audio_api_cohort": 41,
        "claim_limit": "Static exact-build decompiler/callgraph joins; unresolved targets, indirect calls, semantic ownership, and runtime reachability remain open",
    }
    (args.outdir / "EXP-0111-audio-api-direct-callee-cohort.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
