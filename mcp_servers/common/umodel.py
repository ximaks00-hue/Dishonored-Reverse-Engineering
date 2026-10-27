"""UModel subprocess wrapper with timeouts and bounded output."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import ensure_under
from mcp_servers.common.errors import ToolError

_OUTPUT_CAP = 200_000


def run_umodel(
    package_path: str,
    *options: str,
    timeout: int = 180,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.umodel_exe.is_file():
        raise ToolError(
            "missing_dependency",
            f"UModel executable not found: {settings.umodel_exe}",
            path=str(settings.umodel_exe),
        )
    if not settings.game_root.is_dir():
        raise ToolError(
            "missing_dependency",
            f"Game directory missing: {settings.game_root}",
            path=str(settings.game_root),
        )
    target = ensure_under(settings.game_root, settings.game_root / package_path)
    if not target.is_file() or target.suffix.casefold() != ".upk":
        raise ToolError(
            "package_unavailable",
            f"UPK package path is missing or invalid: {target}",
            package=package_path,
            resolved=str(target),
        )
    timeout = max(10, min(int(timeout), 600))
    args = [
        str(settings.umodel_exe),
        "-game=dis",
        f"-path={target.parent}",
        *options,
        target.name,
    ]
    try:
        completed = subprocess.run(
            args,
            cwd=str(target.parent),
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(
            "timeout",
            f"UModel exceeded {timeout} seconds",
            package=package_path,
            timeout=timeout,
        ) from exc
    except OSError as exc:
        raise ToolError(
            "umodel_launch_failed",
            str(exc),
            path=str(settings.umodel_exe),
        ) from exc

    output = (completed.stdout + completed.stderr)[-_OUTPUT_CAP:]
    return {
        "package": package_path,
        "exit_code": completed.returncode,
        "timed_out": False,
        "output": output,
        "command": args,
    }
