#!/usr/bin/env python3
"""Validate experiment markdown frontmatter, IDs, and internal links."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
ID_RE = re.compile(r"^EXP-\d{4}$")
REQUIRED = (
    "id",
    "title",
    "experiment_status",
    "claim_status",
    "build",
    "question",
)
EXPERIMENT_STATUS = {"planned", "in_progress", "done", "superseded"}
CLAIM_STATUS = {
    "confirmed",
    "observed",
    "inferred",
    "unknown",
    "superseded",
    "mixed",
    "rejected",
}
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def expected_id(path: Path) -> str:
    parts = path.stem.split("-")
    if len(parts) >= 2 and parts[0] == "EXP":
        return f"EXP-{parts[1]}"
    return path.stem


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, Path] = {}
    files = sorted(EXPERIMENTS.glob("EXP-*.md"))
    if not files:
        print("No experiment files found", file=sys.stderr)
        return 1

    for path in files:
        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        if meta is None:
            errors.append(f"{path.name}: missing YAML frontmatter")
            continue
        # Compatibility: old single `status` field is an error after repair.
        if "status" in meta and "experiment_status" not in meta:
            errors.append(
                f"{path.name}: legacy 'status' field; use experiment_status + claim_status"
            )
        for key in REQUIRED:
            if not meta.get(key):
                errors.append(f"{path.name}: missing required frontmatter key '{key}'")
        exp_id = meta.get("id", "")
        if exp_id and not ID_RE.match(exp_id):
            errors.append(f"{path.name}: id '{exp_id}' must match EXP-NNNN")
        expected = expected_id(path)
        if exp_id and exp_id != expected:
            errors.append(
                f"{path.name}: id '{exp_id}' does not match filename id '{expected}'"
            )
        if exp_id in seen_ids:
            errors.append(
                f"{path.name}: duplicate id '{exp_id}' also in {seen_ids[exp_id].name}"
            )
        elif exp_id:
            seen_ids[exp_id] = path

        est = meta.get("experiment_status", "")
        if est and est not in EXPERIMENT_STATUS:
            errors.append(f"{path.name}: invalid experiment_status '{est}'")
        cst = meta.get("claim_status", "")
        if cst and cst not in CLAIM_STATUS:
            errors.append(f"{path.name}: invalid claim_status '{cst}'")

        title = meta.get("title", "")
        question = meta.get("question", "")
        if title and question and title == question:
            warnings.append(f"{path.name}: question duplicates title")

        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            rel = target.split("#", 1)[0]
            if not rel:
                continue
            resolved = (path.parent / rel).resolve()
            if not resolved.exists():
                # These paths intentionally refer to machine-local inputs or
                # generated outputs, which are excluded from Git. Their absence
                # in a clean checkout is not a broken link in the published corpus.
                repo_rel = resolved.relative_to(ROOT).as_posix() if resolved.is_relative_to(ROOT) else ""
                if repo_rel.startswith("assets/extracted/") or repo_rel == "tools/ue-package-decompressor/decompress.exe":
                    continue
                errors.append(f"{path.name}: broken link '{target}'")

    numbers = sorted(int(i.split("-")[1]) for i in seen_ids)
    if numbers:
        present = {int(i.split("-")[1]) for i in seen_ids}
        missing = [n for n in range(numbers[0], numbers[-1] + 1) if n not in present]
        if missing:
            warnings.append(
                "missing experiment numbers in range: "
                + ", ".join(f"EXP-{n:04d}" for n in missing)
            )

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    print(
        f"Checked {len(files)} experiments; {len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
