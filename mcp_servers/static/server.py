"""Dishonored static MCP — offline Ghidra function index + headless decompile."""

from __future__ import annotations

import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from mcp_servers.common import decompile_cache
from mcp_servers.common.address import clamp_limit
from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import FunctionIndex
from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.errors import ToolError
from mcp_servers.common.logging_setup import configure_logging

_log = configure_logging("static")
_settings = get_settings()
_functions = FunctionIndex()
_RUN_LOCK = threading.Lock()
_SCRIPT_DIR = (_settings.root / "research" / "executable" / "scripts").resolve()
_DECOMPILE_RE = re.compile(
    r"INFO\s+DecompileFunction\.java>\s*\n(.*?)(?:\n\s*\(GhidraScript\))",
    re.DOTALL,
)


def _health_payload() -> dict[str, Any]:
    report = _settings.path_report()
    report["server"] = "dishonored-static-analysis"
    report["version"] = "2.1.0"
    report["project_name"] = _settings.ghidra_project_name
    report["program"] = _settings.ghidra_program
    try:
        report["function_index_rows"] = len(_functions.all())
    except ToolError as exc:
        report["function_index_rows"] = 0
        report["index_error"] = exc.to_dict()["error"]
    report["ready"] = all(
        report["paths"][key]["exists"] for key in ("functions_csv", "ghidra_project")
    )
    report["headless_ready"] = report["paths"]["ghidra_headless"]["exists"]
    report["decompile_cache_dir"] = str(_settings.decompile_cache_dir)
    return report


@mcp_tool(_log)
def health() -> dict[str, Any]:
    return _health_payload()


@mcp_tool(_log)
def list_functions(query: str = "", limit: int = 50, offset: int = 0) -> dict[str, Any]:
    limit = clamp_limit(limit)
    offset = max(0, offset)
    total, items = _functions.search(query, limit=limit, offset=offset)
    return {"total": total, "offset": offset, "limit": limit, "items": items}


@mcp_tool(_log)
def get_function(address: str) -> dict[str, str]:
    return _functions.get(address)


@mcp_tool(_log)
def get_functions(addresses: list[str]) -> dict[str, Any]:
    if not addresses:
        raise ToolError("invalid_input", "addresses must be a non-empty list")
    if len(addresses) > 64:
        raise ToolError(
            "invalid_limit", "at most 64 addresses per call", count=len(addresses)
        )
    return _functions.get_many(addresses)


@mcp_tool(_log)
def function_at(address: str) -> dict[str, str]:
    return _functions.containing(address)


@mcp_tool(_log)
def functions_in_range(start: str, end: str, limit: int = 50) -> dict[str, Any]:
    limit = clamp_limit(limit)
    items = _functions.in_range(start, end, limit=limit)
    return {"start": start, "end": end, "count": len(items), "items": items}


@mcp_tool(_log)
def decompile_function(address: str, timeout_seconds: int = 90) -> dict[str, Any]:
    function = _functions.get(address)
    cache_key = decompile_cache.cache_key(function["address"], _settings)
    cached = decompile_cache.load(function["address"], expected_cache_key=cache_key)
    if cached is not None:
        return {
            "address": function["address"],
            "name": function["name"],
            "signature": function.get("signature", "") or cached.get("signature", ""),
            "pseudocode": cached["pseudocode"],
            "cache_hit": True,
            "cache_stored": True,
            "cache_path": cached.get("cache_path"),
        }
    if not _settings.ghidra_headless.is_file():
        raise ToolError(
            "missing_dependency",
            f"Ghidra headless launcher not found: {_settings.ghidra_headless}",
            path=str(_settings.ghidra_headless),
        )
    if not _settings.ghidra_project.exists():
        raise ToolError(
            "missing_dependency",
            f"Ghidra project directory missing: {_settings.ghidra_project}",
            path=str(_settings.ghidra_project),
        )
    if not _SCRIPT_DIR.is_dir():
        raise ToolError(
            "missing_dependency",
            f"Ghidra script directory missing: {_SCRIPT_DIR}",
            path=str(_SCRIPT_DIR),
        )
    timeout_seconds = max(20, min(int(timeout_seconds), 180))
    command = [
        str(_settings.ghidra_headless),
        str(_settings.ghidra_project),
        _settings.ghidra_project_name,
        "-process",
        _settings.ghidra_program,
        *decompile_cache.HEADLESS_OPTIONS,
        "-scriptPath",
        str(_SCRIPT_DIR),
        "-postScript",
        "DecompileFunction.java",
        function["address"],
    ]
    with _RUN_LOCK:
        try:
            completed = subprocess.run(
                command,
                cwd=str(_settings.root),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
        except OSError as exc:
            raise ToolError("ghidra_launch_failed", str(exc)) from exc
        except subprocess.TimeoutExpired as exc:
            raise ToolError(
                "timeout",
                f"Ghidra decompilation exceeded {timeout_seconds} seconds",
                address=function["address"],
            ) from exc
    output = (completed.stdout + completed.stderr)[-120_000:]
    match = _DECOMPILE_RE.search(output)
    if completed.returncode != 0 or not match:
        return {
            "address": function["address"],
            "name": function["name"],
            "signature": function.get("signature", ""),
            "exit_code": completed.returncode,
            "error": output[-8_000:],
            "cache_hit": False,
        }
    record = decompile_cache.store(
        function["address"],
        {
            "address": function["address"],
            "name": function["name"],
            "signature": function.get("signature", ""),
            "pseudocode": match.group(1).strip(),
        },
        expected_cache_key=cache_key,
    )
    return {
        "address": function["address"],
        "name": function["name"],
        "signature": function.get("signature", ""),
        "pseudocode": record["pseudocode"],
        "cache_hit": False,
        "cache_stored": record.get("cache_stored", False),
        "cache_path": record.get("cache_path"),
    }


def register(server: MCPServer, *, include_health: bool = True) -> None:
    if include_health:
        server.add_tool(health, description="Report Ghidra project/index readiness.")
    server.add_tool(
        list_functions,
        description="Search indexed functions by address, name, or signature.",
    )
    server.add_tool(
        get_function, description="Return one function index row by virtual address."
    )
    server.add_tool(
        get_functions,
        description="Resolve many function addresses. Missing entries are listed, not fatal.",
    )
    server.add_tool(
        function_at,
        description="Function whose body range contains the given virtual address.",
    )
    server.add_tool(
        functions_in_range,
        description="Function entries whose VA lies in [start, end], inclusive.",
    )
    server.add_tool(
        decompile_function,
        description="Decompile one indexed function (disk cache, then headless Ghidra).",
    )


def create_server() -> MCPServer:
    mcp = MCPServer(
        name="dishonored-static-analysis",
        version="2.1.0",
        instructions=(
            "Search the persisted Ghidra function index and decompile selected functions "
            "via analyzeHeadless -noanalysis -readOnly. Prefer the gateway for agent packs "
            "and callgraph; use interactive ghidra-re-mcp for live DB writes."
        ),
    )
    register(mcp, include_health=True)
    return mcp


server = create_server()


if __name__ == "__main__":
    _log.info("starting dishonored-static-analysis MCP (stdio)")
    server.run("stdio")
