from __future__ import annotations

import pytest

from mcp_servers.common.csv_index import PackageIndex
from mcp_servers.common.errors import ToolError


def test_search_dishonored_game():
    index = PackageIndex()
    rows = index.search("DishonoredGame.upk", limit=5)
    assert rows
    assert any(r["RelativePath"].endswith("DishonoredGame.upk") for r in rows)


def test_resolve_rejects_path_components():
    index = PackageIndex()
    with pytest.raises(ToolError) as exc:
        index.resolve_upk("CookedPCConsole/DishonoredGame.upk")
    assert exc.value.code == "invalid_package"


def test_resolve_ok():
    index = PackageIndex()
    row = index.resolve_upk("DishonoredGame.upk")
    assert "DishonoredGame.upk" in row["RelativePath"]
