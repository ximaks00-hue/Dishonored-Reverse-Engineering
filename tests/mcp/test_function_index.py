from __future__ import annotations

from mcp_servers.common.csv_index import FunctionIndex


def test_lookup_blink_move_mode():
    index = FunctionIndex()
    row = index.get("0x00BFC990")
    assert row["address"].upper().zfill(8) == "00BFC990"
    total, items = index.search("BFC990", limit=5)
    assert total >= 1
    assert items
