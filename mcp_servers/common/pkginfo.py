"""Parse UModel -pkginfo text into structured package metadata."""

from __future__ import annotations

import re
from typing import Any

_SUMMARY_RE = re.compile(
    r"Ver:\s*(?P<ue_major>\d+)/(?P<ue_minor>\d+)\s+"
    r"Engine:\s*(?P<engine>\d+)\s+"
    r"Names:\s*(?P<names>\d+)\s+"
    r"Exports:\s*(?P<exports>\d+)\s+"
    r"Imports:\s*(?P<imports>\d+)\s+"
    r"Game:\s*(?P<game>\d+)",
    re.IGNORECASE,
)
_CLASS_RE = re.compile(r"^\s*(?P<count>\d+)\s+(?P<name>\S+)\s*$", re.MULTILINE)


def parse_pkginfo(output: str) -> dict[str, Any]:
    """Extract version counters and class histogram from UModel stdout.

    Returns ``parsed=False`` when the summary line is absent so callers can
    still keep the raw log.
    """
    match = _SUMMARY_RE.search(output)
    if match is None:
        return {"parsed": False}
    classes = [
        {"count": int(item.group("count")), "name": item.group("name")}
        for item in _CLASS_RE.finditer(output)
    ]
    classes.sort(key=lambda item: (-item["count"], item["name"]))
    return {
        "parsed": True,
        "ue_version": f"{match.group('ue_major')}/{match.group('ue_minor')}",
        "ue_major": int(match.group("ue_major")),
        "ue_minor": int(match.group("ue_minor")),
        "engine": int(match.group("engine")),
        "names": int(match.group("names")),
        "exports": int(match.group("exports")),
        "imports": int(match.group("imports")),
        "game": int(match.group("game")),
        "class_histogram": classes[:40],
        "class_histogram_truncated": len(classes) > 40,
    }
