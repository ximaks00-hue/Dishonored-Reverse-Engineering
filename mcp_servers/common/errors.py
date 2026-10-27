"""Structured tool errors and response envelopes."""

from __future__ import annotations

import time
from typing import Any


class ToolError(Exception):
    """Domain error raised by MCP tools; converted to a structured envelope."""

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            error["details"] = self.details
        return {
            "ok": False,
            "error": error,
            "meta": {"ts": time.time()},
        }


def tool_result(data: Any = None, *, meta: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    """Successful structured response: {ok, data, meta}."""
    payload: dict[str, Any] = {
        "ok": True,
        "data": data,
        "meta": {"ts": time.time(), **(meta or {})},
    }
    # Allow legacy callers that passed top-level extras; fold into meta except reserved keys.
    for key, value in extra.items():
        if key in {"ok", "data", "error", "meta"}:
            continue
        payload["meta"][key] = value
    return payload


def wrap_call(fn, *args, **kwargs) -> dict[str, Any]:
    """Execute fn and normalize ToolError / unexpected exceptions."""
    try:
        result = fn(*args, **kwargs)
        if isinstance(result, dict) and "ok" in result:
            return result
        return tool_result(result)
    except ToolError as exc:
        return exc.to_dict()
    except Exception as exc:  # noqa: BLE001 — last-resort MCP boundary
        return ToolError(
            "internal_error",
            f"{type(exc).__name__}: {exc}",
        ).to_dict()
