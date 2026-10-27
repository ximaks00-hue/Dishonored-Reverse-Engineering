"""SQLite cache of UModel package object listings."""

from __future__ import annotations

import json
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import ensure_under
from mcp_servers.common.errors import ToolError
from mcp_servers.common.pkginfo import parse_pkginfo
from mcp_servers.common.umodel import run_umodel

SCHEMA = """
CREATE TABLE IF NOT EXISTS packages (
    package TEXT PRIMARY KEY,
    relative_path TEXT NOT NULL DEFAULT '',
    mtime_ns INTEGER NOT NULL DEFAULT 0,
    length INTEGER NOT NULL DEFAULT 0,
    sha256 TEXT NOT NULL DEFAULT '',
    parsed_json TEXT NOT NULL DEFAULT '{}',
    refreshed_at REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS objects (
    id INTEGER PRIMARY KEY,
    package TEXT NOT NULL,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL DEFAULT '',
    UNIQUE(package, name)
);
CREATE INDEX IF NOT EXISTS idx_objects_name ON objects(name);
CREATE INDEX IF NOT EXISTS idx_objects_package ON objects(package);
"""

_OBJECT_LINE = re.compile(
    r"^\s*(?:\d+\s+)?(?P<class>[A-Za-z_][\w.]*)\s+(?P<name>[\w./]+)\s*$"
)


def db_path() -> Path:
    return get_settings().package_cache_db


def object_catalog_path() -> Path:
    return get_settings().root / "knowledge" / "database" / "umodel-package-objects.sqlite"


def has_object_catalog() -> bool:
    return object_catalog_path().is_file()


def _package_key(relative_path: str) -> str:
    return relative_path.replace("\\", "/").casefold()


def get_catalog_package(relative_path: str) -> dict[str, Any] | None:
    catalog = object_catalog_path()
    if not catalog.is_file():
        return None
    with sqlite3.connect(str(catalog)) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT p.*, COUNT(o.export_index) AS object_count "
            "FROM packages AS p LEFT JOIN objects AS o "
            "ON o.relative_path = p.relative_path "
            "WHERE p.relative_path = ? COLLATE NOCASE "
            "GROUP BY p.relative_path",
            (relative_path.replace("\\", "/"),),
        ).fetchone()
    return dict(row) if row is not None else None


def list_catalog_objects(relative_path: str, *, limit: int = 200) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    catalog = object_catalog_path()
    if not catalog.is_file():
        return []
    with sqlite3.connect(str(catalog)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT export_index, package_offset, export_size, "
            "object_class AS class, object_name AS name "
            "FROM objects WHERE relative_path = ? COLLATE NOCASE "
            "ORDER BY export_index LIMIT ?",
            (relative_path.replace("\\", "/"), limit),
        ).fetchall()
    return [dict(row) for row in rows]


def ensure_schema() -> Path:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.commit()
    return path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    ensure_schema()
    connection = sqlite3.connect(str(db_path()), timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def parse_object_list(output: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for line in output.splitlines():
        match = _OBJECT_LINE.match(line.strip())
        if not match:
            continue
        class_name = match.group("class")
        name = match.group("name")
        if class_name.lower() in {"loading", "found", "scanned", "export"}:
            continue
        items.append({"class": class_name, "name": name})
    return items


def _package_file(relative_path: str) -> Path:
    settings = get_settings()
    return ensure_under(settings.game_root, settings.game_root / relative_path)


def refresh_package(package_filename: str, relative_path: str) -> dict[str, Any]:
    target = _package_file(relative_path)
    if not target.is_file():
        raise ToolError("package_unavailable", f"Missing package file: {target}")
    stat = target.stat()
    list_result = run_umodel(relative_path, "-list", timeout=240)
    info_result = run_umodel(relative_path, "-pkginfo", timeout=180)
    objects = parse_object_list(str(list_result.get("output", "")))
    parsed = parse_pkginfo(str(info_result.get("output", "")))
    key = _package_key(relative_path)
    with connect() as db:
        db.execute(
            "INSERT INTO packages(package, relative_path, mtime_ns, length, sha256, parsed_json, refreshed_at) "
            "VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(package) DO UPDATE SET relative_path=excluded.relative_path, "
            "mtime_ns=excluded.mtime_ns, length=excluded.length, parsed_json=excluded.parsed_json, "
            "refreshed_at=excluded.refreshed_at",
            (
                key,
                relative_path,
                stat.st_mtime_ns,
                stat.st_size,
                "",
                json.dumps(parsed),
                time.time(),
            ),
        )
        db.execute("DELETE FROM objects WHERE package = ?", (key,))
        db.executemany(
            "INSERT OR IGNORE INTO objects(package, name, class_name) VALUES(?,?,?)",
            [(key, item["name"], item["class"]) for item in objects],
        )
    return {
        "package": relative_path,
        "object_count": len(objects),
        "parsed": parsed,
        "refreshed": True,
        "cache_hit": False,
        "list_exit_code": list_result.get("exit_code"),
        "info_exit_code": info_result.get("exit_code"),
    }


def ensure_package(package_filename: str, relative_path: str) -> dict[str, Any]:
    target = _package_file(relative_path)
    if not target.is_file():
        raise ToolError("package_unavailable", f"Missing package file: {target}")
    mtime_ns = target.stat().st_mtime_ns
    key = _package_key(relative_path)
    with connect() as db:
        row = db.execute(
            "SELECT mtime_ns, parsed_json FROM packages WHERE package = ?",
            (key,),
        ).fetchone()
        if row is not None and int(row["mtime_ns"]) == mtime_ns:
            count = db.execute(
                "SELECT COUNT(*) AS c FROM objects WHERE package = ?",
                (key,),
            ).fetchone()["c"]
            try:
                parsed = json.loads(row["parsed_json"] or "{}")
            except json.JSONDecodeError:
                parsed = {"parsed": False}
            return {
                "package": relative_path,
                "object_count": count,
                "parsed": parsed,
                "refreshed": False,
                "cache_hit": True,
            }
    return refresh_package(package_filename, relative_path)


def list_cached_objects(package_filename: str, *, limit: int = 200) -> list[dict[str, str]]:
    limit = max(1, min(int(limit), 500))
    with connect() as db:
        rows = db.execute(
            "SELECT name, class_name AS class FROM objects WHERE package = ? "
            "ORDER BY name LIMIT ?",
            (_package_key(package_filename), limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_cached_parsed(package_filename: str) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute(
            "SELECT parsed_json FROM packages WHERE package = ?",
            (_package_key(package_filename),),
        ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["parsed_json"] or "{}")
    except json.JSONDecodeError:
        return None


def search_objects(query: str, *, limit: int = 50) -> list[dict[str, str]]:
    if not query.strip():
        raise ToolError("invalid_query", "query must be non-empty")
    limit = max(1, min(int(limit), 200))
    pattern = f"%{query}%"
    catalog = object_catalog_path()
    if catalog.is_file():
        with sqlite3.connect(str(catalog)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT relative_path AS package, object_name AS name, "
                "object_class AS class, export_index "
                "FROM objects WHERE object_name LIKE ? OR object_class LIKE ? "
                "ORDER BY object_name, relative_path LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
        return [dict(row) for row in rows]
    with connect() as db:
        rows = db.execute(
            "SELECT package, name, class_name AS class FROM objects "
            "WHERE name LIKE ? OR class_name LIKE ? ORDER BY name LIMIT ?",
            (pattern, pattern, limit),
        ).fetchall()
    return [dict(row) for row in rows]
