#!/usr/bin/env python3
"""Copyright-safe structural and schema checks for research records."""
from __future__ import annotations
import html
import json
import pathlib
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
            "docs/research-status.md", "docs/methodology/evidence.md",
            "schemas/research-record.schema.json"]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
ATX_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
SETEXT_HEADING = re.compile(r"^\s{0,3}(=+|-+)\s*$")
HTML_ANCHOR = re.compile(r"<(?:a|h[1-6])\b[^>]*\b(?:id|name)\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s>]+))", re.I)
IGNORED = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".cursor", ".nuget", ".tmp", "_excluded_coop_project",
}
RECORD_DIRS = {"experiments", "docs/findings", "docs/hypotheses", "docs/functions"}
SYNTHESIS_PAGES = {"docs/findings/README.md", "docs/findings/baseline.md", "docs/findings/blink-native.md"}
LOCAL_ONLY_PREFIXES = ("assets/extracted/",)
LOCAL_ONLY_FILES = {"tools/ue-package-decompressor/decompress.exe"}
RECORD_FILENAME = re.compile(r"^(?P<prefix>EXP|FIND|OBS|HYP)-(?P<serial>[0-9]{4})-(?P<slug>[a-z0-9][a-z0-9-]*)\.(?P<extension>md|json)$")
EXPERIMENT_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)
REQUIRED = REQUIRED + ["schemas/experiment-frontmatter.schema.json", "requirements-dev.txt"]


def markdown_anchors(text: str) -> set[str]:
    """Return GitHub-style heading slugs plus explicit HTML ids/names."""
    anchors: set[str] = set()
    slug_counts: dict[str, int] = {}
    lines = text.splitlines()
    in_fence = False
    fence_marker = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        fence_match = FENCE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
            index += 1
            continue
        if not in_fence:
            heading_match = ATX_HEADING.match(line)
            heading = heading_match.group(1) if heading_match else None
            if heading is None and index + 1 < len(lines) and SETEXT_HEADING.match(lines[index + 1]):
                heading = line.strip()
                index += 1
            if heading:
                slug_text = re.sub(r"`([^`]*)`", r"\1", heading)
                slug_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", slug_text)
                slug_text = html.unescape(re.sub(r"<[^>]+>", "", slug_text)).casefold()
                slug = re.sub(r"[^\w -]", "", slug_text, flags=re.UNICODE).strip()
                slug = re.sub(r"\s+", "-", slug)
                occurrence = slug_counts.get(slug, 0)
                slug_counts[slug] = occurrence + 1
                anchors.add(slug if occurrence == 0 else f"{slug}-{occurrence}")
            for html_match in HTML_ANCHOR.finditer(line):
                anchors.add(next(value for value in html_match.groups() if value is not None))
        index += 1
    return anchors


def parse_record_id(filename: str) -> str | None:
    """Parse the typed, four-digit record ID from a supported filename."""
    match = RECORD_FILENAME.fullmatch(pathlib.Path(filename).name)
    if not match:
        return None
    return f"{match.group('prefix')}-{match.group('serial')}"


