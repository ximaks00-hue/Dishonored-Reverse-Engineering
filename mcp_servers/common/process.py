"""Locate the configured Dishonored.exe process (read-only)."""

from __future__ import annotations

import os
from typing import Any

import psutil

from mcp_servers.common.config import get_settings
from mcp_servers.common.errors import ToolError


def find_game_process() -> psutil.Process | None:
    settings = get_settings()
    expected = os.path.normcase(str(settings.game_exe)).casefold()
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            actual = proc.info.get("exe")
            if actual and os.path.normcase(actual).casefold() == expected:
                return proc
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            continue
    return None


def require_game_process() -> psutil.Process:
    proc = find_game_process()
    if proc is None:
        settings = get_settings()
        raise ToolError(
            "process_not_running",
            "Configured Dishonored process is not running",
            exe=str(settings.game_exe),
        )
    return proc


def process_snapshot(proc: psutil.Process) -> dict[str, Any]:
    info = proc.as_dict(
        attrs=["pid", "name", "exe", "create_time", "num_threads", "memory_info", "status"]
    )
    mem = info.get("memory_info")
    if mem is not None:
        info["memory_info"] = mem._asdict()
    return info
