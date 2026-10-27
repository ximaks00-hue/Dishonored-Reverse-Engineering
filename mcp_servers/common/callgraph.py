"""Offline call-graph SQLite index (no JVM)."""

from __future__ import annotations

import sqlite3
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from mcp_servers.common.address import format_u32, normalize_function_entry
from mcp_servers.common.config import get_settings
from mcp_servers.common.errors import ToolError

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('call', 'data')),
    from_addr TEXT NOT NULL,
    to_addr TEXT NOT NULL,
    from_name TEXT NOT NULL DEFAULT '',
    to_name TEXT NOT NULL DEFAULT '',
    site_addr TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_addr, kind);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_addr, kind);
"""


def callgraph_path() -> Path:
    return get_settings().callgraph_db


def ensure_schema(path: Path | None = None) -> Path:
    target = path or callgraph_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as db:
        db.executescript(SCHEMA)
        db.commit()
    return target


@contextmanager
def connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    target = path or callgraph_path()
    if not target.is_file():
        raise ToolError(
            "index_missing",
            "Call-graph index is missing. Export it with "
            "research/executable/scripts/ExportCallGraph.java via analyzeHeadless, "
            "or python tools/import_callgraph_csv.py",
            path=str(target),
            build_hint=get_settings().executable_sha256,
        )
    connection = sqlite3.connect(str(target), timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def meta_get(db: sqlite3.Connection, key: str, default: str = "") -> str:
    row = db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def status() -> dict[str, Any]:
    path = callgraph_path()
    if not path.is_file():
        return {
            "available": False,
            "path": str(path),
            "hint": "Run ExportCallGraph.java or tools/import_callgraph_csv.py",
        }
    with connect() as db:
        edge_count = db.execute("SELECT COUNT(*) AS c FROM edges").fetchone()["c"]
        return {
            "available": True,
            "path": str(path),
            "edge_count": edge_count,
            "exe_sha256": meta_get(db, "exe_sha256"),
            "exported_at": meta_get(db, "exported_at"),
        }


def _norm(address: str) -> str:
    return normalize_function_entry(address)


def callers(address: str, *, kind: str = "call", limit: int = 50) -> dict[str, Any]:
    key = _norm(address)
    limit = max(1, min(int(limit), 200))
    with connect() as db:
        rows = db.execute(
            "SELECT from_addr, from_name, to_addr, to_name, site_addr, kind "
            "FROM edges WHERE to_addr = ? AND kind = ? "
            "ORDER BY from_addr LIMIT ?",
            (key, kind, limit),
        ).fetchall()
    return {
        "address": format_u32(int(key, 16)),
        "kind": kind,
        "count": len(rows),
        "items": [dict(row) for row in rows],
    }


def callees(address: str, *, kind: str = "call", limit: int = 50) -> dict[str, Any]:
    key = _norm(address)
    limit = max(1, min(int(limit), 200))
    with connect() as db:
        rows = db.execute(
            "SELECT from_addr, from_name, to_addr, to_name, site_addr, kind "
            "FROM edges WHERE from_addr = ? AND kind = ? "
            "ORDER BY to_addr LIMIT ?",
            (key, kind, limit),
        ).fetchall()
    return {
        "address": format_u32(int(key, 16)),
        "kind": kind,
        "count": len(rows),
        "items": [dict(row) for row in rows],
    }


def xrefs_to(address: str, *, limit: int = 100) -> dict[str, Any]:
    key = _norm(address)
    limit = max(1, min(int(limit), 200))
    with connect() as db:
        rows = db.execute(
            "SELECT from_addr, from_name, to_addr, to_name, site_addr, kind "
            "FROM edges WHERE to_addr = ? ORDER BY kind, from_addr LIMIT ?",
            (key, limit),
        ).fetchall()
    return {
        "address": format_u32(int(key, 16)),
        "count": len(rows),
        "items": [dict(row) for row in rows],
    }


def path(
    start: str,
    goal: str,
    *,
    max_depth: int = 5,
    kind: str = "call",
) -> dict[str, Any]:
    """Bounded BFS on directed call edges from start toward goal."""
    src = _norm(start)
    dst = _norm(goal)
    depth_limit = max(1, min(int(max_depth), 8))
    if src == dst:
        return {
            "found": True,
            "depth": 0,
            "path": [format_u32(int(src, 16))],
            "max_depth": depth_limit,
        }
    with connect() as db:
        frontier: deque[tuple[str, list[str]]] = deque([(src, [src])])
        seen = {src}
        while frontier:
            node, trail = frontier.popleft()
            if len(trail) - 1 > depth_limit:
                continue
            if node == dst and len(trail) > 1:
                return {
                    "found": True,
                    "depth": len(trail) - 1,
                    "path": [format_u32(int(addr, 16)) for addr in trail],
                }
            if len(trail) - 1 >= depth_limit:
                continue
            rows = db.execute(
                "SELECT to_addr FROM edges WHERE from_addr = ? AND kind = ?",
                (node, kind),
            ).fetchall()
            for row in rows:
                nxt = str(row["to_addr"]).upper().zfill(8)
                if nxt in seen:
                    continue
                seen.add(nxt)
                frontier.append((nxt, trail + [nxt]))
    return {
        "found": False,
        "depth": None,
        "path": [],
        "max_depth": depth_limit,
        "start": format_u32(int(src, 16)),
        "goal": format_u32(int(dst, 16)),
    }
