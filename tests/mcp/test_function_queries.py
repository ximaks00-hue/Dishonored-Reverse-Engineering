from __future__ import annotations

from mcp_servers.common.csv_index import FunctionIndex
from mcp_servers.common.errors import ToolError
import pytest


def test_containing_and_range():
    index = FunctionIndex()
    row = index.containing("0x00BFC990")
    assert row["address"].upper().endswith("BFC990") or row["address"].upper().zfill(8) == "00BFC990"
    window = index.in_range("0x00BFC980", "0x00BFC9A0", limit=20)
    assert any(item["address"].upper().zfill(8) == "00BFC990" for item in window)


def test_batch_reports_missing():
    index = FunctionIndex()
    result = index.get_many(["0x00BFC990", "0x00000010"])
    assert result["found_count"] == 1
    assert result["missing"]


def test_inverted_range_rejected():
    index = FunctionIndex()
    with pytest.raises(ToolError) as exc:
        index.in_range("0x00C00000", "0x00B00000")
    assert exc.value.code == "invalid_range"
