"""Decorators that log tool calls and normalize all responses to {ok,data,meta}."""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

from mcp_servers.common.errors import ToolError, tool_result

F = TypeVar("F", bound=Callable[..., Any])


def mcp_tool(logger: logging.Logger) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                if isinstance(result, dict) and result.get("ok") is False and "error" in result:
                    result.setdefault("meta", {})
                    if isinstance(result["meta"], dict):
                        result["meta"]["elapsed_ms"] = elapsed_ms
                        result["meta"]["tool"] = fn.__name__
                    return result
                if isinstance(result, dict) and result.get("ok") is True and "data" in result:
                    meta = result.setdefault("meta", {})
                    if isinstance(meta, dict):
                        meta["elapsed_ms"] = elapsed_ms
                        meta["tool"] = fn.__name__
                    return result
                return tool_result(
                    result,
                    meta={"elapsed_ms": elapsed_ms, "tool": fn.__name__},
                )
            except ToolError as exc:
                logger.info("tool %s -> %s: %s", fn.__name__, exc.code, exc.message)
                payload = exc.to_dict()
                payload["meta"]["elapsed_ms"] = round(
                    (time.perf_counter() - started) * 1000, 3
                )
                payload["meta"]["tool"] = fn.__name__
                return payload
            except Exception as exc:  # noqa: BLE001
                logger.exception("tool %s crashed", fn.__name__)
                payload = ToolError(
                    "internal_error",
                    f"{type(exc).__name__}: {exc}",
                    tool=fn.__name__,
                ).to_dict()
                payload["meta"]["elapsed_ms"] = round(
                    (time.perf_counter() - started) * 1000, 3
                )
                return payload

        return wrapper  # type: ignore[return-value]

    return decorator
