#!/usr/bin/env python3
"""Smoke-test Dishonored MCP server modules without a live MCP host."""

from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def unwrap(result: Any) -> Any:
    if isinstance(result, dict) and result.get("ok") is True and "data" in result:
        return result["data"]
    if isinstance(result, dict) and result.get("ok") is False:
        err = result.get("error") or {}
        raise RuntimeError(f"{err.get('code')}: {err.get('message')}")
    return result


def check(name: str, fn):
    try:
        result = unwrap(fn())
        kind = type(result).__name__
        print(f"OK  {name}: {kind}")
        return result
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        traceback.print_exc(limit=3)
        return None


def main() -> int:
    failures = 0
    gateway = importlib.import_module("mcp_servers.gateway.server")
    assets = importlib.import_module("mcp_servers.assets.server")
    knowledge = importlib.import_module("mcp_servers.knowledge.server")
    runtime = importlib.import_module("mcp_servers.runtime.server")
    static = importlib.import_module("mcp_servers.static.server")
    frida_rt = importlib.import_module("mcp_servers.frida_runtime.server")

    for label, fn in (
        ("gateway.health", gateway.health),
        ("assets.health", assets.health),
        ("knowledge.health", knowledge.health),
        ("runtime.health", runtime.health),
        ("static.health", static.health),
        ("frida.health", frida_rt.health),
    ):
        result = check(label, fn)
        if result is None:
            failures += 1
        elif isinstance(result, dict) and result.get("ready") is False:
            print(f"WARN {label}: ready=false")

    pkgs = check(
        "assets.list_packages(DishonoredGame)",
        lambda: assets.list_packages("DishonoredGame", 5),
    )
    if not pkgs:
        failures += 1

    info = check(
        "assets.get_package_info(DishonoredGame.upk)",
        lambda: assets.get_package_info("DishonoredGame.upk"),
    )
    parsed = (info or {}).get("parsed") or {}
    if parsed.get("ue_version") != "801/30" or parsed.get("exports") != 30049:
        print(f"WARN package_info parsed={parsed}")
        failures += 1

    edges = check("knowledge.list_evidence_edges", knowledge.list_evidence_edges)
    if edges is None or len(edges) < 10:
        failures += 1

    brief = check("knowledge.brief(blink)", lambda: knowledge.brief("blink"))
    if brief is None or "edges" not in brief:
        failures += 1

    funcs = check(
        "static.list_functions(BFC990)", lambda: static.list_functions("BFC990", 5)
    )
    if not funcs or funcs.get("total", 0) < 1:
        failures += 1

    proc = check("runtime.get_game_process", runtime.get_game_process)
    if not isinstance(proc, dict):
        failures += 1
    else:
        print(f"     process={proc.get('status') or proc.get('status_code')}")

    cg = check("gateway.callgraph_status", gateway.callgraph_status)
    if cg is None:
        failures += 1
    else:
        print(f"     callgraph.available={cg.get('available')}")

    print("---")
    print("PASS" if failures == 0 else f"FAILURES={failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
