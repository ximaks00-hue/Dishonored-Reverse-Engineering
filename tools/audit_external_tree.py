#!/usr/bin/env python3
"""Read-only inventory and content-hash audit for an external project tree.

The source tree is never written. The SQLite manifest and reports are written only
to the caller-selected output directory. Directory symlinks/junctions are recorded
as skipped entries so recursive compatibility links cannot multiply or loop scans.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import sys
import time
from collections import Counter
from pathlib import Path

CHUNK_SIZE = 4 * 1024 * 1024
TEXT_EXTENSIONS = {
    ".md", ".txt", ".rst", ".adoc", ".html", ".htm", ".xml", ".json",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".tsv", ".py",
    ".cs", ".cpp", ".h", ".hpp", ".c", ".rs", ".js", ".ts", ".ps1",
    ".psm1", ".sql", ".bat", ".cmd", ".sh", ".properties", ".tex",
    ".diff", ".patch", ".uc", ".usf", ".hlsl", ".asm", ".sln",
    ".vcxproj", ".csproj", ".props", ".targets", ".log", ".vdf",
}


def is_junction(path: str) -> bool:
    checker = getattr(os.path, "isjunction", None)
    return bool(checker and checker(path))


def file_kind(path: Path, info: os.stat_result) -> str:
    if stat.S_ISLNK(info.st_mode):
        return "symlink"
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return "text_candidate"
    return "binary_or_unknown"


def scan(
    root: Path,
    db_path: Path,
    report_path: Path,
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    root = root.resolve(strict=True)
    db_path = db_path.resolve()
    report_path = report_path.resolve()
    if db_path == root or root in db_path.parents:
        raise ValueError("Output database must be outside the source tree")
    if report_path == root or root in report_path.parents:
        raise ValueError("Report must be outside the source tree")
    if db_path == report_path:
        raise ValueError("Database and report paths must be different")
    existing = [path for path in (db_path, report_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Output already exists; choose new paths or pass --overwrite to replace it: "
            + ", ".join(str(path) for path in existing)
        )

    # Validate all destinations before creating directories, so an invalid path
    # cannot mutate the source tree.
    db_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.executescript("""
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS skipped_directories;
        CREATE TABLE files (
            relative_path TEXT PRIMARY KEY,
            project_root TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            kind TEXT NOT NULL,
            sha256 TEXT,
            bytes_read INTEGER NOT NULL,
            status TEXT NOT NULL,
            error TEXT
        );
        CREATE INDEX files_project_idx ON files(project_root);
        CREATE INDEX files_hash_idx ON files(sha256);
        CREATE TABLE skipped_directories (
            relative_path TEXT PRIMARY KEY,
            reason TEXT NOT NULL
        );
    """)

    directories = 0
    rows: list[tuple[object, ...]] = []
    skipped: list[tuple[str, str]] = []
    byte_total = 0
    file_total = 0
    read_failures = 0
    start = time.monotonic()

    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories += 1
        retained: list[str] = []
        for dirname in dirnames:
            child = current_path / dirname
            try:
                info = child.lstat()
                if stat.S_ISLNK(info.st_mode) or is_junction(str(child)):
                    skipped.append((child.relative_to(root).as_posix(), "directory_link_not_followed"))
                else:
                    retained.append(dirname)
            except OSError as exc:
                skipped.append((child.relative_to(root).as_posix(), f"stat_error:{exc.__class__.__name__}"))
        dirnames[:] = retained

        for filename in filenames:
            path = current_path / filename
            rel = path.relative_to(root).as_posix()
            parts = Path(rel).parts
            project = parts[0] if len(parts) > 1 else "[root]"
            try:
                info = path.lstat()
                kind = file_kind(path, info)
                if stat.S_ISLNK(info.st_mode):
                    target = os.readlink(path).encode("utf-8", errors="surrogateescape")
                    digest = hashlib.sha256(target).hexdigest()
                    bytes_read = len(target)
                    status = "link_target_hashed"
                    error = None
                elif stat.S_ISREG(info.st_mode):
                    h = hashlib.sha256()
                    bytes_read = 0
                    with path.open("rb") as stream:
                        while block := stream.read(CHUNK_SIZE):
                            h.update(block)
                            bytes_read += len(block)
                    digest = h.hexdigest()
                    status = "content_hashed"
                    error = None
                else:
                    digest = None
                    bytes_read = 0
                    status = "not_regular_file"
                    error = None
                byte_total += bytes_read
            except OSError as exc:
                info = None
                kind = "unreadable"
                digest = None
                bytes_read = 0
                status = "read_error"
                error = f"{exc.__class__.__name__}: {exc}"
                read_failures += 1
            size = int(info.st_size) if info else -1
            mtime_ns = int(info.st_mtime_ns) if info else -1
            ext = path.suffix.lower() or "[none]"
            rows.append((rel, project, ext, size, mtime_ns, kind, digest, bytes_read, status, error))
            file_total += 1

            if len(rows) >= 2000:
                db.executemany("INSERT INTO files VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
                db.commit()
                rows.clear()
                print(f"hashed {file_total:,} files / {byte_total:,} bytes", flush=True)

    if rows:
        db.executemany("INSERT INTO files VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    if skipped:
        db.executemany("INSERT INTO skipped_directories VALUES (?,?)", skipped)
    db.commit()

    projects = db.execute("""
        SELECT project_root, COUNT(*), SUM(size_bytes), SUM(bytes_read),
               SUM(CASE WHEN status='read_error' THEN 1 ELSE 0 END)
        FROM files GROUP BY project_root ORDER BY project_root
    """).fetchall()
    extensions = db.execute("""
        SELECT extension, COUNT(*), SUM(size_bytes), SUM(bytes_read)
        FROM files GROUP BY extension ORDER BY COUNT(*) DESC, extension
    """).fetchall()
    duplicate_groups = db.execute("""
        SELECT COUNT(*), SUM(n-1), SUM(total_bytes-largest_bytes)
        FROM (
            SELECT sha256, COUNT(*) n, SUM(size_bytes) total_bytes,
                   MAX(size_bytes) largest_bytes
            FROM files
            WHERE sha256 IS NOT NULL AND status='content_hashed'
            GROUP BY sha256 HAVING COUNT(*) > 1
        )
    """).fetchone()
    report = {
        "source_root": str(root),
        "generated_unix_time": int(time.time()),
        "directories_scanned": directories,
        "files_scanned": file_total,
        "source_bytes": sum(int(row[2] or 0) for row in projects),
        "bytes_read_for_hashing": byte_total,
        "read_failures": read_failures,
        "directory_links_skipped": len(skipped),
        "duplicate_content_groups": int(duplicate_groups[0] or 0),
        "duplicate_file_copies": int(duplicate_groups[1] or 0),
        "duplicate_bytes_beyond_one_copy": int(duplicate_groups[2] or 0),
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "projects": [dict(name=r[0], files=r[1], bytes=r[2] or 0, hashed_bytes=r[3] or 0, failures=r[4]) for r in projects],
        "extensions": [dict(extension=r[0], files=r[1], bytes=r[2] or 0, hashed_bytes=r[3] or 0) for r in extensions],
        "manifest_db": str(db_path.resolve()),
        "method_limit": "Hashes establish byte-level inventory only. Text is not semantically reviewed by this utility. Directory symlinks/junctions are listed as skipped rather than traversed.",
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    db.close()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="source tree to audit (read-only)")
    parser.add_argument("--database", type=Path, required=True, help="SQLite manifest path outside source")
    parser.add_argument("--report", type=Path, required=True, help="JSON report path outside source")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace existing output database/report files",
    )
    args = parser.parse_args()
    try:
        report = scan(args.root, args.database, args.report, overwrite=args.overwrite)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({k: report[k] for k in (
        "directories_scanned", "files_scanned", "source_bytes", "bytes_read_for_hashing",
        "read_failures", "directory_links_skipped", "duplicate_content_groups",
        "duplicate_file_copies", "elapsed_seconds", "manifest_db",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
