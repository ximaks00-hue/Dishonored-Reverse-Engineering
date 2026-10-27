#!/usr/bin/env python3
"""Summarize exact-build decompiles and callgraph rows for audio API name candidates."""

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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decompile", type=Path, default=ROOT / "assets/extracted/audio-api-candidate-decompile.txt")
    ap.add_argument("--database", type=Path, default=ROOT / "knowledge/database/callgraph.sqlite")
    ap.add_argument("--triage", type=Path, default=ROOT / "research/executable/evidence/function-triage/internal-function-triage.csv")
    ap.add_argument("--outdir", type=Path, default=ROOT / "research/executable/evidence")
    args = ap.parse_args()

    candidates = {}
    with args.triage.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["subsystem_candidate"] == "audio_middleware_candidate":
                candidates[row["address"].upper()] = row
    assert len(candidates) == 181

    bodies = {}
    source = args.decompile.read_text(encoding="utf-8")
    for match in re.finditer(r"@@@ ([0-9A-F]+) (.*?) @@@\s*(.*?)(?=\n@@@ |\Z)", source, re.S | re.I):
        addr, header_name, body = match.groups()
        bodies[addr.upper()] = (header_name, body)
    assert set(candidates) == set(bodies), (len(candidates), len(bodies), set(candidates) - set(bodies), set(bodies) - set(candidates))
    for addr, (name, body) in bodies.items():
        assert "DECOMPILE_FAILED=" not in body and "NO_FUNCTION" not in body, (addr, name)

    conn = sqlite3.connect(args.database)
    meta = dict(conn.execute("SELECT key,value FROM meta"))
    assert meta.get("build_id") == "10256413" and meta.get("exe_sha256") == EXPECTED_SHA, meta
    all_edges = conn.execute("SELECT from_addr,to_addr,to_name,site_addr FROM edges WHERE kind='call'").fetchall()
    outgoing: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for src, dst, dst_name, site in all_edges:
        if src.upper() in candidates:
            outgoing[src.upper()].append((dst, dst_name, site))

    rows = []
    namespaces = Counter()
    for addr in sorted(candidates):
        triage = candidates[addr]
        header_name, body = bodies[addr]
        name = triage["name"]
        header = body.split("\n{", 1)[0]
        signatures = {(f"AK::{namespace.rstrip(':')}", function)
                      for namespace, function in re.findall(
                          r"AK::((?:[A-Za-z_][A-Za-z_0-9]*::)*)([A-Za-z_][A-Za-z_0-9]*)\s*\(", header)}
        matches = {(namespace, function) for namespace, function in signatures if function == name}
        assert matches, (addr, name, signatures)
        # Multiple declarations can appear in Ghidra's comment and prototype; they
        # must agree on the namespace/function pair for this indexed address.
        assert len(matches) == 1, (addr, name, matches)
        namespace, signature_name = next(iter(matches))
        exact = signature_name == name
        namespaces[namespace] += 1
        edges = sorted(outgoing.get(addr, []), key=lambda e: (e[2], e[0]))
        internal = [e for e in edges if not e[0].upper().startswith("EXTERNAL:")]
        external = [e for e in edges if e[0].upper().startswith("EXTERNAL:")]
        writer = [e for e in edges if e[0].upper() == "00D21A00"]
        rows.append({
            "address": addr,
            "indexed_name": name,
            "decompiler_function_name": header_name,
            "decompiler_namespace": namespace,
            "signature_name_matches_index_label": "yes" if exact else "no_or_unresolved",
            "decompile_status": "completed",
            "indexed_direct_call_edges": len(edges),
            "unique_internal_callees": len({e[0].upper() for e in internal}),
            "external_call_edges": len(external),
            "FUN_00D21A00_call_edges": len(writer),
            "direct_callee_names": "; ".join(f"{e[1]}@{e[2]}" for e in edges),
            "claim_limit": "Exact-build decompiler metadata and static direct-call index only; no runtime reachability claim",
        })

    writer_rows = [r for r in rows if int(r["FUN_00D21A00_call_edges"]) > 0]
    assert len(rows) == 181 and len(writer_rows) == 41
    assert sum(int(r["FUN_00D21A00_call_edges"]) for r in rows) == 43
    assert namespaces == {"AK::SoundEngine": 105, "AK::SoundEngine::Query": 30,
                          "AK::MemoryMgr": 17, "AK::StreamMgr": 12,
                          "AK::SoundEngine::DynamicSequence": 6,
                          "AK::MotionEngine": 5, "AK::SoundEngine::DynamicDialogue": 3,
                          "AK::MusicEngine": 3}, namespaces

    args.outdir.mkdir(parents=True, exist_ok=True)
    csv_path = args.outdir / "EXP-0110-audio-api-candidate-cohort.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "build_id": meta["build_id"], "exe_sha256": meta["exe_sha256"], "callgraph_exported_at": meta.get("exported_at"),
        "candidate_count": len(candidates), "decompiles_completed": len(rows),
        "decompiler_namespace_counts": dict(sorted(namespaces.items())),
        "exact_index_label_signature_matches": sum(r["signature_name_matches_index_label"] == "yes" for r in rows),
        "direct_call_edges_into_FUN_00D21A00": sum(int(r["FUN_00D21A00_call_edges"]) for r in rows),
        "unique_FUN_00D21A00_callers_in_cohort": len(writer_rows),
        "static_claim_limit": "Names/signatures and direct callgraph relationships only; not proof of vendor provenance, complete ownership, indirect calls, or runtime use",
    }
    json_path = args.outdir / "EXP-0110-audio-api-candidate-cohort.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
