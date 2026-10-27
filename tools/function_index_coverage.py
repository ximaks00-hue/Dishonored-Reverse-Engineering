"""Summarize nameability and size buckets in the reconciled Ghidra function index."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter
from pathlib import Path


AUTO = re.compile(r"^FUN_[0-9A-Fa-f]+$")
THUNK_AUTO = re.compile(r"^thunk_FUN_[0-9A-Fa-f]+$")
SIZE_BUCKETS = ((0, 16), (17, 32), (33, 64), (65, 128), (129, 256), (257, 512), (513, 1024), (1025, None))


def summarize(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    names = [row["name"] for row in rows]
    sizes = [int(row["size"]) for row in rows]
    duplicate_names = {name: count for name, count in Counter(names).items() if count > 1}

    buckets = []
    for lower, upper in SIZE_BUCKETS:
        count = sum(size >= lower and (upper is None or size <= upper) for size in sizes)
        buckets.append({"range": f"{lower}+" if upper is None else f"{lower}-{upper}", "count": count})

    auto_count = sum(bool(AUTO.fullmatch(name)) for name in names)
    thunk_auto_count = sum(bool(THUNK_AUTO.fullmatch(name)) for name in names)
    return {
        "input": str(path),
        "rows": len(rows),
        "unique_addresses": len({row["address"].casefold() for row in rows}),
        "name_classes": {
            "FUN_address": auto_count,
            "thunk_FUN_address": thunk_auto_count,
            "other_names": len(rows) - auto_count - thunk_auto_count,
        },
        "unique_names": len(set(names)),
        "duplicate_name_values": len(duplicate_names),
        "rows_beyond_unique_name_count": len(rows) - len(set(names)),
        "top_duplicate_names": sorted(duplicate_names.items(), key=lambda pair: (-pair[1], pair[0]))[:20],
        "size_bytes": {
            "min": min(sizes),
            "median": statistics.median(sizes),
            "mean": statistics.mean(sizes),
            "max": max(sizes),
            "buckets": buckets,
        },
        "limits": [
            "Function names and lengths are index labels only; they do not establish subsystem, semantic review, or decompilation coverage.",
            "The input index covers internal functions; external-function accounting is recorded separately in EXP-0041.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("research/executable/functions.csv"),
        help="Reconciled internal-function index CSV.",
    )
    args = parser.parse_args()
    path = args.input.resolve(strict=True)
    print(json.dumps(summarize(path), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
