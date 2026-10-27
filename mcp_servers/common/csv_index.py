"""Thread-safe CSV indexes for packages and Ghidra functions."""

from __future__ import annotations

import bisect
import csv
import threading
from pathlib import Path
from typing import Any

from mcp_servers.common.address import normalize_function_entry
from mcp_servers.common.config import get_settings
from mcp_servers.common.errors import ToolError


class CsvTable:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()
        self._rows: list[dict[str, str]] | None = None
        self._mtime_ns: int | None = None

    def invalidate(self) -> None:
        with self._lock:
            self._rows = None
            self._mtime_ns = None

    def rows(self) -> list[dict[str, str]]:
        with self._lock:
            if not self.path.is_file():
                raise ToolError(
                    "missing_dependency",
                    f"CSV index not found: {self.path}",
                    path=str(self.path),
                )
            mtime_ns = self.path.stat().st_mtime_ns
            if self._rows is not None and self._mtime_ns == mtime_ns:
                return self._rows
            with self.path.open(encoding="utf-8-sig", newline="") as stream:
                self._rows = list(csv.DictReader(stream))
            self._mtime_ns = mtime_ns
            return self._rows


class FunctionIndex:
    """Address map plus sorted body ranges for O(log n) lookup on ~70k functions."""

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self._table = CsvTable(path or settings.functions_csv)
        self._by_address: dict[str, dict[str, str]] | None = None
        self._haystack: list[tuple[str, dict[str, str]]] | None = None
        self._starts: list[int] | None = None
        self._ordered: list[dict[str, str]] | None = None
        self._rows_id: int | None = None
        self._lock = threading.RLock()

    def invalidate(self) -> None:
        with self._lock:
            self._table.invalidate()
            self._by_address = None
            self._haystack = None
            self._starts = None
            self._ordered = None
            self._rows_id = None

    def all(self) -> list[dict[str, str]]:
        self._ensure()
        assert self._ordered is not None
        return list(self._by_address.values()) if self._by_address else []

    def _ensure(self) -> None:
        with self._lock:
            rows = self._table.rows()
            if self._rows_id == id(rows) and self._by_address is not None:
                return
            mapping: dict[str, dict[str, str]] = {}
            haystack: list[tuple[str, dict[str, str]]] = []
            ordered: list[tuple[int, dict[str, str]]] = []
            for row in rows:
                key = row["address"].upper().zfill(8)
                mapping[key] = row
                haystack.append(
                    (
                        " ".join(
                            (
                                row.get("address", ""),
                                row.get("name", ""),
                                row.get("signature", ""),
                            )
                        ).casefold(),
                        row,
                    )
                )
                try:
                    start = int(row.get("body_start") or key, 16)
                except ValueError:
                    start = int(key, 16)
                ordered.append((start, row))
            ordered.sort(key=lambda item: item[0])
            self._by_address = mapping
            self._haystack = haystack
            self._ordered = [row for _, row in ordered]
            self._starts = [start for start, _ in ordered]
            self._rows_id = id(rows)

    def _index(self) -> dict[str, dict[str, str]]:
        self._ensure()
        assert self._by_address is not None
        return self._by_address

    def get(self, address: str) -> dict[str, str]:
        key = normalize_function_entry(address)
        row = self._index().get(key)
        if row is None:
            raise ToolError(
                "function_not_found",
                f"No function entry at 0x{key}",
                address=f"0x{key}",
            )
        return row

    def search(
        self, query: str = "", *, limit: int = 50, offset: int = 0
    ) -> tuple[int, list[dict[str, str]]]:
        self._ensure()
        assert self._haystack is not None
        q = query.casefold()
        if not q:
            rows = [row for _, row in self._haystack]
        else:
            rows = [row for text, row in self._haystack if q in text]
        return len(rows), rows[offset : offset + limit]

    def get_many(self, addresses: list[str]) -> dict[str, Any]:
        found: list[dict[str, str]] = []
        missing: list[str] = []
        for address in addresses:
            try:
                found.append(self.get(address))
            except ToolError:
                missing.append(address)
        return {"found": found, "missing": missing, "found_count": len(found)}

    def containing(self, address: str) -> dict[str, str]:
        """Return the function whose [body_start, body_end] contains the VA."""
        self._ensure()
        assert self._starts is not None and self._ordered is not None
        va = int(normalize_function_entry(address), 16)
        index = bisect.bisect_right(self._starts, va) - 1
        while index >= 0:
            row = self._ordered[index]
            start = self._starts[index]
            if va - start > 0x20000:
                break
            try:
                end = int(row.get("body_end") or row["address"], 16)
            except ValueError:
                end = start
            if start <= va <= end:
                return row
            index -= 1
        raise ToolError(
            "function_not_found",
            f"No function body contains 0x{va:08X}",
            address=f"0x{va:08X}",
        )

    def in_range(self, start: str, end: str, *, limit: int = 50) -> list[dict[str, str]]:
        """Functions whose entry VA lies in [start, end], inclusive."""
        self._ensure()
        assert self._starts is not None and self._ordered is not None
        lo = int(normalize_function_entry(start), 16)
        hi = int(normalize_function_entry(end), 16)
        if hi < lo:
            raise ToolError("invalid_range", "end address is below start", start=start, end=end)
        left = bisect.bisect_left(self._starts, lo)
        out: list[dict[str, str]] = []
        index = left
        while index < len(self._ordered) and self._starts[index] <= hi and len(out) < limit:
            out.append(self._ordered[index])
            index += 1
        return out


