from __future__ import annotations

import pytest

from mcp_servers.common.address import (
    clamp_size,
    format_u32,
    normalize_function_entry,
    parse_u32_address,
    va_to_rva,
)
from mcp_servers.common.errors import ToolError


def test_parse_and_format():
    assert parse_u32_address("0xBFC990") == 0x00BFC990
    assert format_u32(0xBFC990) == "0x00BFC990"


def test_normalize_function_entry():
    assert normalize_function_entry("0x00bfc990") == "00BFC990"


def test_reject_tiny_rva():
    with pytest.raises(ToolError) as exc:
        normalize_function_entry("0x100")
    assert exc.value.code == "invalid_address"


def test_va_to_rva():
    assert va_to_rva(0x00BFC990) == 0x00BFC990 - 0x00400000


def test_clamp_size():
    assert clamp_size(64) == 64
    with pytest.raises(ToolError):
        clamp_size(0)
    with pytest.raises(ToolError):
        clamp_size(10_000)
