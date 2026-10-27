"""Dishonored Frida MCP — read-only attach, memory read, temporary call traces."""

from __future__ import annotations

import os
import queue
import sys
import threading
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import frida
import psutil
from mcp.server import MCPServer

from mcp_servers.common.address import (
    clamp_size,
    format_u32,
    normalize_function_entry,
    parse_u32_address,
    va_to_rva,
)
from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import FunctionIndex
from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.errors import ToolError
from mcp_servers.common.logging_setup import configure_logging
from mcp_servers.common.process import find_game_process, require_game_process

_log = configure_logging("frida")
_settings = get_settings()
_functions = FunctionIndex()

_lock = threading.RLock()
_trace_events: queue.Queue[dict[str, Any]] = queue.Queue(
    maxsize=_settings.max_trace_queue
)
_session: frida.core.Session | None = None
_script: frida.core.Script | None = None
_attached_pid: int | None = None
_active_traces: set[str] = set()
_trace_names: dict[str, str] = {}

_AGENT = r"""
'use strict';
const listeners = new Map();
rpc.exports = {
  modules() {
    return Process.enumerateModules().map(m => ({
      name: m.name,
      path: m.path,
      base: m.base.toString(),
      size: m.size,
      protection: m.protection
    }));
  },
  read(address, size) {
    const p = ptr(address);
    const range = Process.findRangeByAddress(p);
    if (range === null || !String(range.protection).includes('r')) {
      throw new Error('Address is not in a readable range');
    }
    const bytes = Memory.readByteArray(p, size);
    return Array.from(new Uint8Array(bytes))
      .map(x => x.toString(16).padStart(2, '0'))
      .join(' ');
  },
  readMany(items) {
    return items.map(item => {
      try {
        const hex = rpc.exports.read(item.address, item.size);
        return {status: 'ok', address: item.address, size: item.size, hex: hex};
      } catch (err) {
        return {status: 'read_failed', address: item.address, detail: String(err)};
      }
    });
  },
  trace(address, token) {
    const previous = listeners.get(token);
    if (previous !== undefined) previous.detach();
    const target = ptr(address);
    const listener = Interceptor.attach(target, {
      onEnter() {
        send({
          kind: 'trace',
          token: token,
          address: target.toString(),
          thread_id: Process.getCurrentThreadId(),
          return_address: this.returnAddress.toString()
        });
      }
    });
    listeners.set(token, listener);
    return {token: token, address: target.toString(), status: 'attached'};
  },
  untrace(token) {
    const listener = listeners.get(token);
    if (listener === undefined) return {token: token, status: 'not_found'};
    listener.detach();
    listeners.delete(token);
    return {token: token, status: 'detached'};
  },
  untraceAll() {
    for (const [token, listener] of listeners.entries()) {
      listener.detach();
      listeners.delete(token);
    }
    return {status: 'cleared'};
  }
};
"""


def _message(message: dict[str, Any], _data: bytes | None) -> None:
    if message.get("type") != "send" or not isinstance(message.get("payload"), dict):
        return
    payload = dict(message["payload"])
    token = str(payload.get("token") or "")
    if token:
        payload["function_name"] = _trace_names.get(token, "")
        try:
            payload["function"] = _functions.get(f"0x{token}")
        except ToolError:
            payload["function"] = {
                "address": f"0x{token}",
                "name": payload["function_name"],
            }
    try:
        _trace_events.put_nowait(payload)
    except queue.Full:
        try:
            _trace_events.get_nowait()
            _trace_events.put_nowait(payload)
        except queue.Empty:
            pass


def _clear_session(expected_session: frida.core.Session | None = None) -> None:
    global _session, _script, _attached_pid
    if expected_session is not None and _session is not expected_session:
        return
    _session = None
    _script = None
    _attached_pid = None
    _active_traces.clear()
    _trace_names.clear()


def _ensure_session() -> tuple[psutil.Process, frida.core.Script]:
    global _session, _script, _attached_pid
    proc = require_game_process()
    if _script is not None and _session is not None and _attached_pid == proc.pid:
        return proc, _script
    if _session is not None:
        try:
            _session.detach()
        except frida.InvalidOperationError:
            pass
        _clear_session()
    try:
        device = frida.get_local_device()
        session = device.attach(proc.pid)
    except frida.ProcessNotFoundError as exc:
        raise ToolError("process_not_running", str(exc)) from exc
    except frida.PermissionDeniedError as exc:
        raise ToolError("access_denied", str(exc), pid=proc.pid) from exc
    except frida.Error as exc:
        raise ToolError("frida_attach_failed", str(exc), pid=proc.pid) from exc

    _session = session
    _attached_pid = proc.pid
    session.on("detached", lambda *_args: _clear_session(session))
    script = session.create_script(_AGENT)
    script.on("message", _message)
    script.load()
    _script = script
    _log.info("attached Frida to pid=%s", proc.pid)
    return proc, script


