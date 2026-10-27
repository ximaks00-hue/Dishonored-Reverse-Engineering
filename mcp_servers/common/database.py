"""SQLite access with schema apply + additive migrations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterable, Iterator

from mcp_servers.common.config import get_settings
from mcp_servers.common.errors import ToolError

_MIGRATIONS: dict[str, dict[str, str]] = {
    "experiments": {
        "experiment_key": "TEXT",
        "status": "TEXT NOT NULL DEFAULT 'observed'",
        "experiment_status": "TEXT NOT NULL DEFAULT 'done'",
        "claim_status": "TEXT NOT NULL DEFAULT 'observed'",
        "path": "TEXT NOT NULL DEFAULT ''",
    },
    "functions": {
        "status": "TEXT NOT NULL DEFAULT 'observed'",
        "experiment_key": "TEXT",
    },
    "hypotheses": {"experiment_key": "TEXT"},
    "function_analysis_runs": {
        "is_current": "INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1))",
    },
    "function_claims": {
        "is_current": "INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1))",
        "evidence_va": "INTEGER CHECK (evidence_va IS NULL OR evidence_va >= 0)",
        "evidence_rva": "INTEGER CHECK (evidence_rva IS NULL OR evidence_rva >= 0)",
    },
}


def _migrate(connection: sqlite3.Connection) -> None:
    for table, specs in _MIGRATIONS.items():
        existing = {
            row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if not existing:
            continue
        for name, decl in specs.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_experiments_key_unique "
        "ON experiments(experiment_key) WHERE experiment_key IS NOT NULL"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_edges_status ON evidence_edges(status)"
    )


def _pre_migrate_function_evidence(connection: sqlite3.Connection) -> None:
    """Make columns available before schema.sql rebuilds the dependent view."""
    for table in ("function_analysis_runs", "function_claims"):
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not exists:
            continue
        existing = {
            row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, declaration in _MIGRATIONS[table].items():
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


@contextmanager
def connect(*, write: bool = True) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    settings.research_db.parent.mkdir(parents=True, exist_ok=True)
    if not settings.schema_sql.is_file():
        raise ToolError(
            "missing_dependency",
            f"Schema file missing: {settings.schema_sql}",
            path=str(settings.schema_sql),
        )
    connection = sqlite3.connect(
        settings.research_db,
        timeout=5,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _pre_migrate_function_evidence(connection)
        connection.executescript(settings.schema_sql.read_text(encoding="utf-8"))
        _migrate(connection)
        from mcp_servers.common.fts import ensure_fts

        ensure_fts(connection)
        connection.commit()
        yield connection
        if write:
            connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise ToolError("database_error", str(exc)) from exc
    finally:
        connection.close()


def row_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
