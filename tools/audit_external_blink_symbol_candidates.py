#!/usr/bin/env python3
"""Crosswalk PDB-donor Blink method comments to the retail index without renaming it."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


COMMENT_RE = re.compile(r"^\s*//\s+0x(?P<rva>[0-9a-fA-F]+)\s+(?P<signature>.+?)\s*$")
IMAGE_BASE = 0x400000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def address(value: str) -> int:
    return int(value, 16)


def run(args: argparse.Namespace) -> dict[str, object]:
    matches = read_csv(args.matches)
    local_rows = read_csv(args.local_index)
    by_old_rva = {
        address(row["rva_2012"]): row
        for row in matches
        if row.get("rva_2012") and row.get("kind", "function") == "function"
    }
    local_by_address = {address(row["address"]): row for row in local_rows}
    intervals = sorted(
        (address(row["body_start"]), address(row["body_end"]), row)
        for row in local_rows
        if row.get("body_start") and row.get("body_end")
    )

    output: list[dict[str, str]] = []
    for line_number, line in enumerate(args.stub.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        comment = COMMENT_RE.match(line)
        if not comment:
            continue
        old_rva = int(comment.group("rva"), 16)
        match = by_old_rva.get(old_rva)
        new_rva = address(match["rva_2013"]) if match and match.get("rva_2013") else None
        va = new_rva + IMAGE_BASE if new_rva is not None else None
        local = local_by_address.get(va) if va is not None else None
        containing = next((row for lo, hi, row in intervals if lo <= va <= hi), None) if va is not None else None
        if not match or new_rva is None:
            status = "unmatched_in_2013_symbol_match"
        elif local:
            status = "local_index_entry"
        elif containing:
            status = "inside_local_indexed_body"
        else:
            status = "absent_from_local_index"
        output.append({
            "source_line": str(line_number),
            "rva_2012": f"0x{old_rva:06X}",
            "signature_from_2012_pdb_comment": comment.group("signature"),
            "rva_2013": f"0x{new_rva:06X}" if new_rva is not None else "",
            "va_2013": f"0x{va:08X}" if va is not None else "",
            "match_method": match.get("method", "") if match else "",
            "match_ratio": match.get("ratio", "") if match else "",
            "size_2012": match.get("size_2012", "") if match else "",
            "size_2013": match.get("size_2013", "") if match else "",
            "name_2013": match.get("name_2013", "") if match else "",
            "local_index_status": status,
            "local_function_name": local.get("name", "") if local else "",
            "local_function_size": local.get("size", "") if local else "",
            "containing_function_address": containing.get("address", "") if containing and not local else "",
        })

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]) if output else [])
        writer.writeheader()
        writer.writerows(output)

    counts: dict[str, int] = {}
    for row in output:
        counts[row["local_index_status"]] = counts.get(row["local_index_status"], 0) + 1
    metadata = {
        "schema_version": "1.0",
        "source": "PDB-attributed comments in a recompiled-project stub; comments carry 2012 RVAs.",
        "inputs": {
            "stub": {"path": str(args.stub), "sha256": sha256(args.stub)},
            "match_2012_2013": {"path": str(args.matches), "sha256": sha256(args.matches)},
            "local_function_index": {"path": str(args.local_index), "sha256": sha256(args.local_index), "rows": len(local_rows)},
        },
        "output_csv": str(args.output_csv),
        "rows": len(output),
        "local_index_status_counts": counts,
        "method_counts": {key: sum(row["match_method"] == key for row in output) for key in sorted({row["match_method"] for row in output})},
        "limits": [
            "The stub is an import-generated placeholder, not original Dishonored source; its comments identify 2012 PDB functions.",
            "The 2012-to-2013 name/address transfer is a candidate association; its method and ratio are preserved per row.",
            "This audit does not decompile functions, assign names in Ghidra, or establish runtime behavior.",
            "The retail Ghidra index is checked only by exact VA start and indexed body interval.",
        ],
    }
    args.output_json.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stub", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--local-index", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args)
    except (KeyError, OSError, ValueError, csv.Error) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"rows": result["rows"], "local_index_status_counts": result["local_index_status_counts"], "method_counts": result["method_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
