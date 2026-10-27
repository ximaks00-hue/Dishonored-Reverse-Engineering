from __future__ import annotations

from mcp_servers.common.database import connect, row_dicts


def test_schema_and_edges():
    with connect(write=False) as db:
        edges = row_dicts(
            db.execute(
                "SELECT edge_key, status FROM evidence_edges ORDER BY edge_key"
            ).fetchall()
        )
    keys = {e["edge_key"] for e in edges}
    assert "E5" in keys
    assert "E9" in keys
