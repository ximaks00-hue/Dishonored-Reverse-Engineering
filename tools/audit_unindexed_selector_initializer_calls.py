#!/usr/bin/env python3
"""Audit direct calls to the selector-table initializer outside indexed bodies.

This raw-PE audit validates the small wrapper byte pattern and preserves the
exact-build/input provenance. It does not name callers or infer token meaning.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import re
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, Cs

ROOT = Path(__file__).resolve().parents[1]
BUILD_RECORD = ROOT / "research/builds/BUILD-STEAM-10256413/build.md"
INSTALL_MANIFEST = ROOT / "research/builds/BUILD-STEAM-10256413/files.csv"
FUNCTIONS = ROOT / "research/executable/functions.csv"
EXE = ROOT / "Dishonored RHCP/Binaries/Win32/Dishonored.exe"
NATIVE_CATALOG = ROOT / "research/executable/evidence/native-token-dispatch-catalog.csv"
OUTPUT = ROOT / "research/executable/evidence/EXP-0163-unindexed-selector-initializer-calls.csv"
SUMMARY = ROOT / "research/executable/evidence/EXP-0163-unindexed-selector-initializer-calls.json"
INITIALIZER = 0x00426C60
EXPECTED_FUNCTIONS = 72_437


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_identity() -> tuple[str, str]:
    text = BUILD_RECORD.read_text(encoding="utf-8")
    build = re.search(r"Build ID:\s*`?(\d+)`?", text, re.IGNORECASE)
    exe = re.search(r"Executable SHA-256:\s*`([0-9A-Fa-f]{64})`", text)
    if not build or not exe:
        raise ValueError("build record lacks build ID or executable SHA-256")
    return build.group(1), exe.group(1).upper()


def read_functions() -> tuple[list[tuple[int, int, str]], dict[int, dict[str, str]]]:
    with FUNCTIONS.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    intervals = []
    entries = {}
    for row in rows:
        start, end = int(row["body_start"], 16), int(row["body_end"], 16)
        if start > end:
            raise ValueError(f"invalid function interval: {row['address']}")
        intervals.append((start, end, row["name"]))
        entry = int(row["address"], 16)
        if entry in entries:
            raise ValueError(f"duplicate function entry 0x{entry:08X}")
        entries[entry] = row
    if len(rows) != EXPECTED_FUNCTIONS:
        raise ValueError(f"expected {EXPECTED_FUNCTIONS} function rows, found {len(rows)}")
    return intervals, entries


def read_catalog_tokens() -> tuple[set[int], int]:
    with NATIVE_CATALOG.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {int(row["native_token"], 10) for row in rows}, len(rows)


def containing_body(address: int, intervals: list[tuple[int, int, str]]) -> str | None:
    matches = [name for start, end, name in intervals if start <= address <= end]
    if len(matches) > 1:
        raise ValueError(f"address 0x{address:08X} overlaps multiple indexed bodies")
    return matches[0] if matches else None


def section_for_va(pe: pefile.PE, address: int, *, file_backed: bool = False) -> tuple[str, int | None]:
    rva = address - pe.OPTIONAL_HEADER.ImageBase
    for section in pe.sections:
        end_size = section.SizeOfRawData if file_backed else max(section.Misc_VirtualSize, section.SizeOfRawData)
        if section.VirtualAddress <= rva < section.VirtualAddress + end_size:
            offset = section.PointerToRawData + rva - section.VirtualAddress
            return section.Name.rstrip(b"\0").decode("ascii", "replace"), offset
    return "unmapped", None


def manifest_exe_identity() -> tuple[int, str]:
    with INSTALL_MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream)
                if row.get("relative_path", "").replace("\\", "/").casefold()
                == "binaries/win32/dishonored.exe"]
    # The checked-in historical manifest may use a different header spelling;
    # support its documented path,size,sha256 columns without fuzzy row joins.
    if not rows:
        with INSTALL_MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
            rows = [row for row in csv.DictReader(stream)
                    if row.get("path", "").replace("\\", "/").casefold()
                    == "binaries/win32/dishonored.exe"]
    if len(rows) != 1:
        raise ValueError(f"expected one executable row in {INSTALL_MANIFEST}, found {len(rows)}")
    row = rows[0]
    size = int(row.get("size") or row.get("size_bytes") or row.get("bytes") or "-1")
    digest = (row.get("sha256") or row.get("SHA256") or "").upper()
    return size, digest


def parse_wrapper(code: bytes, call_offset: int, call_va: int) -> dict[str, int | str]:
    """Validate immediate args, direct call, cleanup, result-byte store and RET."""
    if call_offset >= 7 and code[call_offset - 7] == 0x68 and code[call_offset - 2] == 0x6A:
        entry_offset = call_offset - 7
        token = int.from_bytes(code[call_offset - 1:call_offset], "little", signed=True) & 0xFFFFFFFF
        cell = struct.unpack_from("<I", code, call_offset - 6)[0]
        encoding = "imm8"
    elif call_offset >= 10 and code[call_offset - 10] == 0x68 and code[call_offset - 5] == 0x68:
        entry_offset = call_offset - 10
        token = struct.unpack_from("<I", code, call_offset - 4)[0]
        cell = struct.unpack_from("<I", code, call_offset - 9)[0]
        encoding = "imm32"
    else:
        raise ValueError(f"unindexed call at 0x{call_va:08X} lacks the two immediate-push pattern")

    displacement = struct.unpack_from("<i", code, call_offset + 1)[0]
    target = (call_va + 5 + displacement) & 0xFFFFFFFF
    if target != INITIALIZER:
        raise ValueError(f"call at 0x{call_va:08X} resolves to 0x{target:08X}")
    post = code[call_offset + 5:call_offset + 14]
    if len(post) != 9 or post[:3] != bytes((0x83, 0xC4, 0x08)) or post[3] != 0xA2 or post[8] != 0xC3:
        raise ValueError(f"unindexed call at 0x{call_va:08X} lacks validated cleanup/store/RET postlude")
    result_byte = struct.unpack_from("<I", post, 4)[0]
    return {
        "entry_offset": entry_offset,
        "entry_va": call_va - (call_offset - entry_offset),
        "token": token,
        "pointer_cell_va": cell,
        "token_encoding": encoding,
        "return_va": call_va + 13,
        "result_byte_va": result_byte,
    }


def run() -> dict:
    build_id, expected_sha = build_identity()
    actual_sha = sha256(EXE)
    if actual_sha != expected_sha:
        raise ValueError(f"EXE SHA mismatch: expected {expected_sha}, got {actual_sha}")
    manifest_size, manifest_sha = manifest_exe_identity()
    if manifest_size != EXE.stat().st_size or manifest_sha != actual_sha:
        raise ValueError("EXE size/SHA do not match the registered install manifest row")

    image = EXE.read_bytes()
    pe = pefile.PE(data=image, fast_load=True)
    if pe.FILE_HEADER.Machine != 0x14C:
        raise ValueError("expected x86 PE machine type")
    image_base = pe.OPTIONAL_HEADER.ImageBase
    text_section = next((section for section in pe.sections
                         if section.Name.rstrip(b"\0") == b".text"), None)
    if text_section is None:
        raise ValueError("PE has no .text section")
    text_bytes = image[text_section.PointerToRawData:text_section.PointerToRawData + text_section.SizeOfRawData]
    text_va = image_base + text_section.VirtualAddress
    intervals, functions = read_functions()
    catalog_tokens, catalog_rows = read_catalog_tokens()

    # Independently decode every indexed body and require its callsites to be
    # present among the raw E8 candidates; this validates instruction alignment
    # for the indexed side of the split.
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    indexed_call_vas: set[int] = set()
    for start, end, _name in intervals:
        section, offset = section_for_va(pe, start, file_backed=True)
        if section != ".text" or offset is None:
            continue
        body = image[offset:offset + end - start + 1]
        for instruction in decoder.disasm(body, start):
            if instruction.mnemonic == "call" and instruction.operands and instruction.operands[0].type == CS_OP_IMM:
                if (instruction.operands[0].imm & 0xFFFFFFFF) == INITIALIZER:
                    indexed_call_vas.add(instruction.address)

    raw_calls = []
    for offset in range(0, len(text_bytes) - 4):
        if text_bytes[offset] != 0xE8:
            continue
        displacement = struct.unpack_from("<i", text_bytes, offset + 1)[0]
        call_va = text_va + offset
        if (call_va + 5 + displacement) & 0xFFFFFFFF == INITIALIZER:
            raw_calls.append((offset, call_va))

    indexed_calls = []
    external_calls = []
    for offset, call_va in raw_calls:
        owner = containing_body(call_va, intervals)
        if owner:
            indexed_calls.append((offset, call_va, owner))
        else:
            external_calls.append((offset, call_va))
    raw_indexed_sites = {call_va for _offset, call_va, _owner in indexed_calls}
    if raw_indexed_sites != indexed_call_vas:
        raise ValueError(
            "raw E8 sites inside indexed bodies differ from instruction-decoded calls "
            f"(raw={len(raw_indexed_sites)}, decoded={len(indexed_call_vas)})"
        )

    rows = []
    for call_offset, call_va in external_calls:
        wrapper = parse_wrapper(text_bytes, call_offset, call_va)
        entry_va = int(wrapper["entry_va"])
        return_va = int(wrapper["return_va"])
        if entry_va % 16:
            raise ValueError(f"candidate wrapper 0x{entry_va:08X} is not 16-byte aligned")
        if any(start <= return_va and end >= entry_va for start, end, _name in intervals):
            raise ValueError(f"wrapper at 0x{entry_va:08X} overlaps an indexed body")
        cell_va = int(wrapper["pointer_cell_va"])
        cell_section, cell_offset = section_for_va(pe, cell_va, file_backed=True)
        target_va = 0
        target_section = "unmapped"
        target_entry = False
        if cell_offset is None or cell_section != ".data":
            raise ValueError(f"pointer cell 0x{cell_va:08X} is not file-backed .data")
        target_va = struct.unpack_from("<I", image, cell_offset)[0]
        target_section, _ = section_for_va(pe, target_va)
        if target_section != ".text":
            raise ValueError(f"pointer cell 0x{cell_va:08X} points outside .text: 0x{target_va:08X}")
        target_entry = target_va in functions
        rows.append({
            "call_site_va": f"0x{call_va:08X}",
            "wrapper_entry_candidate_va": f"0x{entry_va:08X}",
            "return_instruction_va": f"0x{return_va:08X}",
            "token": f"0x{int(wrapper['token']):08X}",
            "token_is_sentinel": str(int(wrapper["token"]) == 0xFFFFFFFF).lower(),
            "token_push_encoding": wrapper["token_encoding"],
            "pointer_cell_va": f"0x{cell_va:08X}",
            "pointer_cell_section": cell_section,
            "target_va": f"0x{target_va:08X}",
            "target_section": target_section,
            "target_is_indexed_entry": str(target_entry).lower(),
            "result_byte_va": f"0x{int(wrapper['result_byte_va']):08X}",
            "claim_status": "observed_static_call_pattern",
        })

    rows.sort(key=lambda row: int(row["call_site_va"], 16))
    if len(raw_calls) != 2267 or len(indexed_calls) != 1082 or len(rows) != 1185:
        raise ValueError(f"unexpected call counts: raw={len(raw_calls)} indexed={len(indexed_calls)} unindexed={len(rows)}")
    tokens = Counter(row["token"] for row in rows)
    if tokens != Counter({"0xFFFFFFFF": 1183, "0x00000180": 1, "0x00000181": 1}):
        raise ValueError(f"unexpected outside-index token counts: {dict(tokens)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    non_sentinel = [row for row in rows if row["token_is_sentinel"] == "false"]
    catalog_matches = {
        row["token"]: int(row["token"], 16) in catalog_tokens
        for row in non_sentinel
    }
    if any(catalog_matches.values()):
        raise ValueError(f"outside-index token unexpectedly appears in UELib catalog: {catalog_matches}")
    target_probes = []
    probe_decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    probe_decoder.detail = True
    for row in non_sentinel:
        target_va = int(row["target_va"], 16)
        if target_va in functions:
            continue
        section, offset = section_for_va(pe, target_va, file_backed=True)
        if section != ".text" or offset is None:
            raise ValueError(f"unindexed target 0x{target_va:08X} is not file-backed .text")
        instructions = []
        for insn in probe_decoder.disasm(image[offset:offset + 0x100], target_va):
            instructions.append({"address": f"0x{insn.address:08X}", "bytes": insn.bytes.hex(" ").upper(),
                                 "mnemonic": insn.mnemonic, "operands": insn.op_str})
            if insn.mnemonic.startswith("ret"):
                break
        if not instructions or instructions[-1]["address"] != "0x0058C848" or instructions[-1]["mnemonic"] != "ret":
            raise ValueError(f"unexpected instruction boundary/exit for target 0x{target_va:08X}")
        if instructions[-1]["operands"] != "8":
            raise ValueError("expected the unindexed target to end at ret 8")
        target_probes.append({"target_va": f"0x{target_va:08X}", "instructions_through_return": instructions})
    summary = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "build_id": build_id,
        "executable_sha256": actual_sha,
        "inputs": {
            "executable": {"path": "Dishonored RHCP/Binaries/Win32/Dishonored.exe", "sha256": actual_sha, "size": len(image)},
            "install_manifest": {"path": "research/builds/BUILD-STEAM-10256413/files.csv", "sha256": sha256(INSTALL_MANIFEST), "exe_row_size": manifest_size, "exe_row_sha256": manifest_sha},
            "function_index": {"path": "research/executable/functions.csv", "sha256": sha256(FUNCTIONS), "rows": len(functions)},
            "native_token_catalog": {"path": "research/executable/evidence/native-token-dispatch-catalog.csv", "sha256": sha256(NATIVE_CATALOG), "rows": catalog_rows},
            "build_record": {"path": "research/builds/BUILD-STEAM-10256413/build.md", "sha256": sha256(BUILD_RECORD)},
        },
        "tool": {"path": "tools/audit_unindexed_selector_initializer_calls.py", "sha256": sha256(Path(__file__)), "python": __import__("platform").python_version(), "pefile": importlib.metadata.version("pefile"), "capstone": importlib.metadata.version("capstone")},
        "analysis": {
            "initializer_va": f"0x{INITIALIZER:08X}",
            "function_index_body_interval_count": len(intervals),
            "raw_text_rel32_call_candidates": len(raw_calls),
            "calls_in_indexed_bodies_instruction_decoded": len(indexed_calls),
            "calls_outside_indexed_bodies": len(rows),
            "outside_calls_matching_push_call_cleanup_result_byte_store_ret": len(rows),
            "outside_wrapper_entry_candidates_aligned_16": len(rows),
            "outside_tokens": dict(sorted(tokens.items())),
            "non_sentinel_rows": non_sentinel,
            "non_sentinel_tokens_present_in_exp0066_catalog": catalog_matches,
            "unindexed_non_sentinel_target_probes": target_probes,
            "target_sections": dict(Counter(row["target_section"] for row in rows)),
            "distinct_target_addresses": len({row["target_va"] for row in rows}),
        },
        "outputs": {"calls_csv": {"path": "research/executable/evidence/EXP-0163-unindexed-selector-initializer-calls.csv", "sha256": sha256(OUTPUT), "rows": len(rows)}},
        "limits": [
            "The 1,185 rows are raw-code static wrapper candidates outside indexed function body intervals; the checked-in Ghidra function index is unchanged.",
            "The 1,183 sentinel calls pass 0xFFFFFFFF and do not establish token-specific selector-table writes.",
            "Tokens 0x180 and 0x181 are observed arguments to the initializer; neither is identified as a UELib NativeToken or assigned a semantic meaning here.",
            "The UELib absence check is limited to the checked-in 207-row EXP-0066 derived catalog and does not prove absence from every package or runtime registry.",
            "The pointer-cell DWORD and target section/index membership are static PE relations; no caller execution, class ownership, dispatch, or runtime behavior is established.",
            "The scan is exact-build .text only and does not prove complete coverage of indirect calls or non-.text code.",
        ],
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw_text_call_candidates": len(raw_calls), "indexed_body_calls": len(indexed_calls),
                      "unindexed_wrapper_candidates": len(rows), "outside_tokens": dict(tokens),
                      "non_sentinel": non_sentinel, "csv": str(OUTPUT), "summary": str(SUMMARY)}, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
