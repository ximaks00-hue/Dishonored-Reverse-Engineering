#!/usr/bin/env python3
"""Join one exact-build native class/table registration body to UELib class labels.

This is a name/metadata join only. It does not validate runtime use or native
table dispatch semantics.
"""

from __future__ import annotations

import csv
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_ID = "10256413"
EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
CACHE = ROOT / "knowledge/cache/decompiles/00A0DBF0.json"
CLASS_CATALOG = ROOT / "research/packages/uelib-object-initialization/uelib-class-object-catalog.csv.gz"
OUTPUT = ROOT / "research/executable/evidence/EXP-0076-native-class-table-uelib-join.csv"


def main() -> None:
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    if cache.get("build_id") != BUILD_ID or cache.get("exe_sha256", "").upper() != EXE_SHA256:
        raise SystemExit("decompiler cache build identity does not match the selected build")
    body = cache["pseudocode"]

    keys = list(re.finditer(r'FUN_00454fe0\("([^"]+)",1\)', body))
    pointers = list(re.finditer(r"PTR_s_([^;\n]+)", body))
    if not keys or len(keys) != len(pointers):
        raise SystemExit(f"unpaired key/pointer expression counts: {len(keys)} / {len(pointers)}")
    # In this body both expression streams preserve registration order and each
    # paired expression is within 62 characters in the decompiler text.
    pairs = []
    for key, pointer in zip(keys, pointers):
        if abs(key.start() - pointer.start()) > 100:
            raise SystemExit("key/pointer pair exceeded local adjacency bound")
        pairs.append((key.group(1), pointer.group(1)))
    if len({key for key, _ in pairs}) != len(pairs):
        raise SystemExit("duplicate class key found; output schema expects unique keys")

    class_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    with gzip.open(CLASS_CATALOG, "rt", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            label = row["export_or_import_class_label"]
            if row["class_path"].startswith("Class'"):
                class_rows[label].append(row)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "build_id", "exe_sha256", "registration_address", "class_key",
        "table_pointer_symbol", "table_pointer_symbol_address",
        "uelib_class_path", "uelib_class_rows", "uelib_distinct_packages",
        "sample_packages", "claim",
    ]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for key, pointer in pairs:
            rows = class_rows.get(key, [])
            class_paths = sorted({row["class_path"] for row in rows})
            packages = sorted({row["package"] for row in rows})
            writer.writerow({
                "build_id": BUILD_ID,
                "exe_sha256": EXE_SHA256,
                "registration_address": "00A0DBF0",
                "class_key": key,
                "table_pointer_symbol": "PTR_s_" + pointer,
                "table_pointer_symbol_address": pointer.rsplit("_", 1)[-1],
                "uelib_class_path": " | ".join(class_paths),
                "uelib_class_rows": len(rows),
                "uelib_distinct_packages": len(packages),
                "sample_packages": " | ".join(packages[:5]),
                "claim": "exact label join across static decompiler and UELib parser catalogs; runtime use unproved" if rows else "no exact class-path row in UELib catalog",
            })
    print(f"wrote {len(pairs)} rows: {OUTPUT.relative_to(ROOT)}")
    print(f"exact Class-path joins: {sum(bool(class_rows.get(key)) for key, _ in pairs)} / {len(pairs)}")


if __name__ == "__main__":
    main()