def _main_module(modules: list[dict[str, Any]]) -> dict[str, Any]:
    expected = os.path.normcase(str(_settings.game_exe)).casefold()
    for module in modules:
        if os.path.normcase(module.get("path", "")).casefold() == expected:
            return module
    raise ToolError(
        "module_not_found",
        "Frida could not find the configured Dishonored.exe module",
        exe=str(_settings.game_exe),
    )


def _health_payload() -> dict[str, Any]:
    report = _settings.path_report()
    report["server"] = "dishonored-frida-runtime"
    report["version"] = "2.1.0"
    report["frida_version"] = getattr(frida, "__version__", "unknown")
    report["frida_import_ok"] = True
    proc = find_game_process()
    report["process_running"] = proc is not None
    report["pid"] = proc.pid if proc is not None else None
    with _lock:
        report["attached"] = _script is not None and _session is not None
        report["active_traces"] = sorted(_active_traces)
    report["ready"] = bool(
        report["paths"]["game_exe"]["exists"]
        and report["paths"]["functions_csv"]["exists"]
    )
    return report


@mcp_tool(_log)
def health() -> dict[str, Any]:
    return _health_payload()


@mcp_tool(_log)
def attach_game() -> dict[str, Any]:
    with _lock:
        proc, script = _ensure_session()
        modules = script.exports_sync.modules()
        return {
            "pid": proc.pid,
            "exe": proc.exe(),
            "architecture": "x86",
            "module_count": len(modules),
            "status": "attached",
        }


@mcp_tool(_log)
def enumerate_game_modules() -> list[dict[str, Any]]:
    with _lock:
        _, script = _ensure_session()
        return script.exports_sync.modules()


@mcp_tool(_log)
def read_module_rva(rva: str, size: int = 64) -> dict[str, Any]:
    size = clamp_size(size)
    rva_value = parse_u32_address(rva, field="rva")
    if rva_value >= 0x02000000:
        raise ToolError(
            "invalid_address", "RVA looks too large for this x86 image", rva=rva
        )
    with _lock:
        proc, script = _ensure_session()
        main = _main_module(script.exports_sync.modules())
        runtime = int(main["base"], 16) + rva_value
        address = format_u32(runtime)
        try:
            result = script.exports_sync.read(address, size)
        except frida.Error as exc:
            raise ToolError("read_failed", str(exc), address=address, rva=rva) from exc
        return {
            "pid": proc.pid,
            "module_base": main["base"],
            "rva": format_u32(rva_value),
            "address": address,
            "size": size,
            "hex": result,
        }


@mcp_tool(_log)
def read_game_memory(address: str, size: int = 64) -> dict[str, Any]:
    size = clamp_size(size)
    normalized = format_u32(parse_u32_address(address))
    with _lock:
        proc, script = _ensure_session()
        try:
            result = script.exports_sync.read(normalized, size)
        except frida.Error as exc:
            raise ToolError("read_failed", str(exc), address=normalized) from exc
        return {"pid": proc.pid, "address": normalized, "size": size, "hex": result}


@mcp_tool(_log)
def read_many(reads: list[dict[str, Any]]) -> dict[str, Any]:
    if not reads:
        raise ToolError("invalid_input", "reads must be a non-empty list")
    if len(reads) > _settings.max_batch_reads:
        raise ToolError(
            "invalid_limit",
            f"at most {_settings.max_batch_reads} reads per call",
            count=len(reads),
        )
    with _lock:
        proc, script = _ensure_session()
        main = _main_module(script.exports_sync.modules())
        base = int(main["base"], 16)
        prepared: list[dict[str, Any]] = []
        for entry in reads:
            if not isinstance(entry, dict):
                raise ToolError("invalid_input", "each read must be an object")
            size = clamp_size(int(entry.get("size", 64)))
            if "va" in entry and entry["va"]:
                address = format_u32(parse_u32_address(str(entry["va"])))
            elif "rva" in entry and entry["rva"] is not None:
                rva_value = parse_u32_address(str(entry["rva"]), field="rva")
                address = format_u32(base + rva_value)
            elif "address" in entry:
                address = format_u32(parse_u32_address(str(entry["address"])))
            else:
                raise ToolError(
                    "invalid_input",
                    "each read needs va, rva, or address",
                )
            prepared.append({"address": address, "size": size})
        try:
            results = script.exports_sync.read_many(prepared)
        except frida.Error as exc:
            raise ToolError("read_failed", str(exc)) from exc
        return {
            "pid": proc.pid,
            "module_base": main["base"],
            "count": len(results),
            "items": results,
        }


