"""Summarize exact-build call/data-edge coverage against functions.csv."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import re
import sqlite3
import struct
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_RECORD = ROOT / "research" / "builds" / "BUILD-STEAM-10256413" / "build.md"
ADDRESS_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
AUTO = re.compile(r"^FUN_[0-9A-Fa-f]+$")
THUNK_AUTO = re.compile(r"^thunk_FUN_[0-9A-Fa-f]+$")


def read_build_identity() -> tuple[str, str]:
    text = BUILD_RECORD.read_text(encoding="utf-8")
    build_match = re.search(r"Build ID:\s*`?(\d+)`?", text, re.IGNORECASE)
    hash_match = re.search(r"Executable SHA-256:\s*`([0-9A-Fa-f]{64})`", text)
    if not build_match or not hash_match:
        raise ValueError(f"Could not parse build ID/hash from {BUILD_RECORD}")
    return build_match.group(1), hash_match.group(1).upper()


def read_pe_sections(exe_path: Path) -> tuple[int, list[tuple[str, int, int]]]:
    image = exe_path.read_bytes()
    if hashlib.sha256(image).hexdigest().upper() != read_build_identity()[1]:
        raise ValueError("EXE SHA-256 does not match BUILD-STEAM-10256413")
    pe_offset = struct.unpack_from("<I", image, 0x3C)[0]
    if image[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("Invalid PE signature")
    section_count = struct.unpack_from("<H", image, pe_offset + 6)[0]
    optional_size = struct.unpack_from("<H", image, pe_offset + 20)[0]
    optional_offset = pe_offset + 24
    magic = struct.unpack_from("<H", image, optional_offset)[0]
    if magic == 0x10B:
        image_base = struct.unpack_from("<I", image, optional_offset + 28)[0]
    elif magic == 0x20B:
        image_base = struct.unpack_from("<Q", image, optional_offset + 24)[0]
    else:
        raise ValueError(f"Unsupported PE optional-header magic: 0x{magic:04X}")
    table_offset = optional_offset + optional_size
    sections = []
    for index in range(section_count):
        offset = table_offset + index * 40
        name = image[offset : offset + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        virtual_size, virtual_address, raw_size = struct.unpack_from("<III", image, offset + 8)
        start = image_base + virtual_address
        end = start + max(virtual_size, raw_size)
        sections.append((name, start, end))
    return image_base, sections


def summarize(callgraph_path: Path, functions_path: Path, exe_path: Path) -> dict[str, object]:
    with functions_path.open(newline="", encoding="utf-8-sig") as stream:
        function_rows = {row["address"].strip().upper(): row for row in csv.DictReader(stream)}
    function_addresses = set(function_rows)
    if not function_addresses or not all(ADDRESS_RE.fullmatch(address) for address in function_addresses):
        raise ValueError("Function index contains empty or non-image addresses")

    expected_build, expected_hash = read_build_identity()
    image_base, pe_sections = read_pe_sections(exe_path)
    with sqlite3.connect(callgraph_path) as db:
        meta = dict(db.execute("SELECT key, value FROM meta"))
        if meta.get("build_id") != expected_build or meta.get("exe_sha256", "").upper() != expected_hash:
            raise ValueError("Callgraph metadata does not match BUILD-STEAM-10256413")
        edge_counts = dict(db.execute("SELECT kind, COUNT(*) FROM edges GROUP BY kind"))
        all_edges = db.execute("SELECT kind, from_addr, to_addr, site_addr FROM edges").fetchall()

    source_path = Path(meta.get("source_csv", ""))
    if source_path and not source_path.is_absolute():
        source_path = (ROOT / source_path).resolve()
    source_kind_counts: Counter[str] = Counter()
    source_rows = 0
    source_present = source_path.is_file()
    if source_present:
        with source_path.open(newline="", encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream):
                source_rows += 1
                source_kind_counts[row["kind"].strip().lower()] += 1
        if source_rows != len(all_edges) or dict(source_kind_counts) != edge_counts:
            raise ValueError("Callgraph SQLite rows disagree with the recorded source CSV")

    result: dict[str, object] = {
        "build_id": meta["build_id"],
        "exe_sha256": meta["exe_sha256"],
        "exported_at": meta.get("exported_at", ""),
        "source_csv": str(source_path),
        "source_csv_present_and_count_matched": source_present,
        "function_index_rows": len(function_addresses),
        "callgraph_edges": {},
        "limitations": [
            "Direct call references and incoming non-call data xrefs are separate edge kinds.",
            "An absent call edge does not mean the function is unreachable, unused, or semantically reviewed.",
            "Data-edge sources can be instruction/data addresses rather than function entries.",
            "An incoming data xref to a function entry does not identify a vtable slot, function pointer, or dynamic call.",
            "Edge presence does not prove dynamic execution or complete indirect-call coverage.",
        ],
    }

    role_sets: dict[str, set[str]] = {}
    for kind in ("call", "data"):
        edges = [(a.upper(), b.upper()) for edge_kind, a, b, _site in all_edges if edge_kind == kind]
        sources = {a for a, _ in edges}
        targets = {b for _, b in edges}
        internal_sources = sources & function_addresses
        internal_targets = targets & function_addresses
        internal_any = internal_sources | internal_targets
        summary: dict[str, object] = {
            "edge_count": len(edges),
            "distinct_internal_sources": len(internal_sources),
            "distinct_internal_targets": len(internal_targets),
            "distinct_internal_functions_either_end": len(internal_any),
            "internal_functions_without_this_edge_kind": len(function_addresses - internal_any),
            "distinct_non_index_sources": len(sources - function_addresses),
            "distinct_non_index_targets": len(targets - function_addresses),
        }
        if kind == "call":
            role_sets = {"sources": internal_sources, "targets": internal_targets}
            summary["internal_to_internal_edges"] = sum(a in function_addresses and b in function_addresses for a, b in edges)
            summary["internal_to_non_index_edges"] = sum(a in function_addresses and b not in function_addresses for a, b in edges)
            summary["non_index_to_internal_edges"] = sum(a not in function_addresses and b in function_addresses for a, b in edges)
        else:
            role_sets["data_targets"] = internal_targets
        result["callgraph_edges"][kind] = summary  # type: ignore[index]

    caller_set = role_sets["sources"]
    target_set = role_sets["targets"]
    data_target_set = role_sets["data_targets"]
    role_partition = {
        "both": caller_set & target_set,
        "caller_only": caller_set - target_set,
        "target_only": target_set - caller_set,
        "neither": function_addresses - caller_set - target_set,
    }
    result["call_role_partition"] = {}
    for role, addresses in role_partition.items():
        names = [function_rows[address]["name"] for address in addresses]
        sizes = [int(function_rows[address]["size"]) for address in addresses]
        auto_count = sum(bool(AUTO.fullmatch(name)) for name in names)
        thunk_count = sum(bool(THUNK_AUTO.fullmatch(name)) for name in names)
        result["call_role_partition"][role] = {
            "count": len(addresses),
            "FUN_address_names": auto_count,
            "thunk_FUN_address_names": thunk_count,
            "other_names": len(addresses) - auto_count - thunk_count,
            "median_size_bytes": statistics.median(sizes) if sizes else None,
            "max_size_bytes": max(sizes) if sizes else None,
            "also_targeted_by_data_xref": len(addresses & data_target_set),
            "without_data_xref_to_entry": len(addresses - data_target_set),
        }  # type: ignore[index]

    no_call_functions = role_partition["neither"]
    section_edges: Counter[str] = Counter()
    section_targets: dict[str, set[str]] = {}
    for edge_kind, _source, target, site in all_edges:
        if edge_kind != "data":
            continue
        target = target.upper()
        if target not in no_call_functions:
            continue
        try:
            site_address = int(site, 16)
        except ValueError:
            section_name = "symbolic"
        else:
            section_name = next(
                (name for name, start, end in pe_sections if start <= site_address < end),
                "outside_image",
            )
        section_edges[section_name] += 1
        section_targets.setdefault(section_name, set()).add(target)
    result["exe_image_base"] = f"0x{image_base:08X}"
    result["no_call_data_xrefs_by_source_section"] = {
        name: {"edge_count": section_edges[name], "distinct_no_call_targets": len(targets)}
        for name, targets in sorted(section_targets.items(), key=lambda item: (-section_edges[item[0]], item[0]))
    }
    result["no_call_data_xref_edges"] = sum(section_edges.values())

    if source_present and source_rows != sum(edge_counts.values()):
        raise ValueError("Unexpected source-row count mismatch")
    result["edge_kind_counts"] = edge_counts
    result["source_csv_rows"] = source_rows if source_present else None
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--callgraph", type=Path, default=ROOT / "knowledge" / "database" / "callgraph.sqlite")
    parser.add_argument("--functions", type=Path, default=ROOT / "research" / "executable" / "functions.csv")
    parser.add_argument("--exe", type=Path, default=ROOT / "Dishonored RHCP" / "Binaries" / "Win32" / "Dishonored.exe")
    args = parser.parse_args()
    print(json.dumps(summarize(args.callgraph.resolve(strict=True), args.functions.resolve(strict=True), args.exe.resolve(strict=True)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
