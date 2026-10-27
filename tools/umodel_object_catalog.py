#!/usr/bin/env python3
"""Create a local SQLite catalog from UModel -list output for installed UPKs.

The database is a generated metadata index. It does not contain package bytes,
textures, audio, meshes, or exported scripts.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

SUMMARY_RE = re.compile(
    r"Loading package:\s*(.*?)\s+Ver:\s+(\S+)\s+Engine:\s+(\d+)"
    r"\s+Names:\s+(\d+)\s+Exports:\s+(\d+)\s+Imports:\s+(\d+)"
    r"\s+Game:\s+(\d+)"
)
OBJECT_RE = re.compile(r"^\s*(\d+)\s+([0-9A-Fa-f]+)\s+([0-9A-Fa-f]+)\s+(.+?)\s*$")
WARNING_RE = re.compile(r"WARNING:\s*([^:]+):")
ERROR_RE = re.compile(r"(?:ERROR|FATAL):\s*([^:]+):")
PACKAGE_HEADER_RE = re.compile(r"^([^\s].*\.upk)$", re.IGNORECASE)
FOLDERS = [
    "DishonoredGame/CookedPCConsole",
    "DishonoredGame/DLC/PCConsole/DLC05",
    "DishonoredGame/DLC/PCConsole/DLC06",
    "DishonoredGame/DLC/PCConsole/DLC07",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--umodel", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--pkginfo-census", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    umodel = args.umodel.resolve(strict=True)
    game_root = args.game_root.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True)
    pkginfo_path = args.pkginfo_census.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing catalog: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    manifest_rows = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in read_csv(manifest)
    }
    pkginfo_rows = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in read_csv(pkginfo_path)
    }
    expected = {
        path: row
        for path, row in manifest_rows.items()
        if path.endswith(".upk")
        and any(path.startswith(f"{folder}/".casefold()) for folder in FOLDERS)
    }
    if set(expected) != set(pkginfo_rows):
        raise ValueError(
            f"manifest/census package sets differ: manifest={len(expected)}, "
            f"census={len(pkginfo_rows)}"
        )

    fd, temp_name = tempfile.mkstemp(
        prefix=output.name + ".", suffix=".partial", dir=output.parent
    )
    os.close(fd)
    temp_db = Path(temp_name)
    package_rows = 0
    object_rows = 0
    package_statuses: Counter[str] = Counter()
    db: sqlite3.Connection | None = None

    try:
        db = sqlite3.connect(temp_db)
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute(
            """CREATE TABLE packages (
                relative_path TEXT PRIMARY KEY,
                bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                package_version TEXT,
                engine INTEGER,
                names INTEGER,
                exports INTEGER,
                imports INTEGER,
                game INTEGER,
                listed_objects INTEGER NOT NULL DEFAULT 0,
                warning_lines INTEGER NOT NULL DEFAULT 0,
                error_lines INTEGER NOT NULL DEFAULT 0,
                list_status TEXT NOT NULL DEFAULT 'not_listed'
            )"""
        )
        db.execute(
            """CREATE TABLE objects (
                relative_path TEXT NOT NULL,
                export_index INTEGER NOT NULL,
                package_offset INTEGER NOT NULL,
                export_size INTEGER NOT NULL,
                object_class TEXT NOT NULL,
                object_name TEXT NOT NULL,
                PRIMARY KEY (relative_path, export_index)
            )"""
        )
        db.execute("CREATE INDEX objects_by_name ON objects(object_name COLLATE NOCASE)")
        db.execute("CREATE INDEX objects_by_class ON objects(object_class COLLATE NOCASE)")
        db.execute("CREATE INDEX objects_by_package ON objects(relative_path)")

        for path, row in expected.items():
            info = pkginfo_rows[path]
            db.execute(
                """INSERT INTO packages
                (relative_path, bytes, sha256, package_version, engine, names,
                 exports, imports, game, warning_lines, error_lines)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["relative_path"].replace("\\", "/"),
                    int(row["bytes"]),
                    row["sha256"],
                    info["package_version"],
                    int(info["engine"]),
                    int(info["names"]),
                    int(info["exports"]),
                    int(info["imports"]),
                    int(info["game"]),
                    int(info["warning_lines"]),
                    int(info["error_lines"]),
                ),
            )
        db.commit()

        for relative_folder in FOLDERS:
            folder = game_root / Path(relative_folder)
            prefix = relative_folder.replace("\\", "/").rstrip("/") + "/"
            if not folder.is_dir():
                raise FileNotFoundError(f"package directory not found: {folder}")
            proc = subprocess.Popen(
                [str(umodel), "-game=dis", f"-path={folder}", "-list", "*.upk"],
                cwd=folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            current_path: str | None = None
            current_count = 0
            batch: list[tuple[object, ...]] = []
            warnings: Counter[str] = Counter()
            errors: Counter[str] = Counter()

            def finish_current() -> None:
                nonlocal current_path, current_count
                if current_path is None:
                    return
                info = pkginfo_rows.get(current_path.casefold())
                expected_count = int(info["exports"]) if info else -1
                status = "count_match" if current_count == expected_count else "count_mismatch"
                db.execute(
                    """UPDATE packages
                       SET listed_objects=?, list_status=?, warning_lines=?, error_lines=?
                       WHERE relative_path=?""",
                    (
                        current_count,
                        status,
                        warnings[current_path.casefold()],
                        errors[current_path.casefold()],
                        current_path,
                    ),
                )
                package_statuses[status] += 1
                nonlocal package_rows
                package_rows += 1
                if package_rows % 50 == 0:
                    db.commit()
                    print(
                        f"catalogued packages={package_rows}/{len(expected)} objects={object_rows}",
                        flush=True,
                    )

            assert proc.stdout is not None
            for line in proc.stdout:
                summary = SUMMARY_RE.search(line)
                if summary:
                    # Wildcard mode prints all package summaries before the
                    # per-package object-list headings. The latter define
                    # the object stream boundaries.
                    continue

                package_header = PACKAGE_HEADER_RE.match(line.rstrip("\r\n"))
                if package_header:
                    finish_current()
                    current_path = f"{prefix}{package_header.group(1)}"
                    current_count = 0
                    continue

                warning = WARNING_RE.search(line)
                if warning:
                    warnings[f"{prefix}{warning.group(1)}".casefold()] += 1
                    continue
                error = ERROR_RE.search(line)
                if error:
                    errors[f"{prefix}{error.group(1)}".casefold()] += 1
                    continue

                if current_path is None:
                    continue
                item = OBJECT_RE.match(line)
                if not item:
                    continue
                export_index, offset, size, label = item.groups()
                object_class, _, object_name = label.partition(" ")
                if not object_name:
                    object_name = object_class
                batch.append(
                    (
                        current_path,
                        int(export_index),
                        int(offset, 16),
                        int(size, 16),
                        object_class,
                        object_name,
                    )
                )
                current_count += 1
                object_rows += 1
                if len(batch) >= 10_000:
                    db.executemany(
                        "INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?)", batch
                    )
                    batch.clear()
                    db.commit()
            finish_current()
            return_code = proc.wait()
            if batch:
                db.executemany("INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?)", batch)
                batch.clear()
            db.commit()
            if return_code != 0:
                raise RuntimeError(
                    f"UModel -list failed for {folder}: exit {return_code}"
                )

        db.commit()
        missing = db.execute(
            "SELECT relative_path FROM packages WHERE list_status='not_listed'"
        ).fetchall()
        db.close()
        if missing:
            raise RuntimeError(
                f"{len(missing)} packages had no UModel -list summary; "
                f"sample={missing[:10]}"
            )
        os.replace(temp_db, output)
    except Exception:
        if db is not None:
            db.close()
        if temp_db.exists():
            temp_db.unlink()
        raise

    print(f"Packages listed: {package_rows}/{len(expected)}")
    print(f"Object rows: {object_rows}")
    print(f"Package export-count checks: {dict(sorted(package_statuses.items()))}")
    print(f"SQLite catalog: {output}")


if __name__ == "__main__":
    main()
