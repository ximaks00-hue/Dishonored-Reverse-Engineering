"""Disk cache for headless Ghidra decompilation results."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from mcp_servers.common.address import normalize_function_entry
from mcp_servers.common.config import get_settings


def _cache_dir() -> Path:
    path = get_settings().decompile_cache_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(address: str) -> Path:
    key = normalize_function_entry(address)
    return _cache_dir() / f"{key}.json"


def load(address: str) -> dict[str, Any] | None:
    settings = get_settings()
    path = cache_path(address)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("exe_sha256") != settings.executable_sha256:
        return None
    if payload.get("build_id") != settings.build_id:
        return None
    if not payload.get("pseudocode"):
        return None
    payload["cache_hit"] = True
    payload["cache_path"] = str(path)
    return payload


def store(address: str, record: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    key = normalize_function_entry(address)
    path = cache_path(address)
    payload = {
        "address": record.get("address") or f"0x{key}",
        "name": record.get("name", ""),
        "signature": record.get("signature", ""),
        "pseudocode": record.get("pseudocode", ""),
        "exe_sha256": settings.executable_sha256,
        "build_id": settings.build_id,
        "cached_at": time.time(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["cache_hit"] = False
    payload["cache_path"] = str(path)
    return payload
