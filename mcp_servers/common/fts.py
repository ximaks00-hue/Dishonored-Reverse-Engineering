"""FTS5 index over research mirror hot paths."""

from __future__ import annotations

import sqlite3
from typing import Any

from mcp_servers.common.database import connect, row_dicts
from mcp_servers.common.errors import ToolError

_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS research_fts USING fts5(
    kind UNINDEXED,
    key UNINDEXED,
    title,
    body,
    tokenize = 'porter unicode61'
);
"""


def ensure_fts(db: sqlite3.Connection) -> None:
    db.executescript(_FTS_DDL)
    count = db.execute("SELECT COUNT(*) AS c FROM research_fts").fetchone()[0]
    if count > 0:
        return
    rebuild_fts(db)


def rebuild_fts(db: sqlite3.Connection) -> int:
    db.execute("DELETE FROM research_fts")
    db.execute(
        """
        INSERT INTO research_fts(kind, key, title, body)
        SELECT 'experiment',
               coalesce(experiment_key, cast(id AS text)),
               coalesce(title, ''),
               coalesce(procedure, '') || ' ' || coalesce(result, '')
          FROM experiments
        """
    )
    db.execute(
        """
        INSERT INTO research_fts(kind, key, title, body)
        SELECT 'function',
               coalesce(module, '') || '!' || coalesce(address, ''),
               coalesce(name, address, ''),
               coalesce(summary, '') || ' ' || coalesce(signature, '')
          FROM functions
        """
    )
    db.execute(
        """
        INSERT INTO research_fts(kind, key, title, body)
        SELECT 'edge',
               edge_key,
               edge_key || ' ' || coalesce(source_node, '') || ' -> ' || coalesce(target_node, ''),
               coalesce(summary, '')
          FROM evidence_edges
        """
    )
    return db.execute("SELECT COUNT(*) AS c FROM research_fts").fetchone()[0]


def search_fts(query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    if not query.strip():
        raise ToolError("invalid_query", "query must be non-empty")
    limit = max(1, min(int(limit), 100))
    # Escape FTS5 special chars by quoting the whole phrase when operators appear.
    raw = query.strip()
    if any(ch in raw for ch in '"*^'):
        fts_query = '"' + raw.replace('"', '""') + '"'
    else:
        # Prefix match on each token for agent-friendly partials.
        tokens = [t for t in raw.split() if t]
        fts_query = " ".join(f"{t}*" for t in tokens) if tokens else raw
    with connect(write=False) as db:
        ensure_fts(db)
        try:
            rows = db.execute(
                """
                SELECT kind, key, title, body,
                       snippet(research_fts, 3, '[', ']', '…', 12) AS snippet
                  FROM research_fts
                 WHERE research_fts MATCH ?
                 LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            # Fall back to literal phrase if the query is invalid FTS syntax.
            rows = db.execute(
                """
                SELECT kind, key, title, body,
                       snippet(research_fts, 3, '[', ']', '…', 12) AS snippet
                  FROM research_fts
                 WHERE research_fts MATCH ?
                 LIMIT ?
                """,
                ('"' + raw.replace('"', '""') + '"', limit),
            ).fetchall()
    return row_dicts(rows)
