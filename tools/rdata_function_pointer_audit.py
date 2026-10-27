"""Audit raw .rdata DWORDs at data-xref sites targeting no-call-edge functions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import struct
from collections import defaultdict
from pathlib import Path

from callgraph_coverage import ROOT, read_build_identity


def audit(callgraph_path: Path, functions_path: Path, exe_path: Path) -> dict[str, object]:
    expected_build, expected_hash = read_build_identity()
    image = exe_path.read_bytes()
    actual_hash = hashlib.sha256(image).hexdigest().upper()
    if actual_hash != expected_hash:
        raise ValueError("EXE SHA-256 does not match BUILD-STEAM-10256413")

    with functions_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = {row["address"].strip().upper(): row for row in csv.DictReader(stream)}
    functions = set(rows)
    with sqlite3.connect(callgraph_path) as db:
        metadata = dict(db.execute("SELECT key, value FROM meta"))
        if metadata.get("build_id") != expected_build or metadata.get("exe_sha256", "").upper() != expected_hash:
            raise ValueError("Callgraph metadata does not match BUILD-STEAM-10256413")
        callers = {a for (a,) in db.execute("SELECT DISTINCT from_addr FROM edges WHERE kind='call'")} & functions
        targets = {a for (a,) in db.execute("SELECT DISTINCT to_addr FROM edges WHERE kind='call'")} & functions
        no_call = functions - callers - targets
        data_edges = db.execute("SELECT to_addr, site_addr FROM edges WHERE kind='data'").fetchall()

    pe_offset = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("Invalid PE signature")
    section_count = struct.unpack_from("<H", image, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe_offset + 20)[0]
    optional = pe_offset + 24
    if struct.unpack_from("<H", image, optional)[0] != 0x10B:
        raise ValueError("Expected PE32 x86 optional header")
    image_base = struct.unpack_from("<I", image, optional + 28)[0]
    table = optional + optional_size
    rdata: tuple[int, int, int, int] | None = None
    for index in range(section_count):
        offset = table + index * 40
        name = image[offset : offset + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        if name != ".rdata":
            continue
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from("<IIII", image, offset + 8)
        start = image_base + virtual_address
        end = start + max(virtual_size, raw_size)
        rdata = (start, end, image_base + virtual_address, raw_pointer)
        break
    if rdata is None:
        raise ValueError("PE .rdata section not found")

    start, end, rdata_va, raw_pointer = rdata
    sites: dict[int, set[str]] = defaultdict(set)
    candidate_edges = 0
    for target, site in data_edges:
        target = target.upper()
        if target not in no_call:
            continue
        try:
            site_va = int(site, 16)
        except ValueError:
            continue
        if start <= site_va < end:
            sites[site_va].add(target)
            candidate_edges += 1

    va_matches: set[int] = set()
    rva_matches: list[dict[str, object]] = []
    mismatches: list[dict[str, object]] = []
    for site_va, site_targets in sites.items():
        file_offset = raw_pointer + (site_va - rdata_va)
        if file_offset < 0 or file_offset + 4 > len(image):
            raise ValueError(f"Source site is outside file-backed .rdata: 0x{site_va:08X}")
        stored_dword = struct.unpack_from("<I", image, file_offset)[0]
        if len(site_targets) == 1 and stored_dword == int(next(iter(site_targets)), 16):
            va_matches.add(site_va)
        elif len(site_targets) == 1 and stored_dword == int(next(iter(site_targets)), 16) - image_base:
            target = next(iter(site_targets))
            rva_matches.append(
                {
                    "site_va": f"0x{site_va:08X}",
                    "stored_dword": f"0x{stored_dword:08X}",
                    "target_va": f"0x{int(target, 16):08X}",
                    "target_name": rows[target]["name"],
                }
            )
        else:
            mismatches.append(
                {
                    "site_va": f"0x{site_va:08X}",
                    "stored_dword": f"0x{stored_dword:08X}",
                    "target_addresses": sorted(f"0x{int(target, 16):08X}" for target in site_targets),
                    "target_names": sorted(rows[target]["name"] for target in site_targets),
                }
            )

    runs: list[list[int]] = []
    for site_va in sorted(va_matches):
        if site_va - 4 not in va_matches:
            runs.append([site_va])
        else:
            runs[-1].append(site_va)
    long_runs = [run for run in runs if len(run) >= 3]
    longest = max(long_runs, key=len) if long_runs else []
    return {
        "build_id": metadata["build_id"],
        "exe_sha256": actual_hash,
        "image_base": f"0x{image_base:08X}",
        "no_call_edge_functions": len(no_call),
        "rdata_data_xref_edges": candidate_edges,
        "unique_rdata_sites": len(sites),
        "sites_with_multiple_no_call_targets": sum(len(values) > 1 for values in sites.values()),
        "stored_dword_equals_target_va": len(va_matches),
        "stored_dword_equals_target_rva": len(rva_matches),
        "other_mismatched_sites": len(mismatches),
        "contiguous_matching_pointer_runs_at_least_3": len(long_runs),
        "longest_matching_pointer_run_entries": len(longest),
        "longest_matching_pointer_run_start": f"0x{longest[0]:08X}" if longest else None,
        "rva_matching_sites": sorted(rva_matches, key=lambda item: item["site_va"]),
        "other_mismatched_sites_detail": sorted(mismatches, key=lambda item: item["site_va"]),
        "limits": [
            "A stored DWORD equal to a function VA or RVA confirms a raw address value at that source site, not its data-structure type.",
            "Contiguous pointer runs are candidates for table/array inspection; they are not classified as vtables by this script.",
            "This audit is limited to non-call data-xref sites in .rdata targeting functions absent from both direct-call roles.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--callgraph", type=Path, default=ROOT / "knowledge" / "database" / "callgraph.sqlite")
    parser.add_argument("--functions", type=Path, default=ROOT / "research" / "executable" / "functions.csv")
    parser.add_argument("--exe", type=Path, default=ROOT / "Dishonored RHCP" / "Binaries" / "Win32" / "Dishonored.exe")
    args = parser.parse_args()
    print(json.dumps(audit(args.callgraph.resolve(strict=True), args.functions.resolve(strict=True), args.exe.resolve(strict=True)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
