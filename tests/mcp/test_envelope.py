from __future__ import annotations

from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.errors import ToolError, tool_result
import logging

_log = logging.getLogger("test_envelope")


@mcp_tool(_log)
def _ok() -> dict:
    return {"value": 1}


@mcp_tool(_log)
def _fail() -> dict:
    raise ToolError("index_missing", "no graph", path="/tmp/x")


def test_tool_result_shape():
    payload = tool_result({"a": 1}, meta={"tool": "x"})
    assert payload["ok"] is True
    assert payload["data"] == {"a": 1}
    assert "meta" in payload
    assert "ts" in payload["meta"]


def test_decorator_wraps_success():
    payload = _ok()
    assert payload["ok"] is True
    assert payload["data"]["value"] == 1
    assert payload["meta"]["tool"] == "_ok"
    assert "elapsed_ms" in payload["meta"]


def test_decorator_wraps_tool_error():
    payload = _fail()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "index_missing"
    assert payload["meta"]["tool"] == "_fail"
