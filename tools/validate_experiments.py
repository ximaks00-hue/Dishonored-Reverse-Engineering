#!/usr/bin/env python3
"""Validate experiment markdown frontmatter, IDs, and internal links."""

from __future__ import annotations

import csv
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
FUNCTION_INDEX = ROOT / "research" / "executable" / "functions.csv"
FUNCTION_REVIEW_DIR = ROOT / "research" / "executable" / "evidence" / "function-triage"


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


def validate_function_review_overlays() -> list[str]:
    """Check reviewed function addresses and recorded sizes against the exact-build index."""
    errors: list[str] = []
    if not FUNCTION_INDEX.is_file():
        return [f"{FUNCTION_INDEX.relative_to(ROOT)}: function index is missing"]

    try:
        with FUNCTION_INDEX.open("r", encoding="utf-8-sig", newline="") as stream:
            index_reader = csv.DictReader(stream)
            if not {"address", "size"}.issubset(index_reader.fieldnames or []):
                return [f"{FUNCTION_INDEX.relative_to(ROOT)}: expected address and size columns"]
            function_sizes = {
                row["address"].strip().upper(): row["size"].strip()
                for row in index_reader
                if row.get("address") and row.get("size")
            }
    except (OSError, csv.Error) as exc:
        return [f"{FUNCTION_INDEX.relative_to(ROOT)}: cannot read function index: {exc}"]

    overlay_paths = sorted(FUNCTION_REVIEW_DIR.glob("manual-review-overlay-EXP-*.csv"))
    overlay_paths += sorted(FUNCTION_REVIEW_DIR.glob("manual-review-overlay-cumulative-EXP-*.csv"))
    for path in overlay_paths:
        relpath = path.relative_to(ROOT).as_posix()
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                if not {"address", "size_bytes"}.issubset(reader.fieldnames or []):
                    errors.append(f"{relpath}: expected address and size_bytes columns")
                    continue
                seen: set[str] = set()
                for line_number, row in enumerate(reader, start=2):
                    address = (row.get("address") or "").strip().upper()
                    size = (row.get("size_bytes") or "").strip()
                    if not re.fullmatch(r"[0-9A-F]{8}", address):
                        errors.append(f"{relpath}:{line_number}: invalid function address '{address}'")
                        continue
                    if address in seen:
                        errors.append(f"{relpath}:{line_number}: duplicate function address {address}")
                    seen.add(address)
                    indexed_size = function_sizes.get(address)
                    if indexed_size is None:
                        errors.append(f"{relpath}:{line_number}: {address} is absent from the exact-build function index")
                    elif size != indexed_size:
                        errors.append(
                            f"{relpath}:{line_number}: {address} size_bytes={size!r} "
                            f"does not match indexed size {indexed_size}"
                        )
        except (OSError, csv.Error) as exc:
            errors.append(f"{relpath}: cannot read review overlay: {exc}")
    return errors


def main() -> int:
    errors: list[str] = validate_function_review_overlays()
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
