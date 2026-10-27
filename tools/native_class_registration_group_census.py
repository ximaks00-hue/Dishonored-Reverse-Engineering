#!/usr/bin/env python3
"""Join exact-build class/table key pairs from selected registration bodies to UELib classes.

The extraction recognizes only explicit decompiler expression patterns and
reports exact class-label matches. It does not establish runtime registration,
table layout, token dispatch, or that every class method has been recovered.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_ID = "10256413"
EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
CACHE_DIR = ROOT / "knowledge/cache/decompiles"
CLASS_CATALOG = ROOT / "research/packages/uelib-object-initialization/uelib-class-object-catalog.csv.gz"
OUTPUT_DIR = ROOT / "research/executable/evidence"
GROUPS = {
    "006067A0": (
        "FUN_00454fe0",
        "FUN_0044c310",
        re.compile(
            r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
            r'(?P<keyvar>\w+)\s*=\s*FUN_00454fe0\("(?P<key>[^"]+)",1\);\s*'
            r'FUN_0044c310\(\s*(?P=keyvar)\s*,\s*(?P=ptrvar)\s*\)', re.I),
    ),
    "0096DAB0": (
        "FUN_00454fe0",
        "FUN_00b699e0",
        re.compile(
            r'(?P<keyvar>\w+)\s*=\s*FUN_00454fe0\("(?P<key>[^"]+)",1\);\s*'
            r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
            r'FUN_00b699e0\([^;\n]*&\s*(?P=keyvar)\s*,\s*0\s*\)', re.I),
    ),
    "00970A10": (
        "FUN_00454fe0", "FUN_00b699e0", None,
    ),
    "0099A100": (
        "FUN_00454fe0", "FUN_00b699e0", None,
    ),
    "009AE330": (
        "FUN_00454fe0", "FUN_00b699e0", None,
    ),
    "00A0DBF0": (
        "FUN_00454fe0", "mixed", None,
    ),
    "004811B0": (
        "FUN_00449a10", "FUN_00b699e0", None,
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load_cache(address: str) -> tuple[dict[str, object], str]:
    path = CACHE_DIR / f"{address}.json"
    data = path.read_bytes()
    cache = json.loads(data)
    if cache.get("build_id") != BUILD_ID or cache.get("exe_sha256", "").upper() != EXE_SHA256:
        raise SystemExit(f"decompiler cache identity mismatch: {address}")
    return cache, sha256_bytes(data)


def extracted_pairs(address: str, body: str) -> list[dict[str, str]]:
    if address == "00A0DBF0":
        patterns = [
            ("FUN_00b699e0", re.compile(
                r'(?P<keyvar>\w+)\s*=\s*FUN_00454fe0\("(?P<key>[^"]+)",1\);\s*'
                r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
                r'FUN_00b699e0\([^;\n]*&\s*(?P=keyvar)\s*,\s*0\s*\)', re.I)),
            ("FUN_0044c310", re.compile(
                r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
                r'(?P<keyvar>\w+)\s*=\s*FUN_00454fe0\("(?P<key>[^"]+)",1\);\s*'
                r'FUN_0044c310\(\s*(?P=keyvar)\s*,\s*(?P=ptrvar)\s*\)', re.I)),
        ]
    elif address == "004811B0":
        patterns = [("FUN_00b699e0", re.compile(
            r'FUN_00449a10\("(?P<key>[^"]+)",0,1\);\s*'
            r'(?P<keyvar>\w+)\s*=\s*[^;\n]+;\s*'
            r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
            r'FUN_00b699e0\([^;\n]*&\s*(?P=keyvar)\s*,\s*0\s*\)', re.I))]
    else:
        factory, helper, pattern = GROUPS[address]
        if pattern is None:
            if helper == "FUN_0044c310":
                pattern = re.compile(
                    r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
                    r'(?P<keyvar>\w+)\s*=\s*FUN_00454fe0\("(?P<key>[^"]+)",1\);\s*'
                    r'FUN_0044c310\(\s*(?P=keyvar)\s*,\s*(?P=ptrvar)\s*\)', re.I)
            else:
                pattern = re.compile(
                    r'(?P<keyvar>\w+)\s*=\s*FUN_00454fe0\("(?P<key>[^"]+)",1\);\s*'
                    r'(?P<ptrvar>\w+)\s*=\s*&PTR_s_(?P<symbol>[^;\n]+);\s*'
                    r'FUN_00b699e0\([^;\n]*&\s*(?P=keyvar)\s*,\s*0\s*\)', re.I)
        patterns = [(helper, pattern)]

    rows: list[dict[str, str]] = []
    for helper, pattern in patterns:
        for match in pattern.finditer(body):
            rows.append({
                "registration_address": address,
                "class_key_constructor": GROUPS[address][0],
                "registration_helper": helper,
                "class_key": match.group("key"),
                "table_pointer_symbol": "PTR_s_" + match.group("symbol"),
                "table_pointer_symbol_address": match.group("symbol").rsplit("_", 1)[-1],
                "body_offset": str(match.start()),
            })
    rows.sort(key=lambda row: int(row["body_offset"]))
    if len({row["body_offset"] for row in rows}) != len(rows):
        raise SystemExit(f"overlapping extraction patterns: {address}")
    if len({row["class_key"] for row in rows}) != len(rows):
        raise SystemExit(f"duplicate class key within registration body: {address}")
    return rows


def main() -> None:
    class_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    with gzip.open(CLASS_CATALOG, "rt", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["class_path"].startswith("Class'"):
                class_rows[row["export_or_import_class_label"]].append(row)

    all_rows: list[dict[str, object]] = []
    all_matched_packages: set[str] = set()
    cache_hashes: dict[str, str] = {}
    group_summary: dict[str, dict[str, object]] = {}
    for address in GROUPS:
        cache, cache_hash = load_cache(address)
        cache_hashes[address] = cache_hash
        body = str(cache["pseudocode"])
        pairs = extracted_pairs(address, body)
        for pair in pairs:
            matched = class_rows.get(pair["class_key"], [])
            class_paths = sorted({row["class_path"] for row in matched})
            packages = sorted({row["package"] for row in matched})
            all_matched_packages.update(packages)
            all_rows.append({
                "build_id": BUILD_ID,
                "exe_sha256": EXE_SHA256,
                "registration_address": pair["registration_address"],
                "registration_cache_sha256": cache_hash,
                "registration_body_sha256": sha256_bytes(body.encode("utf-8")),
                "class_key_constructor": pair["class_key_constructor"],
                "registration_helper": pair["registration_helper"],
                "class_key": pair["class_key"],
                "table_pointer_symbol": pair["table_pointer_symbol"],
                "table_pointer_symbol_address": pair["table_pointer_symbol_address"],
                "uelib_class_paths": " | ".join(class_paths),
                "uelib_class_catalog_rows": len(matched),
                "uelib_distinct_packages": len(packages),
                "sample_uelib_packages": " | ".join(packages[:8]),
                "claim": "observed exact decompiler-key to UELib Class-path label join; runtime use and table semantics unknown" if matched else "no exact Class-path label row in UELib catalog",
            })
        group_summary[address] = {
            "decompiler_cache_sha256": cache_hash,
            "pseudocode_sha256": sha256_bytes(body.encode("utf-8")),
            "class_table_key_pairs": len(pairs),
            "unique_exact_uelib_class_path_keys": sum(bool(class_rows.get(row["class_key"])) for row in pairs),
            "uelib_class_catalog_rows": sum(len(class_rows.get(row["class_key"], [])) for row in pairs),
            "direct_helper_pairs": sum(row["registration_helper"] == "FUN_00b699e0" for row in pairs),
            "wrapper_helper_pairs": sum(row["registration_helper"] == "FUN_0044c310" for row in pairs),
        }

    unique = {(str(row["registration_address"]), str(row["class_key"])) for row in all_rows}
    if len(unique) != len(all_rows):
        raise SystemExit("duplicate registration function/class-key pair")
    root, root_hash = load_cache("009DD640")
    root_body = str(root["pseudocode"])
    root_callees = sorted({
        call for call in re.findall(r"\b(FUN_[0-9a-f]{8})\(", root_body, re.I)
        if call.upper() != "FUN_009DD640"
    })
    direct_calls = [address for address in GROUPS if re.search(rf"FUN_{address}\(", root_body, re.I)]
    # The 004811B0 call is reported with its different class-key constructor.
    if set(direct_calls) != set(GROUPS):
        raise SystemExit(f"root dispatcher direct-call set differs: {direct_calls}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "EXP-0137-native-class-registration-group-uelib-join.csv"
    fields = list(all_rows[0])
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_rows)

    total = {
        "build_id": BUILD_ID,
        "exe_sha256": EXE_SHA256,
        "class_catalog_sha256": sha256_bytes(CLASS_CATALOG.read_bytes()),
        "root_dispatcher_address": "009DD640",
        "root_dispatcher_cache_sha256": root_hash,
        "root_dispatcher_unique_direct_callee_count": len(root_callees),
        "root_dispatcher_unique_direct_callees": [address.upper().replace("FUN_", "") for address in root_callees],
        "root_sets_and_clears_flag_mask_0x200_in_decompiler_output": (
            "DAT_01412958 = DAT_01412958 | 0x200" in root_body
            and "DAT_01412958 = DAT_01412958 & 0xfffffdff" in root_body
        ),
        "selected_group_functions_directly_called": direct_calls,
        "selected_registration_group_count": len(GROUPS),
        "class_table_key_pairs": len(all_rows),
        "distinct_function_key_pairs": len(unique),
        "distinct_class_key_strings": len({str(row["class_key"]) for row in all_rows}),
        "exact_uelib_class_path_matches": sum(bool(row["uelib_class_paths"]) for row in all_rows),
        "rows_across_matched_uelib_class_catalog": sum(int(row["uelib_class_catalog_rows"]) for row in all_rows),
        "distinct_matched_uelib_packages": len(all_matched_packages),
        "groups": group_summary,
        "limitations": [
            "Pairs are extracted from exact-build Ghidra decompiler output with explicit local-expression/helper-call patterns; pseudocode is not original source.",
            "UELib Class-path matching is exact label evidence. It does not prove object identity, table layout, token lookup, runtime invocation, or handler reachability.",
            "The group census covers the seven listed key/table bodies called directly by FUN_009DD640; it does not claim all executable registration paths or every NativeToken function.",
            "Pointer-symbol suffixes are retained as decompiler symbol metadata and were not used to infer table lengths or enumerate every handler in a class table.",
        ],
    }
    summary = OUTPUT_DIR / "EXP-0137-native-class-registration-group-uelib-join-summary.json"
    summary.write_text(json.dumps(total, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: total[k] for k in (
        "class_table_key_pairs", "distinct_class_key_strings", "exact_uelib_class_path_matches",
        "rows_across_matched_uelib_class_catalog", "distinct_matched_uelib_packages",
        "selected_group_functions_directly_called", "groups")}, indent=2))


if __name__ == "__main__":
    main()
