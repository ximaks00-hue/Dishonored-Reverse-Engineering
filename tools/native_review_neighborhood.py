#!/usr/bin/env python3
"""Export a bounded, provenance-preserving native-function neighborhood.

Call edges control traversal. Data xrefs are attached as context only and never
become traversal edges or semantic claims. No function review level is changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDRESS_RE = re.compile(r"^(?:0x)?([0-9a-fA-F]{1,8})$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalize_address(raw: str) -> str:
    match = ADDRESS_RE.fullmatch(raw.strip())
    if not match:
        raise ValueError(f"invalid 32-bit VA: {raw!r}")
    return f"{int(match.group(1), 16):08X}"


def build_identity(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    build = re.search(r"Build ID:\s*`?(\d+)`?", text, re.IGNORECASE)
    exe = re.search(r"Executable SHA-256:\s*`([0-9a-fA-F]{64})`", text)
    if not build or not exe:
        raise ValueError(f"build identity missing from {path}")
    return build.group(1), exe.group(1).upper()


def function_index(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        address = normalize_address(row["address"])
        if address in result:
            raise ValueError(f"duplicate function address {address}")
        result[address] = {"name": row.get("name", ""), "size": row.get("size", "")}
    if not result:
        raise ValueError("function index is empty")
    return result


def extract_neighborhood(
    callgraph: Path,
    functions: Path,
    build_record: Path,
    anchors: list[str],
    *,
    max_depth: int = 1,
    node_budget: int = 100,
) -> dict:
    if not 0 <= max_depth <= 2:
        raise ValueError("max_depth must be between 0 and 2")
    if not 1 <= node_budget <= 1000:
        raise ValueError("node_budget must be between 1 and 1000")
    build_id, exe_sha = build_identity(build_record)
    index = function_index(functions)
    seeds = list(dict.fromkeys(normalize_address(item) for item in anchors))
    if not seeds:
        raise ValueError("at least one --anchor is required")
    missing = [seed for seed in seeds if seed not in index]
    if missing:
        raise ValueError(f"anchors absent from function index: {', '.join(missing)}")

    db = sqlite3.connect(f"file:{callgraph.resolve().as_posix()}?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        meta = dict(db.execute("SELECT key, value FROM meta"))
        if meta.get("build_id") != build_id or meta.get("exe_sha256", "").upper() != exe_sha:
            raise ValueError("callgraph metadata does not match the registered build")
        columns = {row[1] for row in db.execute("PRAGMA table_info(edges)")}
        required = {"id", "kind", "from_addr", "to_addr", "from_name", "to_name", "site_addr"}
        if not required <= columns:
            raise ValueError("callgraph edges table has an unsupported schema")

        # Edges are loaded in stable database-row order. Traversal uses only
        # indexed function-entry endpoints of direct-call edges.
        all_edges = [dict(row) for row in db.execute(
            "SELECT id, kind, from_addr, to_addr, from_name, to_name, site_addr "
            "FROM edges ORDER BY id"
        )]
    finally:
        db.close()

    graph_sha = sha256(callgraph)
    function_sha = sha256(functions)
    node_depth = {seed: 0 for seed in seeds}
    queue = deque(seeds)
    truncated = False
    while queue:
        source = queue.popleft()
        depth = node_depth[source]
        if depth >= max_depth:
            continue
        for edge in all_edges:
            if edge["kind"] != "call":
                continue
            caller, callee = edge["from_addr"].upper(), edge["to_addr"].upper()
            if source == caller:
                neighbor = callee
            elif source == callee:
                neighbor = caller
            else:
                continue
            if neighbor not in index or neighbor in node_depth:
                continue
            if len(node_depth) >= node_budget:
                truncated = True
                break
            node_depth[neighbor] = depth + 1
            queue.append(neighbor)
        if truncated:
            break

    selected_edges = []
    selected = set(node_depth)
    for edge in all_edges:
        source = edge["from_addr"].upper()
        target = edge["to_addr"].upper()
        # Call edges are limited to included endpoints. Data xrefs are context
        # only: attach an edge when it touches an included indexed function.
        if edge["kind"] == "call":
            keep = source in selected and target in selected
        else:
            keep = (source in selected or target in selected)
        if not keep:
            continue
        selected_edges.append({
            "kind": edge["kind"],
            "from": edge["from_addr"],
            "from_name": edge["from_name"],
            "to": edge["to_addr"],
            "to_name": edge["to_name"],
            "site": edge["site_addr"],
            "source": {
                "callgraph_sha256": graph_sha,
                "edge_row_id": edge["id"],
            },
            "interpretation": "static_reference_only",
        })

    return {
        "schema": "native-review-neighborhood-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "build": {"id": build_id, "exe_sha256": exe_sha},
        "inputs": {
            "callgraph_sha256": graph_sha,
            "callgraph_exported_at": meta.get("exported_at", ""),
            "callgraph_source_csv": Path(meta.get("source_csv", "")).name,
            "function_index_sha256": function_sha,
            "function_index_rows": len(index),
        },
        "query": {"anchors": seeds, "max_call_depth": max_depth, "node_budget": node_budget},
        "nodes": [
            {"address": address, **index[address], "depth": node_depth[address],
             "review_status": "not_changed_by_neighborhood_export"}
            for address in sorted(node_depth, key=lambda item: (node_depth[item], item))
        ],
        "edges": selected_edges,
        "truncated": truncated,
        "limitations": [
            "Call edges are static references from the recorded callgraph export; dynamic reachability is not established.",
            "Data xrefs are contextual records only and are not traversed or interpreted as fields, vtable slots, or dataflow.",
            "Neighbor inclusion does not mean the function body was inspected and does not advance L0-L4 or review status.",
            "The export is bounded to indexed function entries and the requested call depth/node budget; indirect edges may be absent.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchor", action="append", required=True, help="Function VA; repeat for multiple anchors")
    parser.add_argument("--callgraph", type=Path, default=ROOT / "knowledge/database/callgraph.sqlite")
    parser.add_argument("--functions", type=Path, default=ROOT / "research/executable/functions.csv")
    parser.add_argument("--build-record", type=Path, default=ROOT / "research/builds/BUILD-STEAM-10256413/build.md")
    parser.add_argument("--depth", type=int, default=1, choices=range(0, 3))
    parser.add_argument("--node-budget", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = extract_neighborhood(
        args.callgraph.resolve(strict=True), args.functions.resolve(strict=True),
        args.build_record.resolve(strict=True), args.anchor,
        max_depth=args.depth, node_budget=args.node_budget,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"nodes": len(result["nodes"]), "edges": len(result["edges"]),
                      "truncated": result["truncated"], "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
