#!/usr/bin/env python3
"""Check repository-local Markdown links in all tracked Markdown files.

This checks local target paths and repository-boundary escapes. It does not
validate heading fragments, external URLs, or Markdown syntax in general.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INLINE_LINK_RE = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")
REFERENCE_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S.*?)\s*$")
INLINE_CODE_RE = re.compile(r"(?<!`)`+[^`]*`+(?!`)")


def markdown_files(root: Path) -> list[Path]:
    """Return tracked Markdown files, or all Markdown files in a fixture tree."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "*.md",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout:
        names = result.stdout.decode("utf-8", errors="strict").split("\0")
        return sorted(root / name for name in names if name.lower().endswith(".md"))
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def link_target(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<"):
        return raw[1:].split(">", 1)[0]
    # An optional GFM title follows whitespace after the destination.
    return raw.split(maxsplit=1)[0] if raw else ""


def visible_markdown_lines(content: str) -> list[tuple[int, str]]:
    """Remove fenced blocks and inline code while preserving source line numbers."""
    visible: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_size = 0
    for line_number, line in enumerate(content.splitlines(), 1):
        stripped = line.lstrip()
        match = re.match(r"(`{3,}|~{3,})", stripped)
        if match:
            marker = match.group(1)
            if fence_char is None:
                fence_char, fence_size = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                fence_char, fence_size = None, 0
            continue
        if fence_char is None:
            # Preserve a placeholder so code-formatted link labels do not turn
            # into empty Markdown labels and disappear from the scan.
            visible.append((line_number, INLINE_CODE_RE.sub("CODE", line)))
    return visible


def local_link_failures(root: Path, path: Path) -> list[str]:
    failures: list[str] = []
    root = root.resolve()
    content = path.read_text(encoding="utf-8")
    candidates: list[tuple[int, str]] = []
    for line_number, line in visible_markdown_lines(content):
        candidates.extend((line_number, match.group(1)) for match in INLINE_LINK_RE.finditer(line))
        match = REFERENCE_RE.match(line)
        if match:
            candidates.append((line_number, match.group(1)))

    for line_number, raw in candidates:
        destination = link_target(raw)
        if not destination or destination.startswith("#"):
            continue
        parsed = urlsplit(destination)
        if parsed.scheme or destination.startswith("//"):
            continue
        relative_path = unquote(parsed.path)
        if not relative_path:
            continue
        resolved = (path.parent / relative_path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            failures.append(
                f"{path.relative_to(root)}:{line_number}: link escapes repository: {destination}"
            )
            continue
        if not resolved.exists():
            failures.append(
                f"{path.relative_to(root)}:{line_number}: missing local target: {destination}"
            )
    return failures


def check_links(root: Path) -> list[str]:
    failures: list[str] = []
    for path in markdown_files(root):
        if path.is_file():
            failures.extend(local_link_failures(root, path))
    return failures


def main() -> int:
    files = markdown_files(ROOT)
    failures = check_links(ROOT)
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    print(f"Checked {len(files)} tracked Markdown files; {len(failures)} broken local link(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