class PackageIndex:
    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self._table = CsvTable(path or settings.packages_index)
        self._by_name: dict[str, list[dict[str, str]]] | None = None
        self._by_path: dict[str, dict[str, str]] | None = None
        self._rows_id: int | None = None
        self._lock = threading.RLock()

    def invalidate(self) -> None:
        with self._lock:
            self._table.invalidate()
            self._by_name = None
            self._by_path = None
            self._rows_id = None

    def all(self) -> list[dict[str, str]]:
        return self._table.rows()

    def _index(self) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
        with self._lock:
            rows = self._table.rows()
            if (
                self._rows_id == id(rows)
                and self._by_name is not None
                and self._by_path is not None
            ):
                return self._by_name, self._by_path
            by_name: dict[str, list[dict[str, str]]] = {}
            by_path: dict[str, dict[str, str]] = {}
            for row in rows:
                relative = row["RelativePath"].replace("\\", "/")
                name = Path(relative).name.casefold()
                by_name.setdefault(name, []).append(row)
                by_path[relative.casefold()] = row
            self._by_name = by_name
            self._by_path = by_path
            self._rows_id = id(rows)
            return by_name, by_path

    def resolve_upk(self, package: str) -> dict[str, str]:
        settings = get_settings()
        normalized = package.replace("\\", "/")
        parts = normalized.split("/")
        if (
            not normalized
            or normalized.startswith("/")
            or ":" in normalized
            or any(part in {"", ".", ".."} for part in parts)
            or not normalized.casefold().endswith(".upk")
        ):
            raise ToolError(
                "invalid_package",
                "Pass a manifest-listed .upk filename or game-root-relative path",
                package=package,
            )
        by_name, by_path = self._index()
        if "/" in normalized:
            row = by_path.get(normalized.casefold())
        else:
            candidates = by_name.get(normalized.casefold(), [])
            if len(candidates) > 1:
                raise ToolError(
                    "ambiguous_package",
                    "Package filename occurs at multiple paths; pass a relative path",
                    package=package,
                    matches=[item["RelativePath"] for item in candidates],
                )
            row = candidates[0] if candidates else None
        if row is None:
            raise ToolError(
                "package_not_found",
                f"Package is not present in the local manifest: {package}",
                package=package,
            )
        target = ensure_under(settings.game_root, settings.game_root / row["RelativePath"])
        if target.suffix.casefold() != ".upk" or not target.is_file():
            raise ToolError(
                "package_unavailable",
                "Package path is outside the game root or the file is missing",
                package=package,
                resolved=str(target),
                game_root=str(settings.game_root),
            )
        return row

    def search(
        self, query: str = "", *, limit: int = 50, upk_only: bool = True
    ) -> list[dict[str, str]]:
        q = query.casefold()
        matches: list[dict[str, str]] = []
        for row in self.all():
            relative = row.get("RelativePath", "")
            if upk_only and not relative.casefold().endswith(".upk"):
                continue
            if q and q not in relative.casefold():
                continue
            matches.append(row)
            if len(matches) >= limit:
                break
        return matches


def ensure_under(parent: Path, child: Path) -> Path:
    """Resolve child and require it to stay under parent (path-traversal guard)."""
    parent_r = parent.resolve()
    child_r = child.resolve()
    if child_r != parent_r and parent_r not in child_r.parents:
        raise ToolError(
            "path_escape",
            "Resolved path escaped the allowed directory",
            parent=str(parent_r),
            child=str(child_r),
        )
    return child_r
