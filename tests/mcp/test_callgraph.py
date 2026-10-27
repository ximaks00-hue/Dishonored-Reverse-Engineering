from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from mcp_servers.common import callgraph
from mcp_servers.common.errors import ToolError


def _seed(db_path: Path) -> None:
    callgraph.ensure_schema(db_path)
    with sqlite3.connect(db_path) as db:
        db.executescript(callgraph.SCHEMA)
        db.execute("DELETE FROM edges")
        db.executemany(
            "INSERT INTO edges(kind, from_addr, to_addr, from_name, to_name, site_addr) "
            "VALUES(?,?,?,?,?,?)",
            [
                ("call", "00AA0000", "00BB0000", "A", "B", "00AA0010"),
                ("call", "00BB0000", "00CC0000", "B", "C", "00BB0020"),
                ("call", "00AA0000", "00CC0000", "A", "C", "00AA0030"),
                ("data", "00DD0000", "00BB0000", "D", "B", "00DD0004"),
            ],
        )
        db.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('exe_sha256', 'TEST')"
        )
        db.commit()


def test_callers_callees_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "callgraph.sqlite"
    _seed(db_path)
    monkeypatch.setenv("DISHONORED_CALLGRAPH_DB", str(db_path))
    from mcp_servers.common.config import get_settings

    get_settings(refresh=True)

    callers = callgraph.callers("0x00BB0000")
    assert callers["count"] == 1
    assert callers["items"][0]["from_addr"] == "00AA0000"

    callees = callgraph.callees("0x00AA0000")
    assert callees["count"] == 2

    xrefs = callgraph.xrefs_to("0x00BB0000")
    assert xrefs["count"] == 2

    found = callgraph.path("0x00AA0000", "0x00CC0000", max_depth=3)
    assert found["found"] is True
    assert found["depth"] >= 1

    missing = callgraph.path("0x00CC0000", "0x00AA0000", max_depth=2)
    assert missing["found"] is False


def test_index_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    missing = tmp_path / "missing.sqlite"
    monkeypatch.setenv("DISHONORED_CALLGRAPH_DB", str(missing))
    from mcp_servers.common.config import get_settings

    get_settings(refresh=True)
    with pytest.raises(ToolError) as exc:
        callgraph.callers("0x00AA0000")
    assert exc.value.code == "index_missing"
