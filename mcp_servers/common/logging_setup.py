"""Consistent logging for MCP stdio servers (stderr only — stdout is MCP)."""

from __future__ import annotations

import logging
import os
import sys


def configure_logging(server_name: str, level: str | None = None) -> logging.Logger:
    resolved = (level or os.environ.get("DISHONORED_MCP_LOG", "INFO")).upper()
    logger = logging.getLogger(f"dishonored.mcp.{server_name}")
    if logger.handlers:
        logger.setLevel(resolved)
        return logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(resolved)
    logger.propagate = False
    return logger
