#!/usr/bin/env python3
"""Copyright-safe, dependency-free structural checks for research records."""
from __future__ import annotations
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
            "docs/research-status.md", "docs/methodology/evidence.md",
            "schemas/research-record.schema.json"]
RECORD_PATTERN = re.compile(r"^(EXP|FIND|HYP|FUNC)-[0-9]{4}[-_][a-z0-9][a-z0-9-]*\.md$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
IGNORED = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".cursor", ".nuget", ".tmp", "_excluded_coop_project",
}
RECORD_DIRS = {"experiments", "docs/findings", "docs/hypotheses", "docs/functions"}
SYNTHESIS_PAGES = {"docs/findings/README.md", "docs/findings/baseline.md", "docs/findings/blink-native.md"}

def check(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"missing required file: {name}")
    seen: dict[str, pathlib.Path] = {}
    for path in root.rglob("*.md"):
        if any(part in IGNORED for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root)
        contents = path.read_text(encoding="utf-8")
        dirname = str(rel.parent).replace("\\", "/")
        if dirname in RECORD_DIRS and path.name != "README.md" and str(rel).replace("\\", "/") not in SYNTHESIS_PAGES:
            if not RECORD_PATTERN.fullmatch(path.name):
                errors.append(f"{rel}: invalid record filename")
            else:
                record_id = "-".join(path.stem.split("-")[:2])
                if record_id in seen:
                    errors.append(f"duplicate record ID: {record_id}: {seen[record_id]} and {rel}")
                seen[record_id] = rel
        for target in LINK.findall(contents):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            local = target.split("#", 1)[0].split("?", 1)[0]
            if local and not (path.parent / local).exists():
                errors.append(f"{rel}: broken relative link: {target}")
    return errors

if __name__ == "__main__":
    problems = check()
    for issue in problems:
        print("ERROR:", issue)
    print(f"{len(problems)} issue(s)")
    sys.exit(bool(problems))
