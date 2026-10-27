"""x86 address / RVA helpers bound to the configured image base."""

from __future__ import annotations

import re

from mcp_servers.common.config import Settings, get_settings
from mcp_servers.common.errors import ToolError

_ADDRESS_RE = re.compile(r"^(?:0[xX])?([0-9a-fA-F]{1,8})$")


def parse_u32_address(value: str, *, field: str = "address") -> int:
    match = _ADDRESS_RE.fullmatch(value.strip())
    if not match:
        raise ToolError(
            "invalid_address",
            f"{field} must be a 32-bit hexadecimal value, e.g. 0x00BFC990",
            field=field,
            value=value,
        )
    number = int(match.group(1), 16)
    if not 0 <= number <= 0xFFFFFFFF:
        raise ToolError(
            "invalid_address",
            f"{field} is outside the 32-bit range",
            field=field,
            value=value,
        )
    return number


def format_u32(address: int) -> str:
    return f"0x{address & 0xFFFFFFFF:08X}"


def normalize_function_entry(value: str, settings: Settings | None = None) -> str:
    """Return zero-padded uppercase hex without 0x prefix (functions.csv style)."""
    cfg = settings or get_settings()
    address = parse_u32_address(value, field="function_address")
    # Accept either VA or bare RVA-looking small values only when explicitly below image base
    # with enough digits; otherwise treat as VA. Our index stores VAs.
    if address < cfg.image_base and address < 0x10000:
        raise ToolError(
            "invalid_address",
            "Pass a virtual address from the Ghidra index (image base 0x00400000), not a tiny RVA",
            value=value,
        )
    return f"{address:08X}"


def va_to_rva(va: int, settings: Settings | None = None) -> int:
    cfg = settings or get_settings()
    if va < cfg.image_base:
        raise ToolError(
            "invalid_address",
            "VA is below the configured image base",
            va=format_u32(va),
            image_base=format_u32(cfg.image_base),
        )
    return va - cfg.image_base


def rva_to_va(rva: int, settings: Settings | None = None) -> int:
    cfg = settings or get_settings()
    if not 0 <= rva <= 0xFFFFFFFF - cfg.image_base:
        raise ToolError("invalid_address", "RVA out of range for configured image", rva=rva)
    return cfg.image_base + rva


def clamp_size(size: int, *, maximum: int | None = None, field: str = "size") -> int:
    cfg = get_settings()
    limit = maximum if maximum is not None else cfg.max_memory_read
    if not 1 <= size <= limit:
        raise ToolError(
            "invalid_size",
            f"{field} must be between 1 and {limit}",
            field=field,
            size=size,
            maximum=limit,
        )
    return size


def clamp_limit(limit: int, *, maximum: int | None = None, field: str = "limit") -> int:
    cfg = get_settings()
    cap = maximum if maximum is not None else cfg.max_list_limit
    if limit < 1:
        raise ToolError("invalid_limit", f"{field} must be >= 1", field=field, limit=limit)
    return min(limit, cap)
