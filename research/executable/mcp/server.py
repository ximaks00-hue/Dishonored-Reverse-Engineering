"""Compatibility launcher for the canonical static MCP server.

Prefer `mcp_servers/static/server.py`. This path remains for older configs.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_CANONICAL = Path(__file__).resolve().parents[3] / "mcp_servers" / "static" / "server.py"

if __name__ == "__main__":
    sys.argv[0] = str(_CANONICAL)
    runpy.run_path(str(_CANONICAL), run_name="__main__")
else:
    raise ImportError(
        "Import mcp_servers.static.server instead of research.executable.mcp.server"
    )
