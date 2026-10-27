#!/usr/bin/env python3
"""Summarize install-file families and parse INI-style text under Config/Localization.

The input manifest is authoritative for the recorded snapshot. Optional local
verification hashes only selected Config and Localization files, not the full
multi-gigabyte install tree.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter
from pathlib import Path, PurePosixPath

SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*(?:[;#].*)?$")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def family(path: str) -> str:
    normalized = path.replace("\\", "/")
    lower = normalized.casefold()
    ext = PurePosixPath(normalized).suffix.casefold()
    if "/localization/" in lower:
        return "game_localization" if lower.startswith("dishonoredgame/") else "engine_localization"
    if "/config/" in lower:
        return "configuration"
    if lower.startswith("dishonoredgame/movies/") or "/movies/" in lower:
        return "movies"
    if lower.startswith("binaries/win32/dvr_cb/") or lower.startswith("binaries/win32/dvr_cc/"):
        return "binaries_dvr_capture_frames"
    if lower.startswith("binaries/win32/dvr_vp0/"):
        return "binaries_dvr_capture_vp0"
    if lower.startswith("binaries/win32/dvr_traces/"):
        return "binaries_dvr_traces"
    if lower.startswith("binaries/win32/ghidra_projects/"):
        return "binaries_ghidra_project_data"
    if lower.startswith("binaries/redist/"):
        return "redistributables"
    if lower.startswith("mods/") or lower == "startinmenu-mod.zip":
        return "mods"
    if ext in {".exe", ".dll"}:
        return "executables_and_libraries"
    if ext in {".ini", ".bak", ".lf_backup"}:
        return "other_config_or_backup"
    if ext in {".pck", ".bnk", ".akmap", ".dvc0", ".dvc1"}:
        return "audio_or_wwise_named"
    if ext in {".bik"}:
        return "movies"
    if ext == ".tfc":
        return "texture_cache"
    if ext in {".asm", ".dxso"} or lower.startswith("binaries/win32/dvr_"):
        return "binaries_graphics_capture_or_shader"
    if ext == ".upk":
        return "unreal_packages"
    if lower.startswith("dishonoredgame/dlc/"):
        return "dlc_content_other"
    if lower.startswith("dishonoredgame/cookedpcconsole/"):
        return "cooked_game_content_other"
    if lower.startswith("binaries/win32/"):
        return "binaries_win32_other"
    if lower.startswith("engine/"):
        return "engine_other"
    return "other"


def decode_bytes(raw: bytes) -> tuple[str, str]:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
        encoding = "utf-16-bom"
    else:
        try:
            text = raw.decode("utf-8-sig")
            encoding = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("cp1252")
            encoding = "cp1252-fallback"
    return text, encoding


def parse_text(path: Path) -> tuple[str, int, int, int, int, int, str]:
    raw = path.read_bytes()
    text, encoding = decode_bytes(raw)
    sections: list[str] = []
    assignments = 0
    malformed = 0
    section_keys: Counter[tuple[str, str]] = Counter()
    current_section = "<global>"
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith((";", "#", "//")):
            continue
        match = SECTION_RE.match(line)
        if match:
            current_section = match.group(1).strip()
            sections.append(current_section)
            continue
        if "=" in line and line.split("=", 1)[0].strip():
            key = line.split("=", 1)[0].strip()
            section_keys[(current_section, key)] += 1
            assignments += 1
        else:
            malformed += 1
    duplicate_pairs = sum(count - 1 for count in section_keys.values() if count > 1)
    return (
        encoding,
        len(text.splitlines()),
        len(sections),
        assignments,
        duplicate_pairs,
        malformed,
        hashlib.sha256(raw).hexdigest().upper(),
    )


def localization_signatures(path: Path) -> tuple[set[tuple[str, str]], set[str]]:
    text, _ = decode_bytes(path.read_bytes())
    current_section = "<global>"
    signatures: set[tuple[str, str]] = set()
    keys: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith((";", "#")):
            continue
        match = SECTION_RE.match(line)
        if match:
            current_section = match.group(1).strip()
        elif "=" in line and line.split("=", 1)[0].strip():
            key = line.split("=", 1)[0].strip()
            signatures.add((current_section, key))
            keys.add(key)
    return signatures, keys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--text-output", required=True, type=Path)
    parser.add_argument("--config-reference-output", required=True, type=Path)
    parser.add_argument("--localization-parity-output", required=True, type=Path)
    parser.add_argument("--verify-text-hashes", action="store_true")
    parser.add_argument("--verify-dvr-ghidra-hashes", action="store_true")
    args = parser.parse_args()

    game_root = args.game_root.resolve(strict=True)
    rows = read_csv(args.manifest.resolve(strict=True))
    family_ext: Counter[tuple[str, str]] = Counter()
    family_ext_bytes: Counter[tuple[str, str]] = Counter()
    family_files: Counter[str] = Counter()
    locale_counts: Counter[tuple[str, str]] = Counter()
    text_rows: list[dict[str, object]] = []
    localization_files: dict[tuple[str, str], dict[str, Path]] = {}
    config_references: list[dict[str, str]] = []
    verified = 0
    dvr_ghidra_verified = 0
    dvr_ghidra_mismatches: list[str] = []

    for row in rows:
        rel = row["relative_path"].replace("\\", "/")
        path = PurePosixPath(rel)
        ext = path.suffix.casefold() or "[no extension]"
        group = family(rel)
        size = int(row["bytes"])
        family_ext[(group, ext)] += 1
        family_ext_bytes[(group, ext)] += size
        family_files[group] += 1
        if args.verify_dvr_ghidra_hashes and group in {
            "binaries_dvr_capture_frames",
            "binaries_dvr_capture_vp0",
            "binaries_dvr_traces",
            "binaries_ghidra_project_data",
        }:
            binary_path = game_root.joinpath(*path.parts)
            if binary_path.is_file():
                actual_size = binary_path.stat().st_size
                actual_hash = hashlib.sha256(binary_path.read_bytes()).hexdigest().upper()
                if actual_size == size and actual_hash.casefold() == row["sha256"].casefold():
                    dvr_ghidra_verified += 1
                else:
                    dvr_ghidra_mismatches.append(rel)
            else:
                dvr_ghidra_mismatches.append(rel)
        parts = path.parts
        if "/Localization/" in rel:
            locale_counts[(parts[0] if len(parts) > 0 else "?", parts[2] if len(parts) > 2 else "?")] += 1

        is_text_target = group in {"configuration", "game_localization", "engine_localization"}
        if not is_text_target:
            continue
        absolute = game_root.joinpath(*path.parts)
        exists = absolute.is_file()
        actual_hash = ""
        parse_result = ("missing", 0, 0, 0, 0, 0, "")
        hash_match: bool | str = "not_checked"
        if exists:
            parse_result = parse_text(absolute)
            actual_hash = parse_result[-1]
            if args.verify_text_hashes:
                hash_match = actual_hash.casefold() == row["sha256"].casefold()
                verified += int(hash_match is True)
            if group in {"game_localization", "engine_localization"}:
                locale = path.parts[2]
                logical_stem = PurePosixPath(path.parts[-1]).stem.casefold()
                logical_name = "/".join((path.parts[0].casefold(), *path.parts[3:-1], logical_stem))
                localization_files.setdefault((group, locale), {})[logical_name] = absolute
            elif group == "configuration":
                text, _ = decode_bytes(absolute.read_bytes())
                current_section = "<global>"
                for line_number, line in enumerate(text.splitlines(), 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith((";", "#", "//")):
                        continue
                    section_match = SECTION_RE.match(line)
                    if section_match:
                        current_section = section_match.group(1).strip()
                        continue
                    if "=" not in line:
                        continue
                    key, value = (part.strip() for part in line.split("=", 1))
                    key_name = key.lstrip("+-!").casefold()
                    if key_name == "basedon" or key_name.endswith("paths") or key_name.endswith("path"):
                        config_references.append({
                            "source_path": rel,
                            "line": str(line_number),
                            "section": current_section,
                            "key": key,
                            "value": value,
                        })
        text_rows.append({
            "relative_path": rel,
            "family": group,
            "bytes_manifest": size,
            "bytes_match": absolute.stat().st_size == size if exists else False,
            "exists": exists,
            "hash_match": hash_match,
            "encoding": parse_result[0],
            "lines": parse_result[1],
            "sections": parse_result[2],
            "assignments": parse_result[3],
            "duplicate_section_keys": parse_result[4],
            "unparsed_noncomment_lines": parse_result[5],
            "sha256_observed": actual_hash,
        })

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    with args.summary_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("family", "extension", "files", "bytes"))
        for (group, ext), count in sorted(family_ext.items()):
            writer.writerow((group, ext, count, family_ext_bytes[(group, ext)]))
    args.text_output.parent.mkdir(parents=True, exist_ok=True)
    with args.text_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(text_rows[0]) if text_rows else [])
        if text_rows:
            writer.writeheader()
            writer.writerows(text_rows)

    args.config_reference_output.parent.mkdir(parents=True, exist_ok=True)
    with args.config_reference_output.open("w", encoding="utf-8", newline="") as stream:
        fields = ("source_path", "line", "section", "key", "value")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(config_references)

    parity_rows: list[dict[str, object]] = []
    for group in ("game_localization", "engine_localization"):
        reference = localization_files.get((group, "INT"), {})
        locales = sorted(locale for family_name, locale in localization_files if family_name == group and locale != "INT")
        for locale in locales:
            candidate = localization_files[(group, locale)]
            ref_names, cand_names = set(reference), set(candidate)
            matched_names = ref_names & cand_names
            same_signatures = 0
            missing_key_count = 0
            extra_key_count = 0
            for name in matched_names:
                ref_signatures, _ = localization_signatures(reference[name])
                cand_signatures, _ = localization_signatures(candidate[name])
                same_signatures += int(ref_signatures == cand_signatures)
                missing_key_count += len(ref_signatures - cand_signatures)
                extra_key_count += len(cand_signatures - ref_signatures)
            parity_rows.append({
                "family": group,
                "reference_locale": "INT",
                "locale": locale,
                "reference_files": len(ref_names),
                "locale_files": len(cand_names),
                "common_files": len(matched_names),
                "reference_only_files": len(ref_names - cand_names),
                "locale_only_files": len(cand_names - ref_names),
                "files_with_identical_section_key_sets": same_signatures,
                "missing_section_key_pairs": missing_key_count,
                "extra_section_key_pairs": extra_key_count,
            })
    with args.localization_parity_output.open("w", encoding="utf-8", newline="") as stream:
        fields = tuple(parity_rows[0]) if parity_rows else ()
        writer = csv.DictWriter(stream, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(parity_rows)

    print(f"Manifest files: {len(rows)}")
    print(f"Families: {dict(sorted(family_files.items()))}")
    print(f"Localization directories: {dict(sorted(locale_counts.items()))}")
    print(f"Config/Localization text candidates: {len(text_rows)}")
    print(f"Text candidates present: {sum(bool(row['exists']) for row in text_rows)}")
    if args.verify_text_hashes:
        print(f"Text candidates hash-matched: {verified}/{len(text_rows)}")
    if args.verify_dvr_ghidra_hashes:
        print(f"DVR/Ghidra candidate paths hash-matched: {dvr_ghidra_verified}")
        print(f"DVR/Ghidra candidate missing or mismatched: {dvr_ghidra_mismatches[:20]}")
    print(f"Family/extension summary: {args.summary_output.resolve()}")
    print(f"Config/Localization profile: {args.text_output.resolve()}")
    print(f"Config path directives: {len(config_references)}")
    print(f"Localization structural comparisons: {len(parity_rows)}")
    print(f"Config reference output: {args.config_reference_output.resolve()}")
    print(f"Localization parity output: {args.localization_parity_output.resolve()}")


if __name__ == "__main__":
    main()
