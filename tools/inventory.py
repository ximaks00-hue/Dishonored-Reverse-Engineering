#!/usr/bin/env python3
"""Create a deterministic metadata-only inventory for a local game installation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def digest_file(path: Path, root: Path) -> tuple[str, int, str]:
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            hasher.update(chunk)
            size += len(chunk)
    return path.relative_to(root).as_posix(), size, hasher.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="root of the local game installation")
    parser.add_argument("output", type=Path, help="CSV output path")
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    args = parser.parse_args()

    root = args.root.resolve(strict=True)
    if not root.is_dir():
        parser.error(f"installation root is not a directory: {root}")
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    files = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda p: p.as_posix().casefold())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("relative_path", "bytes", "sha256"))
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for record in pool.map(lambda path: digest_file(path, root), files):
                writer.writerow(record)

    total_bytes = sum(path.stat().st_size for path in files)
    print(f"Files: {len(files)}")
    print(f"Bytes: {total_bytes}")
    print(f"Manifest: {args.output.resolve()}")


if __name__ == "__main__":
    main()