@mcp_tool(_log)
def trace_game_function(address: str) -> dict[str, Any]:
    function = _functions.get(address)
    token = normalize_function_entry(function["address"])
    rva = va_to_rva(int(token, 16))
    with _lock:
        proc, script = _ensure_session()
        main = _main_module(script.exports_sync.modules())
        runtime_address = format_u32(int(main["base"], 16) + rva)
        try:
            result = script.exports_sync.trace(runtime_address, token)
        except frida.Error as exc:
            raise ToolError(
                "trace_failed", str(exc), address=runtime_address, token=token
            ) from exc
        _active_traces.add(token)
        _trace_names[token] = function.get("name") or ""
        return {
            "pid": proc.pid,
            "function": function,
            "function_name": function.get("name"),
            "runtime_address": runtime_address,
            **result,
        }


@mcp_tool(_log)
def get_trace_events(limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    events: list[dict[str, Any]] = []
    while len(events) < limit:
        try:
            events.append(_trace_events.get_nowait())
        except queue.Empty:
            break
    return events


@mcp_tool(_log)
def untrace_game_function(address: str) -> dict[str, str]:
    function = _functions.get(address)
    with _lock:
        if _script is None:
            return {"address": function["address"], "status": "not_attached"}
        token = normalize_function_entry(function["address"])
        result = _script.exports_sync.untrace(token)
        _active_traces.discard(token)
        _trace_names.pop(token, None)
        return result


@mcp_tool(_log)
def detach_game() -> dict[str, Any]:
    global _session, _script, _attached_pid
    with _lock:
        if _script is None or _session is None:
            return {"status": "not_attached"}
        pid = _attached_pid
        traces_detached = len(_active_traces)
        session = _session
        script = _script
        try:
            script.exports_sync.untraceAll()
        except frida.Error:
            pass
        _session = None
        _script = None
        _attached_pid = None
        _active_traces.clear()
        _trace_names.clear()
    try:
        session.detach()
    except frida.InvalidOperationError:
        pass
    _log.info("detached Frida from pid=%s", pid)
    return {"pid": pid, "traces_detached": traces_detached, "status": "detached"}


def register(
    server: MCPServer,
    *,
    include_health: bool = True,
    read_memory_name: str = "read_game_memory",
) -> None:
    if include_health:
        server.add_tool(
            health, description="Report Frida/EXE readiness without attaching if idle."
        )
    server.add_tool(
        attach_game, description="Attach Frida to the configured Dishonored process."
    )
    server.add_tool(enumerate_game_modules, description="Enumerate modules via Frida.")
    server.add_tool(
        read_module_rva,
        description="Read bytes at image_base+RVA inside the live Dishonored.exe module.",
    )
    server.add_tool(
        read_game_memory,
        name=read_memory_name,
        description="Read up to 4096 bytes from a readable 32-bit VA via Frida.",
    )
    server.add_tool(
        read_many,
        description="Batch-read many RVA/VA targets in one Frida attach (read-only).",
    )
    server.add_tool(
        trace_game_function,
        description="Temporarily Interceptor.attach one Ghidra-indexed function.",
    )
    server.add_tool(
        get_trace_events,
        description="Drain queued events from active temporary traces (includes function names).",
    )
    server.add_tool(
        untrace_game_function,
        description="Detach Interceptor for one traced Ghidra address.",
    )
    server.add_tool(
        detach_game,
        description="Clear all traces and detach Frida from Dishonored.exe.",
    )


def create_server() -> MCPServer:
    mcp = MCPServer(
        name="dishonored-frida-runtime",
        version="2.1.0",
        instructions=(
            "Read-only Frida inspection for the configured Dishonored.exe. "
            "Memory writes, patches, process control, and arbitrary process attachment "
            "are not exposed. Function traces are temporary and must be detached explicitly. "
            f"EXE: {_settings.game_exe}."
        ),
    )
    register(mcp, include_health=True)
    return mcp


server = create_server()


if __name__ == "__main__":
    _log.info("starting dishonored-frida-runtime MCP (stdio)")
    server.run("stdio")
