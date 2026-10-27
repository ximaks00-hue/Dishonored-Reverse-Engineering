"""Unified Dishonored MCP gateway — one process, shared indexes, agent packs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from mcp_servers.assets import server as assets_mod
from mcp_servers.common import callgraph
from mcp_servers.common.config import get_settings
from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.logging_setup import configure_logging
from mcp_servers.frida_runtime import server as frida_mod
from mcp_servers.knowledge import server as knowledge_mod
from mcp_servers.runtime import server as runtime_mod
from mcp_servers.static import server as static_mod

_log = configure_logging("gateway")
_settings = get_settings()

server = MCPServer(
    name="dishonored-gateway",
    version="1.0.0",
    instructions=(
        "Single Dishonored research gateway. Call brief / function_dossier / experiment / "
        "get_function / callers first. Local indexes answer in milliseconds; decompile and "
        "UModel use disk caches. Live ghidra-re-mcp remains for DB writes/renames. "
        "Never promote inferred claims to confirmed."
    ),
)


@server.tool(description="Aggregated readiness for indexes, caches, and live process.")
@mcp_tool(_log)
def health() -> dict[str, Any]:
    report = _settings.path_report()
    report["server"] = "dishonored-gateway"
    report["version"] = "1.0.0"
    report["modules"] = {
        "static": static_mod._health_payload(),
        "assets": assets_mod._health_payload(),
        "knowledge": knowledge_mod._health_payload(),
        "runtime": runtime_mod._health_payload(),
        "frida": frida_mod._health_payload(),
    }
    report["callgraph"] = callgraph.status()
    report["ready"] = all(
        report["paths"][key]["exists"]
        for key in ("functions_csv", "packages_index", "schema_sql")
    )
    return report


@server.tool(description="Offline call-graph: who calls this address (index only, no JVM).")
@mcp_tool(_log)
def callers(address: str, kind: str = "call", limit: int = 50) -> dict[str, Any]:
    return callgraph.callers(address, kind=kind, limit=limit)


@server.tool(description="Offline call-graph: what this address calls (index only, no JVM).")
@mcp_tool(_log)
def callees(address: str, kind: str = "call", limit: int = 50) -> dict[str, Any]:
    return callgraph.callees(address, kind=kind, limit=limit)


@server.tool(description="Offline xrefs to an address (call + data edges).")
@mcp_tool(_log)
def xrefs_to(address: str, limit: int = 100) -> dict[str, Any]:
    return callgraph.xrefs_to(address, limit=limit)


@server.tool(description="Bounded BFS path on the offline call graph (max_depth 1–8).")
@mcp_tool(_log)
def path(
    start: str, goal: str, max_depth: int = 5, kind: str = "call"
) -> dict[str, Any]:
    return callgraph.path(start, goal, max_depth=max_depth, kind=kind)


@server.tool(description="Call-graph index status (available / edge_count / build hash).")
@mcp_tool(_log)
def callgraph_status() -> dict[str, Any]:
    return callgraph.status()


# Register domain tools once; skip per-module health; avoid Frida/runtime memory name clash.
static_mod.register(server, include_health=False)
assets_mod.register(server, include_health=False)
knowledge_mod.register(server, include_health=False)
runtime_mod.register(server, include_health=False)
frida_mod.register(
    server,
    include_health=False,
    read_memory_name="frida_read_game_memory",
)


if __name__ == "__main__":
    _log.info("starting dishonored-gateway MCP (stdio)")
    server.run("stdio")
