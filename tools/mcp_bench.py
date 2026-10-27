#!/usr/bin/env python3
"""Warm-process latency bench for gateway index tools (p50)."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_servers.common import agent_packs, callgraph, package_cache
from mcp_servers.common.csv_index import FunctionIndex
from mcp_servers.common.errors import ToolError


def _p50(samples: list[float]) -> float:
    return statistics.median(samples)


def _bench(name: str, fn, rounds: int = 21) -> dict:
    times: list[float] = []
    error = None
    # Warmup
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    for _ in range(rounds):
        started = time.perf_counter()
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            break
        times.append((time.perf_counter() - started) * 1000)
    if error:
        return {"name": name, "ok": False, "error": error}
    return {
        "name": name,
        "ok": True,
        "p50_ms": round(_p50(times), 3),
        "p95_ms": round(sorted(times)[max(0, int(len(times) * 0.95) - 1)], 3),
        "n": len(times),
    }


def main() -> int:
    index = FunctionIndex()
    # Prefer a known Blink-related address if present; else first row.
    probe = "0x00BFC990"
    try:
        index.get(probe)
    except ToolError:
        rows = index.all()
        probe = rows[0]["address"] if rows else "0x00401000"

    jobs = [
        ("get_function", lambda: index.get(probe)),
        ("brief_blink", lambda: agent_packs.brief("blink")),
        ("search_objects", lambda: package_cache.search_objects("Blink", limit=20)),
    ]

    def callers_job():
        try:
            return callgraph.callers(probe, limit=20)
        except ToolError as exc:
            if exc.code == "index_missing":
                return {"available": False}
            raise

    jobs.insert(1, ("callers", callers_job))

    results = [_bench(name, fn) for name, fn in jobs]
    print("mcp_bench (warm process)")
    for row in results:
        if row["ok"]:
            # callers may no-op when the offline graph is not exported yet
            if row["name"] == "callers" and not callgraph.status().get("available"):
                print(f"  {row['name']}: SKIP index_missing")
                continue
            flag = "OK" if row["p50_ms"] < 50 else "SLOW"
            print(f"  {row['name']}: p50={row['p50_ms']}ms p95={row['p95_ms']}ms [{flag}]")
        else:
            print(f"  {row['name']}: FAIL {row['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