def _schema_errors(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        import yaml
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        return [f"schema validation dependencies missing: {exc}; install requirements-dev.txt"]

    schema_paths = {
        "structured": root / "schemas/research-record.schema.json",
        "experiment_frontmatter": root / "schemas/experiment-frontmatter.schema.json",
    }
    schemas: dict[str, dict] = {}
    for name, schema_path in schema_paths.items():
        if not schema_path.is_file():
            continue
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[name] = schema
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{schema_path.relative_to(root)}: invalid JSON Schema: {exc}")

    structured_validator = Draft202012Validator(schemas["structured"]) if "structured" in schemas else None
    experiment_validator = Draft202012Validator(schemas["experiment_frontmatter"]) if "experiment_frontmatter" in schemas else None

    experiment_root = root / "experiments"
    for path in sorted(experiment_root.rglob("*.md")) if experiment_root.exists() else []:
        rel = path.relative_to(root)
        if path.name == "README.md":
            continue
        if experiment_validator is None:
            continue
        match = EXPERIMENT_FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            errors.append(f"{rel}: missing YAML frontmatter for experiment schema")
            continue
        try:
            record = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: invalid YAML frontmatter: {exc}")
            continue
        filename = RECORD_FILENAME.fullmatch(path.name)
        expected_id = parse_record_id(path.name) if filename else None
        if not isinstance(record, dict):
            errors.append(f"{rel}: YAML frontmatter must be an object")
            continue
        if record.get("id") != expected_id:
            errors.append(f"{rel}: frontmatter id {record.get('id')!r} does not match filename id {expected_id!r}")
        for issue in experiment_validator.iter_errors(record):
            location = ".".join(str(part) for part in issue.absolute_path)
            errors.append(f"{rel}: frontmatter schema {location}: {issue.message}")

    if structured_validator is not None:
        record_roots = [root / "docs/findings", root / "docs/hypotheses", root / "docs/functions", root / "research/records"]
        for record_root in record_roots:
            if not record_root.exists():
                continue
            for path in sorted(record_root.rglob("*.json")):
                match = RECORD_FILENAME.fullmatch(path.with_suffix(".json").name)
                if not match:
                    continue
                rel = path.relative_to(root)
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    errors.append(f"{rel}: invalid JSON record: {exc}")
                    continue
                expected_id = f"{match.group('prefix')}-{match.group('serial')}"
                if not isinstance(record, dict):
                    errors.append(f"{rel}: JSON record must be an object")
                    continue
                if record.get("id") != expected_id:
                    errors.append(f"{rel}: record id {record.get('id')!r} does not match filename id {expected_id!r}")
                for issue in structured_validator.iter_errors(record):
                    location = ".".join(str(part) for part in issue.absolute_path)
                    errors.append(f"{rel}: record schema {location}: {issue.message}")
    return errors

def check(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = _schema_errors(root)
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"missing required file: {name}")
    seen: dict[str, pathlib.Path] = {}
    anchor_cache: dict[pathlib.Path, set[str]] = {}
    for path in root.rglob("*.md"):
        if any(part in IGNORED for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root)
        contents = path.read_text(encoding="utf-8")
        dirname = str(rel.parent).replace("\\", "/")
        matching_record_dir = any(dirname == record_dir or dirname.startswith(record_dir + "/") for record_dir in RECORD_DIRS)
        if matching_record_dir and path.name != "README.md" and str(rel).replace("\\", "/") not in SYNTHESIS_PAGES:
            filename_match = RECORD_FILENAME.fullmatch(path.name)
            if not filename_match:
                errors.append(f"{rel}: invalid record filename")
            else:
                record_id = parse_record_id(path.name)
                if record_id in seen:
                    errors.append(f"duplicate record ID: {record_id}: {seen[record_id]} and {rel}")
                seen[record_id] = rel
        for target in LINK.findall(contents):
            destination = target.strip().strip("<>")
            parsed = urlsplit(destination)
            if parsed.scheme or destination.startswith("//"):
                continue
            local = unquote(parsed.path)
            resolved = (path.parent / local).resolve() if local else path.resolve()
            if not resolved.exists():
                try:
                    repository_path = resolved.relative_to(root.resolve()).as_posix()
                except ValueError:
                    repository_path = ""
                if repository_path not in LOCAL_ONLY_FILES and not repository_path.startswith(LOCAL_ONLY_PREFIXES):
                    errors.append(f"{rel}: broken relative link: {target}")
                continue
            if parsed.fragment and resolved.is_file() and resolved.suffix.casefold() == ".md":
                if resolved not in anchor_cache:
                    anchor_cache[resolved] = markdown_anchors(resolved.read_text(encoding="utf-8"))
                anchor = unquote(parsed.fragment)
                if anchor not in anchor_cache[resolved] and anchor.casefold() not in {value.casefold() for value in anchor_cache[resolved]}:
                    errors.append(f"{rel}: broken local anchor '{parsed.fragment}' in {resolved.relative_to(root)}")
    return errors

if __name__ == "__main__":
    problems = check()
    for issue in problems:
        print("ERROR:", issue)
    print(f"{len(problems)} issue(s)")
    sys.exit(bool(problems))
