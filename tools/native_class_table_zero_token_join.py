#!/usr/bin/env python3
"""Join EXP-0138 raw class-table entries to UELib native functions with token zero."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "research/builds/BUILD-STEAM-10256413"
GAME_ROOT = ROOT / "Dishonored RHCP"
EXECUTABLE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
RAW_TABLE_ROWS = ROOT / "research/executable/evidence/EXP-0138-native-class-table-raw-pointer-validation.csv"
FUNCTION_INDEX = ROOT / "research/executable/functions.csv"
BASELINE_TRIAGE = ROOT / "research/executable/evidence/function-triage/internal-function-triage.csv"
MANUAL_OVERLAY = ROOT / "research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0128.csv"
BASELINE_SUMMARY = ROOT / "research/executable/evidence/function-triage/internal-function-triage-summary.json"
MANUAL_SUMMARY = ROOT / "research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0128.json"
OUTPUT_DIR = ROOT / "research/executable/evidence"
EXPORT_RE = re.compile(r"// Export ([A-Za-z0-9_]+)::(exec[A-Za-z0-9_]+)")
FUNCTION_PATH_RE = re.compile(r"Function'[^.]+\.([^.]+)\.([^']+)'$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def class_owner_variants(class_key: str) -> tuple[str, ...]:
    return (class_key, "A" + class_key, "U" + class_key)


def package_relative_path(raw_path: str, game_root: Path) -> str:
    path = Path(raw_path).resolve(strict=True)
    return PurePosixPath(path.relative_to(game_root).as_posix()).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl-root", required=True, type=Path,
                        help="UELib function-census root containing the eight EXP-0057 packages")
    parser.add_argument("--manifest", type=Path, default=BUILD / "files.csv")
    parser.add_argument("--game-root", type=Path, default=GAME_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    jsonl_root = args.jsonl_root.resolve(strict=True)
    game_root = args.game_root.resolve(strict=True)
    manifest_rows = read_csv(args.manifest.resolve(strict=True))
    manifest = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in manifest_rows if row.get("relative_path")
    }
    if len(manifest_rows) != 13623:
        raise SystemExit(f"expected 13,623 manifest rows, found {len(manifest_rows)}")
    exe_row = manifest.get("binaries/win32/dishonored.exe")
    if not exe_row or exe_row["sha256"].upper() != EXECUTABLE_SHA256:
        raise SystemExit("manifest executable identity differs from selected build")

    source_files = sorted(jsonl_root.rglob("*.functions.jsonl"))
    if len(source_files) != 8:
        raise SystemExit(f"expected eight function-census JSONL files, found {len(source_files)}")
    source_hashes = {path: sha256_file(path) for path in source_files}
    exports_by_owner_exec: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    corpus_rows = 0
    native_flagged_rows = 0
    zero_token_rows = 0
    package_hashes: dict[str, str] = {}
    package_rels: dict[str, str] = {}

    for path in source_files:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                item = json.loads(line)
                corpus_rows += 1
                source_path = Path(str(item["package"])).resolve(strict=True)
                package_rel = package_relative_path(str(source_path), game_root)
                manifest_row = manifest.get(package_rel.casefold())
                if not manifest_row or item.get("sourceSha256", "").upper() != manifest_row["sha256"].upper():
                    raise SystemExit(f"UELib record source hash differs from manifest: {package_rel}")
                if package_rel.casefold() not in package_hashes:
                    actual_hash = sha256_file(source_path)
                    if actual_hash != manifest_row["sha256"].upper():
                        raise SystemExit(f"local package differs from manifest: {package_rel}")
                    package_hashes[package_rel.casefold()] = actual_hash
                    package_rels[package_rel.casefold()] = package_rel
                match = EXPORT_RE.search(str(item.get("decompiled", "")))
                if not match:
                    continue
                owner, exec_name = match.groups()
                if item.get("nativeFlag") is True:
                    native_flagged_rows += 1
                    if int(item.get("nativeToken") or 0) == 0:
                        zero_token_rows += 1
                exports_by_owner_exec[(owner, exec_name)].append({
                    **item,
                    "_owner": owner,
                    "_exec": exec_name,
                    "_package_relative_path": package_rel,
                    "_jsonl_path": path.relative_to(jsonl_root).as_posix(),
                    "_jsonl_sha256": source_hashes[path],
                    "_jsonl_line": line_number,
                })

    if corpus_rows != 4772 or native_flagged_rows != 2572 or zero_token_rows != 2383:
        raise SystemExit(
            "UELib corpus denominator differs from EXP-0057/0066: "
            f"rows={corpus_rows}, native={native_flagged_rows}, zero-token={zero_token_rows}"
        )

    table_rows = read_csv(RAW_TABLE_ROWS)
    if len(table_rows) != 332 or any(row["build_id"] != "10256413"
                                     or row["exe_sha256"].upper() != EXECUTABLE_SHA256
                                     for row in table_rows):
        raise SystemExit("EXP-0138 input count or build identity differs")

    matches: list[dict[str, object]] = []
    for table_row in table_rows:
        key = table_row["class_key"]
        native_name = table_row["decoded_native_exec_name"]
        owner = next((candidate for candidate in sorted(class_owner_variants(key), key=len, reverse=True)
                      if native_name.startswith(candidate + "exec")), None)
        if owner is None:
            raise SystemExit(f"exec name does not encode the EXP-0137 class key: {key} / {native_name}")
        exec_name = native_name[len(owner):]
        candidates = [
            item
            for owner_variant in class_owner_variants(key)
            for item in exports_by_owner_exec.get((owner_variant, exec_name), [])
        ]
        if len(candidates) != 1:
            raise SystemExit(f"expected one exact UELib Function export for {native_name}; found {len(candidates)}")
        item = candidates[0]
        path_match = FUNCTION_PATH_RE.fullmatch(str(item.get("objectPath", "")))
        if not path_match or path_match.group(1) != key or path_match.group(2) != exec_name.removeprefix("exec"):
            raise SystemExit(f"UELib Function object path disagrees with exact owner/name join: {native_name}")
        native_flag = item.get("nativeFlag") is True
        native_token = int(item.get("nativeToken") or 0)
        if not native_flag or native_token != 0:
            raise SystemExit(f"matched export is not NativeFlag/token-zero as expected: {native_name}")
        declaration = ""
        for line in str(item.get("decompiled", "")).splitlines():
            if line.strip().startswith("native "):
                declaration = line.strip()
                break
        matches.append({
            **table_row,
            "uelib_package_relative_path": item["_package_relative_path"],
            "uelib_package_sha256": str(item["sourceSha256"]).upper(),
            "uelib_function_object_path": item["objectPath"],
            "uelib_export_owner": item["_owner"],
            "uelib_exec_name": item["_exec"],
            "uelib_native_flag": native_flag,
            "uelib_native_token": native_token,
            "uelib_script_size": item.get("scriptSize", ""),
            "uelib_native_declaration": declaration,
            "uelib_jsonl_source": item["_jsonl_path"],
            "uelib_jsonl_sha256": item["_jsonl_sha256"],
            "uelib_jsonl_line": item["_jsonl_line"],
        })

    if len({(row["class_key"], row["uelib_function_object_path"]) for row in matches}) != len(matches):
        raise SystemExit("duplicate class-key/UELib-function relation")

    functions = {row["address"].upper(): row for row in read_csv(FUNCTION_INDEX)}
    baseline = {row["address"].upper(): row for row in read_csv(BASELINE_TRIAGE)}
    manual = {row["address"].upper(): row for row in read_csv(MANUAL_OVERLAY)}
    baseline_summary = json.loads(BASELINE_SUMMARY.read_text(encoding="utf-8"))
    manual_summary = json.loads(MANUAL_SUMMARY.read_text(encoding="utf-8"))
    candidates_by_address: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in matches:
        if row["exact_function_index_start"] != "True":
            continue
        address = str(row["raw_handler_target_va"])[2:].upper()
        if address not in functions or address not in baseline:
            raise SystemExit(f"EXP-0138 exact function target is absent from function index: {address}")
        if baseline[address]["subsystem_candidate"] != "unknown":
            raise SystemExit(f"unexpected preexisting subsystem label for target {address}")
        candidates_by_address[address].append(row)

    if set(candidates_by_address) & set(manual):
        raise SystemExit("new pointer-target candidates overlap existing manually reviewed addresses")

    candidate_rows: list[dict[str, object]] = []
    for address, edges in sorted(candidates_by_address.items()):
        class_methods = sorted({
            (str(row["class_key"]), str(row["uelib_function_object_path"]),
             str(row["uelib_package_relative_path"]), str(row["uelib_native_declaration"]))
            for row in edges
        })
        candidate_rows.append({
            "address": address,
            "name": functions[address]["name"],
            "size_bytes": functions[address]["size"],
            "baseline_subsystem_candidate": baseline[address]["subsystem_candidate"],
            "pointer_target_edge_count": len(edges),
            "source_class_methods_json": json.dumps([
                {"class_key": cls, "uelib_function": path, "uelib_package": package,
                 "declaration": declaration}
                for cls, path, package, declaration in class_methods
            ], ensure_ascii=False, separators=(",", ":")),
            "registration_functions": " | ".join(sorted({str(row["registration_address"]) for row in edges})),
            "body_review_status": "not_reviewed_by_this_pointer_join",
            "static_role_candidate": "exact class-table .text target joined by exec name to UELib NativeFlag=true NativeToken=0 exports",
            "subsystem_assignment": "unknown",
            "runtime_status": "unknown",
            "claim_status": "observed pointer/name/export joins; native handler interpretation is a candidate",
        })

    if len(matches) != 332 or len(candidate_rows) != 254:
        raise SystemExit(f"unexpected join/unique-target counts: {len(matches)} / {len(candidate_rows)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    join_path = args.output_dir / "EXP-0139-native-class-table-uelib-zero-token-join.csv"
    with join_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(matches[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(matches)
    overlay_path = args.output_dir / "function-triage/native-class-table-handler-candidates-EXP-0139.csv"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    with overlay_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(candidate_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(candidate_rows)

    package_counts = Counter(str(row["uelib_package_relative_path"]) for row in matches)
    registration_counts: dict[str, dict[str, object]] = {}
    for address in sorted({str(row["registration_address"]) for row in matches}):
        group = [row for row in matches if row["registration_address"] == address]
        registration_counts[address] = {
            "table_export_edges": len(group),
            "exact_uelib_zero_token_matches": sum(row["uelib_native_token"] == 0 for row in group),
            "indexed_function_start_edges": sum(row["exact_function_index_start"] == "True" for row in group),
            "unique_indexed_target_functions": len({
                str(row["raw_handler_target_va"]) for row in group
                if row["exact_function_index_start"] == "True"
            }),
        }
    summary = {
        "build_id": "10256413",
        "exe_sha256": EXECUTABLE_SHA256,
        "exp_0138_input_sha256": sha256_file(RAW_TABLE_ROWS),
        "function_index_sha256": sha256_file(FUNCTION_INDEX),
        "manifest_sha256": sha256_file(args.manifest.resolve(strict=True)),
        "uelib_census_root": str(jsonl_root.relative_to(ROOT)),
        "uelib_jsonl_sources": [
            {"path": path.relative_to(jsonl_root).as_posix(), "sha256": source_hashes[path]}
            for path in source_files
        ],
        "uelib_package_sources_rehashed": len(package_hashes),
        "uelib_corpus_function_rows": corpus_rows,
        "uelib_native_flagged_rows": native_flagged_rows,
        "uelib_native_flagged_zero_token_rows": zero_token_rows,
        "class_table_edges": len(matches),
        "unique_exact_uelib_function_matches": len(matches),
        "matched_native_flag_true_rows": sum(bool(row["uelib_native_flag"]) for row in matches),
        "matched_native_token_zero_rows": sum(int(row["uelib_native_token"]) == 0 for row in matches),
        "matched_nonzero_native_token_rows": sum(int(row["uelib_native_token"]) != 0 for row in matches),
        "indexed_function_start_edges": sum(row["exact_function_index_start"] == "True" for row in matches),
        "unindexed_text_target_edges": sum(row["exact_function_index_start"] != "True" for row in matches),
        "unique_indexed_target_functions": len(candidate_rows),
        "target_addresses_in_baseline_unknown_subsystem": len(candidate_rows),
        "target_addresses_overlapping_manual_review_overlay": 0,
        "target_addresses_overlapping_baseline_symbol_candidates": 0,
        "baseline_unknown_subsystem_functions": int(baseline_summary["functions_assigned_unknown_subsystem_bucket"]),
        "manual_overlay_prior_unresolved_unknown_rows": int(manual_summary["overlay_unresolved_unknown_subsystem"]),
        "unresolved_unknown_rows_after_this_candidate_overlay": int(manual_summary["overlay_unresolved_unknown_subsystem"]),
        "candidate_rows_in_prior_combined_overlay": int(manual_summary["overlay_candidate_rows"]),
        "candidate_rows_if_this_role_overlay_is_counted_additively": int(manual_summary["overlay_candidate_rows"]) + len(candidate_rows),
        "body_reviewed_functions_added": 0,
        "runtime_verified_functions_added": 0,
        "matched_uelib_function_package_rows": dict(sorted(package_counts.items())),
        "registration_function_counts": registration_counts,
        "limitations": [
            "The 332 matches are exact class/method label and UELib metadata joins to raw pointer records; they are static role candidates, not runtime dispatch proof.",
            "The 254 unique indexed targets remain subsystem-unassigned and their function bodies were not reviewed by this pass.",
            "Three matched .text targets do not match function-index starts or indexed function ranges; they remain outside the unique function-target overlay.",
            "The census covers selected table groups and eight function-bearing UELib packages, not every executable function or registration path.",
        ],
    }
    summary_path = args.output_dir / "EXP-0139-native-class-table-uelib-zero-token-join-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "uelib_corpus_function_rows", "uelib_native_flagged_rows", "uelib_native_flagged_zero_token_rows",
        "class_table_edges", "unique_exact_uelib_function_matches", "matched_native_token_zero_rows",
        "indexed_function_start_edges", "unindexed_text_target_edges", "unique_indexed_target_functions",
        "target_addresses_in_baseline_unknown_subsystem", "target_addresses_overlapping_manual_review_overlay",
        "unresolved_unknown_rows_after_this_candidate_overlay", "candidate_rows_if_this_role_overlay_is_counted_additively",
        "matched_uelib_function_package_rows", "registration_function_counts")}, indent=2))


if __name__ == "__main__":
    main()
