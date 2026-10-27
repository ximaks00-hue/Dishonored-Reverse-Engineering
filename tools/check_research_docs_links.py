#!/usr/bin/env python3
"""Check repository-local Markdown links in research documentation.

This deliberately checks *path existence*, not heading anchors, web URLs,
content accuracy, or links inside fenced code blocks.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def documentation_files(root: Path) -> list[Path]:
    files = list((root / "docs").rglob("*.md"))
    files.extend(root / name for name in ("README.md", "AGENTS.md"))
    files.append(root / "mcp_servers" / "README.md")
    return sorted(path for path in files if path.is_file())


def target_from_markdown(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<"):
        return raw[1:].split(">", 1)[0]
    # Optional GFM link title follows a whitespace separator.
    return raw.split(maxsplit=1)[0]


def check_links(root: Path) -> list[str]:
    failures: list[str] = []
    for path in documentation_files(root):
        content = path.read_text(encoding="utf-8")
        # Fenced Markdown code is illustrative text, not live links.
        visible_lines: list[str] = []
        fence: str | None = None
        for line in content.splitlines():
            stripped = line.lstrip()
            token = stripped[:3]
            if token in ("```", "~~~"):
                if fence is None:
                    fence = token
                elif fence == token:
                    fence = None
                continue
            if fence is None:
                visible_lines.append(line)
        for match in LINK_RE.finditer("\n".join(visible_lines)):
            raw = target_from_markdown(match.group(1))
            if not raw or raw.startswith("#"):
                continue
            parts = urlsplit(raw)
            if parts.scheme or raw.startswith("//"):
                continue
            target = unquote(parts.path)
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                failures.append(f"{path.relative_to(root)}: link escapes repository: {raw}")
                continue
            if not resolved.exists():
                failures.append(f"{path.relative_to(root)}: missing local target: {raw}")
    return failures


def main() -> int:
    failures = check_links(ROOT)
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    count = len(documentation_files(ROOT))
    print(f"Checked {count} documentation files; {len(failures)} broken local link(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
