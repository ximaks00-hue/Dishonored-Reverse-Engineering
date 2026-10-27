#!/usr/bin/env python3
"""Record small headers for selected non-UPK media/cache files.

Reads only the configured prefix from each selected file. A matching magic
value is a signature observation, not evidence of full format compatibility.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path, PurePosixPath

DEFAULT_EXTENSIONS = {".pck", ".bnk", ".akmap", ".bik", ".tfc"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--header-bytes", type=int, default=16)
    args = parser.parse_args()
    if args.header_bytes < 4:
        parser.error("--header-bytes must be at least 4")

    root = args.game_root.resolve(strict=True)
    with args.manifest.resolve(strict=True).open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    selected = [
        row for row in manifest
        if PurePosixPath(row["relative_path"].replace("\\", "/")).suffix.casefold() in DEFAULT_EXTENSIONS
    ]
    rows: list[dict[str, object]] = []
    signatures: Counter[tuple[str, str]] = Counter()
    for item in selected:
        relative = item["relative_path"].replace("\\", "/")
        path = root.joinpath(*PurePosixPath(relative).parts)
        exists = path.is_file()
        observed_size = path.stat().st_size if exists else ""
        if exists:
            with path.open("rb") as file_stream:
                header = file_stream.read(args.header_bytes)
        else:
            header = b""
        extension = PurePosixPath(relative).suffix.casefold()
        signature = header[:4].hex().upper() if header else ""
        signatures[(extension, signature)] += 1
        rows.append({
            "relative_path": relative,
            "extension": extension,
            "manifest_bytes": int(item["bytes"]),
            "exists": exists,
            "observed_bytes": observed_size,
            "size_match": observed_size == int(item["bytes"]) if exists else False,
            "header_bytes_read": len(header),
            "first_4_bytes_hex": signature,
            "header_hex": header.hex().upper(),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    print(f"Manifest candidates: {len(selected)}")
    print(f"Present: {sum(bool(row['exists']) for row in rows)}")
    print(f"Size matched: {sum(bool(row['size_match']) for row in rows)}")
    print(f"Signatures by extension: {dict(sorted(signatures.items()))}")
    print(f"Header census: {args.output.resolve()}")


if __name__ == "__main__":
    main()
