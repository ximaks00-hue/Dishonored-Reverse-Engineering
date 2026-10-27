"""Dishonored runtime MCP — read-only live process inspection."""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from mcp_servers.common.address import clamp_size, format_u32, parse_u32_address
from mcp_servers.common.config import get_settings
from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.errors import ToolError
from mcp_servers.common.logging_setup import configure_logging
from mcp_servers.common.process import find_game_process, process_snapshot, require_game_process

_log = configure_logging("runtime")
_settings = get_settings()


def _open_process(pid: int):
    if os.name != "nt":
        raise ToolError("unsupported_platform", "Runtime MCP is Windows-only")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.ReadProcessMemory.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    kernel32.ReadProcessMemory.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.OpenProcess(0x0010 | 0x1000, 0, pid)
    if not handle:
        raise ToolError(
            "access_denied",
            "OpenProcess failed",
            pid=pid,
            winerror=ctypes.get_last_error(),
        )
    return kernel32, handle


def _read_va(kernel32, handle, address_value: int, size: int) -> dict[str, Any]:
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    ok = kernel32.ReadProcessMemory(
        handle,
        ctypes.c_void_p(address_value),
        buffer,
        size,
        ctypes.byref(bytes_read),
    )
    if not ok and bytes_read.value == 0:
        return {
            "status": "read_failed",
            "address": format_u32(address_value),
            "winerror": ctypes.get_last_error(),
        }
    data = buffer.raw[: bytes_read.value]
    return {
        "status": "ok",
        "address": format_u32(address_value),
        "bytes_read": len(data),
        "hex": data.hex(" "),
    }


def _health_payload() -> dict[str, Any]:
    report = _settings.path_report()
    report["server"] = "dishonored-runtime"
    report["version"] = "2.1.0"
    proc = find_game_process()
    report["process_running"] = proc is not None
    report["pid"] = proc.pid if proc is not None else None
    report["ready"] = report["paths"]["game_exe"]["exists"]
    return report


@mcp_tool(_log)
def health() -> dict[str, Any]:
    return _health_payload()


@mcp_tool(_log)
def get_game_process() -> dict[str, Any]:
    proc = find_game_process()
    if proc is None:
        return {
            "status": "not_running",
            "exe": str(_settings.game_exe),
            "detail": "Launch the workspace Dishonored.exe before using runtime tools.",
        }
    info = process_snapshot(proc)
    info["status_code"] = "ok"
    return info


@mcp_tool(_log)
def get_main_module() -> dict[str, Any]:
    proc = find_game_process()
    if proc is None:
        return {"status": "not_running", "exe": str(_settings.game_exe)}
    expected = os.path.normcase(str(_settings.game_exe)).casefold()
    try:
        mappings = proc.memory_maps(grouped=False)
    except OSError as exc:
        return {"status": "access_denied", "detail": str(exc)}
    hits = [
        {"path": m.path, "address_range": m.addr, "rss": m.rss}
        for m in mappings
        if os.path.normcase(m.path).casefold() == expected
    ]
    if not hits:
        return {
            "status": "module_not_mapped",
            "pid": proc.pid,
            "exe": str(_settings.game_exe),
        }
    return {
        "status": "ok",
        "pid": proc.pid,
        "image_base_hint": "0x00400000",
        "mappings": hits,
    }


@mcp_tool(_log)
def get_loaded_modules() -> dict[str, Any]:
    proc = find_game_process()
    if proc is None:
        return {"status": "not_running", "modules": [], "exe": str(_settings.game_exe)}
    try:
        mappings = proc.memory_maps(grouped=True)
    except (OSError, Exception) as exc:
        return {"status": "access_denied", "modules": [], "detail": str(exc)}
    modules = [
        {"path": m.path, "address_range": m.addr, "rss": m.rss}
        for m in mappings
        if m.path.casefold().endswith((".exe", ".dll"))
    ]
    return {"status": "ok", "pid": proc.pid, "modules": modules}


@mcp_tool(_log)
def read_game_memory(address: str, size: int = 64) -> dict[str, Any]:
    proc = require_game_process()
    address_value = parse_u32_address(address)
    size = clamp_size(size)
    kernel32, handle = _open_process(proc.pid)
    try:
        result = _read_va(kernel32, handle, address_value, size)
        result["pid"] = proc.pid
        return result
    finally:
        kernel32.CloseHandle(handle)


@mcp_tool(_log)
def read_game_memory_many(reads: list[dict[str, Any]]) -> dict[str, Any]:
    if not reads:
        raise ToolError("invalid_input", "reads must be a non-empty list")
    if len(reads) > _settings.max_batch_reads:
        raise ToolError(
            "invalid_limit",
            f"at most {_settings.max_batch_reads} reads per call",
            count=len(reads),
        )
    proc = require_game_process()
    kernel32, handle = _open_process(proc.pid)
    items: list[dict[str, Any]] = []
    try:
        for entry in reads:
            if not isinstance(entry, dict) or "address" not in entry:
                items.append({"status": "invalid_input", "detail": "each item needs address"})
                continue
            size = clamp_size(int(entry.get("size", 64)))
            address_value = parse_u32_address(str(entry["address"]))
            items.append(_read_va(kernel32, handle, address_value, size))
    finally:
        kernel32.CloseHandle(handle)
    return {"status": "ok", "pid": proc.pid, "count": len(items), "items": items}


def register(server: MCPServer, *, include_health: bool = True) -> None:
    if include_health:
        server.add_tool(
            health, description="Report EXE readiness and whether the process is running."
        )
    server.add_tool(
        get_game_process, description="Return process stats, or status=not_running if absent."
    )
    server.add_tool(
        get_main_module,
        description="Base address and size of the configured Dishonored.exe mapping.",
    )
    server.add_tool(
        get_loaded_modules, description="List .exe/.dll mappings in the configured process."
    )
    server.add_tool(
        read_game_memory, description="Read up to 4096 bytes at a 32-bit VA; never writes."
    )
    server.add_tool(
        read_game_memory_many,
        description="Batch-read multiple VAs with one OpenProcess handle (read-only).",
    )


def create_server() -> MCPServer:
    mcp = MCPServer(
        name="dishonored-runtime",
        version="2.1.0",
        instructions=(
            "Read-only inspection of the exact configured Dishonored.exe process. "
            "No write, patch, suspend, or terminate operations are exposed. "
            f"EXE: {_settings.game_exe}."
        ),
    )
    register(mcp, include_health=True)
    return mcp


server = create_server()


if __name__ == "__main__":
    _log.info("starting dishonored-runtime MCP (stdio)")
    server.run("stdio")
