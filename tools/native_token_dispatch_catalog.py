#!/usr/bin/env python3
"""Join UELib NativeToken declarations to exact-build executable registration tables.

This is a static, read-only workflow. It asks Ghidra to search native exec-name
strings and export their data xrefs, then checks the raw PE DWORDs at each xref
site and at the adjacent +4 slot. A .text address is a candidate code target;
an exact function-index entry is stronger evidence. Neither alone proves runtime
execution or full native-token coverage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

import pefile

EXPECTED_EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
OWNER_ALIASES = {
    "UActor": "AActor",
    "UController": "AController",
    "UPlayerController": "APlayerController",
}
EXPORT_RE = re.compile(r"^// Export ([A-Za-z0-9_]+)::(exec[A-Za-z0-9_]+)", re.MULTILINE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_native_records(jsonl_root: Path, package_manifest: Path, game_root: Path) -> list[dict[str, str]]:
    manifest = {
        row["relative_path"].replace("\\", "/").casefold(): row["sha256"].upper()
        for row in read_csv(package_manifest)
        if row.get("relative_path") and row.get("sha256")
    }
    records: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for jsonl_path in sorted(jsonl_root.rglob("*.jsonl")):
        with jsonl_path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                item = json.loads(line)
                if not item.get("nativeFlag") or int(item.get("nativeToken", 0)) == 0:
                    continue
                source = Path(item["package"]).resolve(strict=True)
                relative = PurePosixPath(source.relative_to(game_root).as_posix()).as_posix()
                expected = manifest.get(relative.casefold())
                if expected is None:
                    raise ValueError(f"package is not in manifest: {relative}")
                if item.get("sourceSha256", "").upper() != expected:
                    raise ValueError(f"source package hash mismatch: {relative}")
                match = EXPORT_RE.search(item.get("decompiled", ""))
                if not match:
                    raise ValueError(f"cannot parse UELib export name: {jsonl_path}:{line_number}")
                owner, exec_name = match.groups()
                registration_owner = OWNER_ALIASES.get(owner, owner)
                record = {
                    "native_token": str(int(item["nativeToken"])),
                    "package": source.name,
                    "package_relative_path": relative,
                    "object_name": item["objectName"],
                    "decompiled_owner_class": owner,
                    "registration_owner_class": registration_owner,
                    "search_string": registration_owner + exec_name,
                    "source_sha256": expected,
                }
                key = (record["native_token"], relative.casefold(), record["object_name"].casefold())
                if key in seen:
                    raise ValueError(f"duplicate native function record: {key}")
                seen.add(key)
                records.append(record)
    if not records:
        raise ValueError(f"no nonzero NativeToken exports found under {jsonl_root}")
    return records


def section_for_va(pe: pefile.PE, va: int) -> tuple[str, int | None]:
    rva = va - pe.OPTIONAL_HEADER.ImageBase
    for section in pe.sections:
        start = section.VirtualAddress
        raw_size = section.SizeOfRawData
        if start <= rva < start + raw_size:
            offset = section.PointerToRawData + rva - start
            name = section.Name.rstrip(b"\0").decode("ascii", errors="replace")
            return name, offset
    return "", None


def csv_va(value: str) -> int:
    return int(value.strip().removeprefix("0x").removeprefix("0X"), 16)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl-root", required=True, type=Path,
                        help="root containing UELib *.functions.jsonl outputs")
    parser.add_argument("--package-manifest", required=True, type=Path,
                        help="manifest with relative_path and sha256 columns")
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--function-index", required=True, type=Path)
    parser.add_argument("--analyze-headless", required=True, type=Path)
    parser.add_argument("--ghidra-project", required=True, type=Path)
    parser.add_argument("--project-name", default="Dishonored-RHCP-10256413")
    parser.add_argument("--script", type=Path,
                        default=Path("research/executable/scripts/ExportNativeTokenStringRefs.java"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    executable = args.executable.resolve(strict=True)
    game_root = args.game_root.resolve(strict=True)
    analyze_headless = args.analyze_headless.resolve(strict=True)
    ghidra_project = args.ghidra_project.resolve(strict=True)
    script = args.script.resolve(strict=True)
    jsonl_root = args.jsonl_root.resolve(strict=True)
    package_manifest = args.package_manifest.resolve(strict=True)
    function_index = args.function_index.resolve(strict=True)
    output = args.output.resolve()

    exe_sha = hashlib.sha256(executable.read_bytes()).hexdigest().upper()
    if exe_sha != EXPECTED_EXE_SHA256:
        raise ValueError(f"unexpected executable SHA-256: {exe_sha}")

    records = load_native_records(jsonl_root, package_manifest, game_root)
    index_rows = read_csv(function_index)
    index = {int(row["address"], 16): row for row in index_rows}
    pe = pefile.PE(str(executable), fast_load=True)
    image = executable.read_bytes()

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(".tmp/native-token-dispatch").resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-", dir=temp_root) as work:
        work_dir = Path(work)
        input_csv = work_dir / "native-token-input.csv"
        refs_csv = work_dir / "native-token-xrefs.csv"
        with input_csv.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=("native_token", "package", "object_name", "search_string"))
            writer.writeheader()
            writer.writerows({
                "native_token": r["native_token"],
                "package": r["package"],
                "object_name": r["object_name"],
                "search_string": r["search_string"],
            } for r in records)

        command = [
            str(analyze_headless), str(ghidra_project), args.project_name,
            "-process", executable.name, "-noanalysis", "-readOnly",
            "-scriptPath", str(script.parent),
            "-postScript", script.name, str(input_csv), str(refs_csv),
        ]
        process = subprocess.run(
            command, cwd=script.parents[3], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=args.timeout_seconds,
        )
        report = process.stdout + "\n" + process.stderr
        if process.returncode != 0 or not refs_csv.is_file():
            sys.stderr.write(report[-12000:])
            raise RuntimeError(f"analyzeHeadless failed with exit code {process.returncode}")
        if f"INPUT_RECORDS={len(records)}" not in report or "PROGRAM=Dishonored.exe" not in report:
            sys.stderr.write(report[-12000:])
            raise RuntimeError("headless script did not report the expected input/program")
        refs = read_csv(refs_csv)

    records_by_key = {
        (r["native_token"], r["package"], r["object_name"]): r for r in records
    }
    output_rows: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    observed: set[tuple[str, str, str]] = set()
    for ref in refs:
        key = (ref["native_token"], ref["package"], ref["object_name"])
        record = records_by_key.get(key)
        if record is None:
            raise ValueError(f"unexpected Ghidra result row: {key}")
        observed.add(key)
        row: dict[str, object] = {
            **record,
            "string_va": ref["string_va"],
            "xref_site_va": ref["xref_from_va"],
            "xref_containing_function_va": ref["xref_function_va"],
            "xref_containing_function_name": ref["xref_function_name"],
            "reference_type": ref["reference_type"],
            "raw_name_pointer": "",
            "name_pointer_matches_string": False,
            "adjacent_target_va": "",
            "adjacent_target_section": "",
            "target_exact_function_index": False,
            "target_function_name": "",
            "target_function_signature": "",
        }
        if ref["string_va"] and ref["xref_from_va"]:
            site_va = csv_va(ref["xref_from_va"])
            string_va = csv_va(ref["string_va"])
            site_section, site_offset = section_for_va(pe, site_va)
            pointer_slot_section, pointer_slot_offset = section_for_va(pe, site_va + 4)
            if site_offset is not None and site_offset + 4 <= len(image) - 4 and pointer_slot_section == site_section and pointer_slot_offset is not None:
                raw_name = int.from_bytes(image[site_offset:site_offset + 4], "little")
                raw_target = int.from_bytes(image[site_offset + 4:site_offset + 8], "little")
                target_section, _ = section_for_va(pe, raw_target)
                target_index = index.get(raw_target)
                row.update({
                    "xref_site_section": site_section,
                    "raw_name_pointer": f"0x{raw_name:08X}",
                    "name_pointer_matches_string": raw_name == string_va,
                    "adjacent_target_va": f"0x{raw_target:08X}",
                    "adjacent_target_section": target_section,
                    "target_exact_function_index": target_index is not None,
                    "target_function_name": target_index["name"] if target_index else "",
                    "target_function_signature": target_index["signature"] if target_index else "",
                })
                counts["xref_rows"] += 1
                counts["raw_name_pointer_matches"] += raw_name == string_va
                counts["data_to_text_pairs"] += site_section == ".data" and target_section == ".text"
                counts["target_exact_function_index"] += target_index is not None
                if target_section == ".text":
                    counts["text_targets"] += 1
        output_rows.append(row)

    if observed != set(records_by_key):
        missing = sorted(set(records_by_key) - observed)
        raise ValueError(f"Ghidra did not resolve {len(missing)} records; first: {missing[:5]}")

    fields = [
        "native_token", "package", "package_relative_path", "object_name",
        "decompiled_owner_class", "registration_owner_class", "search_string", "source_sha256",
        "string_va", "xref_site_va", "xref_site_section", "raw_name_pointer",
        "name_pointer_matches_string", "adjacent_target_va", "adjacent_target_section",
        "target_exact_function_index", "target_function_name", "target_function_signature",
        "xref_containing_function_va", "xref_containing_function_name", "reference_type",
    ]
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    unique_records = len(records_by_key)
    distinct_sites = len({row["xref_site_va"] for row in output_rows if row["xref_site_va"]})
    distinct_targets = len({row["adjacent_target_va"] for row in output_rows if row["adjacent_target_va"]})
    print(f"Executable SHA-256: {exe_sha}")
    print(f"UELib NativeToken records: {unique_records}")
    print(f"Ghidra string-xref rows: {counts['xref_rows']}")
    print(f"Unique .data source sites: {distinct_sites}")
    print(f"Distinct adjacent target addresses: {distinct_targets}")
    print(f"Raw name pointers equal string VAs: {counts['raw_name_pointer_matches']}/{counts['xref_rows']}")
    print(f"Adjacent .data-to-.text pairs: {counts['data_to_text_pairs']}/{counts['xref_rows']}")
    print(f"Adjacent targets at indexed function starts: {counts['target_exact_function_index']}/{counts['xref_rows']}")
    print(f"Catalog: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
