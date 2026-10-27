"""Summarize exact-build references to the native selector table and its initializer."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pefile
from capstone import (
    CS_AC_READ,
    CS_AC_WRITE,
    CS_ARCH_X86,
    CS_MODE_32,
    CS_OP_IMM,
    CS_OP_MEM,
    Cs,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE = ROOT / "Dishonored RHCP" / "Binaries" / "Win32" / "Dishonored.exe"
DEFAULT_FUNCTIONS = ROOT / "research" / "executable" / "functions.csv"
DEFAULT_NATIVE_TOKEN_CATALOG = (
    ROOT / "research" / "executable" / "evidence" / "native-token-dispatch-catalog.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "research"
    / "executable"
    / "evidence"
    / "native-selector-table-registration-census.csv"
)
DEFAULT_MANIFEST = (
    ROOT
    / "research"
    / "executable"
    / "evidence"
    / "native-selector-table-registration-census.json"
)
BUILD_RECORD = ROOT / "research" / "builds" / "BUILD-STEAM-10256413" / "build.md"
DEFAULT_TABLE = 0x014068F0
DEFAULT_INITIALIZER = 0x00426C60


def expected_build_sha256() -> str:
    text = BUILD_RECORD.read_text(encoding="utf-8")
    match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", text)
    if not match:
        raise ValueError(f"could not find executable SHA-256 in {BUILD_RECORD}")
    return match.group(1).lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_functions(path: Path) -> list[tuple[int, int, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        return [
            (int(row["body_start"], 16), int(row["body_end"], 16), row["name"])
            for row in rows
        ]


def va_to_offset(pe: pefile.PE, va: int) -> int:
    return pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)


def read_dword(pe: pefile.PE, va: int) -> int:
    offset = va_to_offset(pe, va)
    return int.from_bytes(pe.__data__[offset : offset + 4], "little")


def read_native_token_catalog(path: Path) -> dict[int, list[dict[str, str]]]:
    catalog: dict[int, list[dict[str, str]]] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            catalog.setdefault(int(row["native_token"], 10), []).append(row)
    return catalog


def access_for(insn, operand_index: int, operand) -> str:
    access = operand.access
    if access & CS_AC_READ and access & CS_AC_WRITE:
        return "read/write"
    if access & CS_AC_READ:
        return "read"
    if access & CS_AC_WRITE:
        return "write"
    if insn.mnemonic in {"mov", "movsx", "movsxd", "movzx"}:
        return "write" if operand_index == 0 else "read"
    if insn.mnemonic in {"cmp", "test", "push"}:
        return "read"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--functions", type=Path, default=DEFAULT_FUNCTIONS)
    parser.add_argument("--native-token-catalog", type=Path, default=DEFAULT_NATIVE_TOKEN_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--table", type=lambda value: int(value, 0), default=DEFAULT_TABLE)
    parser.add_argument(
        "--initializer",
        type=lambda value: int(value, 0),
        default=DEFAULT_INITIALIZER,
    )
    args = parser.parse_args()

    expected_sha = expected_build_sha256()
    actual_sha = sha256_file(args.exe)
    if actual_sha != expected_sha:
        parser.error(f"EXE SHA-256 mismatch: expected {expected_sha}, got {actual_sha}")

    pe = pefile.PE(str(args.exe), fast_load=True)
    if pe.FILE_HEADER.Machine != 0x14C:
        parser.error("expected an x86 PE executable")
    image_base = pe.OPTIONAL_HEADER.ImageBase
    functions = load_functions(args.functions)
    function_names = {start: name for start, _, name in functions}
    native_tokens = read_native_token_catalog(args.native_token_catalog)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True

    table_references: list[tuple[str, int, str, str]] = []
    direct_calls: list[tuple[int, str, int, int | None, int | None]] = []
    for start, end, name in functions:
        try:
            file_offset = pe.get_offset_from_rva(start - image_base)
        except pefile.PEFormatError:
            continue
        code = pe.__data__[file_offset : file_offset + end - start + 1]
        instructions = list(decoder.disasm(code, start))
        for index, insn in enumerate(instructions):
            if insn.mnemonic == "call" and insn.operands:
                target = insn.operands[0]
                if target.type == CS_OP_IMM and (target.imm & 0xFFFFFFFF) == args.initializer:
                    pushes = [
                        item.operands[0].imm
                        for item in reversed(instructions[max(0, index - 2) : index])
                        if item.mnemonic == "push"
                        and item.operands
                        and item.operands[0].type == CS_OP_IMM
                    ]
                    first_arg = pushes[0] & 0xFFFFFFFF if len(pushes) > 0 else None
                    second_arg = pushes[1] & 0xFFFFFFFF if len(pushes) > 1 else None
                    direct_calls.append((start, name, insn.address, first_arg, second_arg))

            for operand_index, operand in enumerate(insn.operands):
                if operand.type != CS_OP_MEM or (operand.mem.disp & 0xFFFFFFFF) != args.table:
                    continue
                table_references.append(
                    (name, insn.address, insn.mnemonic, access_for(insn, operand_index, operand))
                )

    access_counts = Counter((mnemonic, access) for _, _, mnemonic, access in table_references)
    token_counts = Counter(first_arg for _, _, _, first_arg, _ in direct_calls)
    pointer_args = sorted(
        {second_arg for _, _, _, _, second_arg in direct_calls if second_arg is not None}
    )
    contiguous_pointer_args = bool(pointer_args) and all(
        right - left == 4 for left, right in zip(pointer_args, pointer_args[1:])
    )

    print(f"build_exe_sha256={actual_sha}")
    print(f"indexed_functions={len(functions)}")
    print(
        f"table_operand_references={len(table_references)} "
        f"referencing_functions={len({name for name, _, _, _ in table_references})}"
    )
    print(f"table_operand_access_counts={dict(sorted(access_counts.items()))}")
    print(
        f"direct_initializer_calls={len(direct_calls)} "
        f"distinct_callers={len({name for _, name, _, _, _ in direct_calls})}"
    )
    print(f"direct_call_first_argument_counts={dict(sorted(token_counts.items(), key=str))}")
    sentinel_calls = token_counts.get(0xFFFFFFFF, 0)
    non_sentinel_calls = len(direct_calls) - sentinel_calls
    distinct_tokens = {
        token for token in token_counts if token not in (None, 0xFFFFFFFF)
    }
    print(
        f"sentinel_initializer_calls={sentinel_calls} "
        f"non_sentinel_registration_calls={non_sentinel_calls} "
        f"distinct_non_sentinel_tokens={len(distinct_tokens)}"
    )
    print(
        f"distinct_second_argument_pointer_cells={len(pointer_args)} "
        f"contiguous_4byte_cells={contiguous_pointer_args}"
    )
    if pointer_args:
        print(f"second_argument_cell_range=0x{pointer_args[0]:08X}-0x{pointer_args[-1]:08X}")

    output_rows = []
    for function_start, function_name, callsite, token, pointer_cell in direct_calls:
        if token is None or token == 0xFFFFFFFF or pointer_cell is None:
            continue
        target = read_dword(pe, pointer_cell)
        token_rows = native_tokens.get(token, [])
        exact_rows = [
            row
            for row in token_rows
            if row.get("adjacent_target_va", "").lower() == f"0x{target:08x}"
        ]
        target_section = "unmapped"
        target_rva = target - image_base
        for section in pe.sections:
            start_rva = section.VirtualAddress
            end_rva = start_rva + max(section.Misc_VirtualSize, section.SizeOfRawData)
            if start_rva <= target_rva < end_rva:
                target_section = section.Name.rstrip(b"\0").decode(errors="replace")
                break
        output_rows.append(
            {
                "native_token": f"0x{token:04X}",
                "build_id": "10256413",
                "executable_sha256": actual_sha,
                "registration_function_va": f"0x{function_start:08X}",
                "registration_function_name": function_name,
                "call_site_va": f"0x{callsite:08X}",
                "target_pointer_cell_va": f"0x{pointer_cell:08X}",
                "target_va": f"0x{target:08X}",
                "target_section": target_section,
                "target_exact_function_index": str(target in function_names).lower(),
                "target_function_name": function_names.get(target, ""),
                "uelib_token_catalog_rows": str(len(token_rows)),
                "uelib_exact_token_target_rows": str(len(exact_rows)),
                "uelib_exact_match_names": ";".join(
                    sorted({row["object_name"] for row in exact_rows})
                ),
                "uelib_exact_match_packages": ";".join(
                    sorted({row["package"] for row in exact_rows})
                ),
                "claim_status": "observed",
            }
        )

    fieldnames = [
        "native_token",
        "build_id",
        "executable_sha256",
        "registration_function_va",
        "registration_function_name",
        "call_site_va",
        "target_pointer_cell_va",
        "target_va",
        "target_section",
        "target_exact_function_index",
        "target_function_name",
        "uelib_token_catalog_rows",
        "uelib_exact_token_target_rows",
        "uelib_exact_match_names",
        "uelib_exact_match_packages",
        "claim_status",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(output_rows, key=lambda row: (row["native_token"], row["target_va"])))
    print(f"non_sentinel_registration_rows={len(output_rows)}")
    print(
        "exact_uelib_token_target_matches="
        f"{sum(int(row['uelib_exact_token_target_rows']) > 0 for row in output_rows)}"
    )
    print(f"registration_census={args.output.relative_to(ROOT).as_posix()}")
    exact_match_rows = sum(
        int(row["uelib_exact_token_target_rows"]) > 0 for row in output_rows
    )
    engine_tokens = {
        token
        for token, rows in native_tokens.items()
        if any(row.get("package") == "Engine.upk" for row in rows)
    }
    registered_tokens = {int(row["native_token"], 16) for row in output_rows}
    engine_token_sets_equal = registered_tokens == engine_tokens
    print(
        f"uelib_engine_token_set_equal={engine_token_sets_equal} "
        f"uelib_engine_token_count={len(engine_tokens)}"
    )
    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "build_id": "10256413",
        "executable_sha256": actual_sha,
        "inputs": {
            "executable": {"path": repo_relative(args.exe), "sha256": actual_sha},
            "function_index": {
                "path": repo_relative(args.functions),
                "sha256": sha256_file(args.functions),
                "rows": len(functions),
            },
            "native_token_catalog": {
                "path": repo_relative(args.native_token_catalog),
                "sha256": sha256_file(args.native_token_catalog),
                "rows": sum(len(rows) for rows in native_tokens.values()),
            },
            "build_record": {
                "path": repo_relative(BUILD_RECORD),
                "sha256": sha256_file(BUILD_RECORD),
            },
        },
        "tool": {
            "path": "tools/scan_native_selector_table.py",
            "sha256": sha256_file(Path(__file__).resolve()),
            "python": sys.version.split()[0],
            "pefile": importlib.metadata.version("pefile"),
            "capstone": importlib.metadata.version("capstone"),
            "command": "python tools/scan_native_selector_table.py",
        },
        "analysis": {
            "table_va": f"0x{args.table:08X}",
            "initializer_va": f"0x{args.initializer:08X}",
            "indexed_function_count": len(functions),
            "table_operand_reference_count": len(table_references),
            "table_referencing_function_count": len(
                {name for name, _, _, _ in table_references}
            ),
            "table_operand_access_counts": {
                f"{mnemonic}:{access}": count
                for (mnemonic, access), count in sorted(access_counts.items())
            },
            "direct_initializer_call_count": len(direct_calls),
            "sentinel_initializer_call_count": sentinel_calls,
            "non_sentinel_registration_call_count": non_sentinel_calls,
            "distinct_non_sentinel_token_count": len(distinct_tokens),
            "uelib_engine_distinct_nonzero_native_token_count": len(engine_tokens),
            "registration_tokens_equal_uelib_engine_tokens": engine_token_sets_equal,
            "distinct_second_argument_pointer_cell_count": len(pointer_args),
            "second_argument_cells_contiguous_by_4_bytes": contiguous_pointer_args,
            "registration_row_count": len(output_rows),
            "exact_uelib_token_target_match_row_count": exact_match_rows,
        },
        "outputs": {
            "registration_census": {
                "path": repo_relative(args.output),
                "sha256": sha256_file(args.output),
                "rows": len(output_rows),
            }
        },
        "limits": [
            "The call-site census includes direct calls found while disassembling indexed function bodies.",
            "Static call sites and pointer writes do not prove runtime execution of the registration wrappers.",
            "Exact token/target joins to EXP-0066 establish static address correspondence, not runtime dispatch or gameplay reachability.",
        ],
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"provenance_manifest={args.manifest_output.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
