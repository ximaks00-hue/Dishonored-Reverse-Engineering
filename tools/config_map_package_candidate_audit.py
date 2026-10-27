#!/usr/bin/env python3
"""Join selected Dishonored INI map/package names to exact-build UPK basenames."""

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
EXE_SHA256 = "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"
ASSIGNMENT_RE = re.compile(r"^\s*([+.-]*)([A-Za-z0-9_.\[\]-]+)\s*=\s*(.*?)\s*$")
MAP_HINT_RE = re.compile(r"m_MapName\s*=\s*\"?([^\",)]+)", re.IGNORECASE)
OBJECT_PATH_RE = re.compile(r"^\s*(?:Class)?['\"]?([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)['\"]?\s*$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def decode_config(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".part")
    try:
        with temp.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def reference_value(name: str) -> str:
    return name.strip().strip("\"'").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=BUILD / "files.csv")
    parser.add_argument("--build-record", type=Path, default=BUILD / "build.md")
    parser.add_argument("--game-root", type=Path, default=GAME_ROOT)
    parser.add_argument("--output-dir", type=Path, default=BUILD)
    parser.add_argument("--prefix", default="config-map-package-candidates")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve(strict=True)
    manifest = read_csv(manifest_path)
    manifest_by_path = {r["relative_path"].replace("\\", "/").casefold(): r for r in manifest}
    build_text = args.build_record.resolve(strict=True).read_text(encoding="utf-8")
    build_match = re.search(r"Steam build ID:\s*`?(\d+)", build_text)
    exe_match = re.search(r"Executable SHA-256:\s*`?([0-9A-Fa-f]{64})", build_text)
    if not build_match or not exe_match or build_match.group(1) != "10256413" or exe_match.group(1).upper() != EXE_SHA256:
        raise SystemExit("build record identity differs from the scoped build")
    exe = (args.game_root / "Binaries/Win32/Dishonored.exe").resolve(strict=True)
    exe_manifest = manifest_by_path.get("binaries/win32/dishonored.exe")
    if sha256_file(exe) != EXE_SHA256 or not exe_manifest or exe_manifest["sha256"].upper() != EXE_SHA256:
        raise SystemExit("local executable does not match build record and manifest")

    ini_paths = []
    for row in manifest:
        rel = row["relative_path"].replace("\\", "/")
        low = rel.casefold()
        if not low.endswith(".ini"):
            continue
        if low.startswith("dishonoredgame/config/") or low.startswith("engine/config/") or low.startswith("dishonoredgame/dlc/pcconsole/"):
            ini_paths.append((row, rel))
    if len(ini_paths) != 46:
        raise SystemExit(f"expected 46 scoped INI files from the current manifest; found {len(ini_paths)}")

    upk_by_stem: dict[str, list[str]] = defaultdict(list)
    for row in manifest:
        rel = row["relative_path"].replace("\\", "/")
        if rel.casefold().endswith(".upk"):
            upk_by_stem[PurePosixPath(rel).stem.casefold()].append(rel)
    if sum(len(paths) for paths in upk_by_stem.values()) != 904:
        raise SystemExit("manifest UPK denominator is not 904")

    config_sources: list[dict[str, object]] = []
    refs: list[dict[str, object]] = []

    def emit(row: dict[str, str], line_no: int, section: str, key: str, raw: str,
             kind: str, target: str, allow_sf: bool) -> None:
        target = reference_value(target)
        exact = upk_by_stem.get(target.casefold(), [])
        plus_sf = []
        if allow_sf and not target.casefold().endswith("_sf"):
            plus_sf = upk_by_stem.get((target + "_SF").casefold(), [])
        all_paths = sorted(set(exact + plus_sf), key=str.casefold)
        candidate_files = [
            {
                "path": path,
                "bytes": int(manifest_by_path[path.casefold()]["bytes"]),
                "sha256": manifest_by_path[path.casefold()]["sha256"].upper(),
            }
            for path in all_paths
        ]
        if not target:
            status = "empty_target"
        elif exact and plus_sf:
            status = "exact_and_plus_SF_candidates"
        elif exact:
            status = "exact_basename_match" if len(exact) == 1 else "ambiguous_exact_basename"
        elif plus_sf:
            status = "plus_SF_candidate" if len(plus_sf) == 1 else "ambiguous_plus_SF_candidates"
        elif kind == "mission_image_object_without_package" or kind == "dotted_object_reference_without_package_candidate":
            status = "object_name_without_package_candidate"
        else:
            status = "no_UPK_basename_candidate"
        refs.append({
            "source_path": row["relative_path"].replace("\\", "/"),
            "source_sha256": row["sha256"].upper(), "line": line_no,
            "section": section, "key": key, "reference_kind": kind,
            "raw_value": raw, "target_name": target,
            "exact_basename_paths": json.dumps(sorted(exact, key=str.casefold), ensure_ascii=False, separators=(",", ":")),
            "name_plus_SF_paths": json.dumps(sorted(plus_sf, key=str.casefold), ensure_ascii=False, separators=(",", ":")),
            "all_candidate_paths": json.dumps(all_paths, ensure_ascii=False, separators=(",", ":")),
            "candidate_files_with_manifest_hashes": json.dumps(candidate_files, ensure_ascii=False, separators=(",", ":")),
            "candidate_path_count": len(all_paths), "join_status": status,
        })

    package_list_keys = {"package", "seekfreepackage", "packagestobefullyloadedatstartup"}
    for manifest_row, rel in sorted(ini_paths, key=lambda x: x[1].casefold()):
        pure = PurePosixPath(rel)
        if pure.is_absolute() or ".." in pure.parts:
            raise SystemExit(f"configuration path escapes game root: {rel}")
        source = args.game_root.resolve(strict=True).joinpath(*pure.parts)
        data = source.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest().upper()
        if len(data) != int(manifest_row["bytes"]) or actual_sha != manifest_row["sha256"].upper():
            raise SystemExit(f"configuration source differs from manifest: {rel}")
        text = decode_config(data)
        config_sources.append({"source_path": rel, "source_bytes": len(data), "source_sha256": actual_sha, "manifest_match": True})
        section = ""
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith((";", "#")):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                section = stripped[1:-1].strip()
                continue
            match = ASSIGNMENT_RE.match(line)
            if not match:
                continue
            prefix, raw_key, raw_value = match.groups()
            key = raw_key.strip()
            canonical_key = key.casefold()
            value = raw_value.strip()
            if canonical_key in package_list_keys:
                target = value.split(",", 1)[0].strip()
                emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "package_list_declaration", target, True)
            elif canonical_key.endswith("package"):
                target = value.split(",", 1)[0].split(".", 1)[0].strip()
                emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "package_property", target, True)
            elif canonical_key.startswith("m_missionimages["):
                if "." in value:
                    target = value.split(".", 1)[0]
                    emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "mission_image_package_object", target, True)
                else:
                    emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "mission_image_object_without_package", value, False)
            elif canonical_key == "m_mapstobarkprofile":
                emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "configured_map_name", value.split(",", 1)[0], False)
            elif canonical_key == "m_maphintbindings":
                nested = MAP_HINT_RE.search(value)
                if nested:
                    emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "map_hint_map_name", nested.group(1), False)
            elif section.casefold() == "url" and canonical_key in {"map", "localmap", "transitionmap"}:
                target = value.strip().strip("\"'")
                for suffix in (".umap", ".upk"):
                    if target.casefold().endswith(suffix):
                        target = target[:-len(suffix)]
                        break
                emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "url_map_target", target, False)
            elif canonical_key.startswith("m_") and "." in value and not value.lstrip().startswith(("(", "[")):
                object_path = OBJECT_PATH_RE.match(value)
                if object_path:
                    target = object_path.group(1).split(".", 1)[0]
                    emit(manifest_row, line_no, section, (prefix or "") + key, raw_value, "dotted_object_reference", target, True)

    if not refs:
        raise SystemExit("no selected package/map references were parsed")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / f"{args.prefix}.csv", refs)
    write_csv(out / f"{args.prefix}-config-sources.csv", config_sources)
    counts = Counter(r["join_status"] for r in refs)
    by_kind = Counter(r["reference_kind"] for r in refs)
    unique_targets = defaultdict(set)
    for row in refs:
        unique_targets[row["reference_kind"]].add(str(row["target_name"]).casefold())
    summary = {
        "build_id": build_match.group(1), "exe_sha256": EXE_SHA256,
        "manifest_sha256": sha256_file(manifest_path),
        "ini_files_verified": len(config_sources), "upk_manifest_rows": sum(map(len, upk_by_stem.values())),
        "distinct_upk_basenames": len(upk_by_stem), "reference_rows": len(refs),
        "unique_targets_by_reference_kind": {k: len(v) for k, v in sorted(unique_targets.items())},
        "rows_by_reference_kind": dict(sorted(by_kind.items())),
        "rows_by_join_status": dict(sorted(counts.items())),
        "rows_with_exact_basename_candidates": sum(bool(json.loads(r["exact_basename_paths"])) for r in refs),
        "rows_with_plus_SF_candidates": sum(bool(json.loads(r["name_plus_SF_paths"])) for r in refs),
        "ambiguous_rows": sum(str(r["join_status"]).startswith("ambiguous") or r["join_status"] == "exact_and_plus_SF_candidates" for r in refs),
        "limitations": [
            "INI assignments are syntactic declarations; this pass does not implement Unreal configuration inheritance/merge or load-order rules.",
            "UPK basename matches are filename candidates only and do not prove a declaration is consumed or the package is loaded.",
            "The `_SF` alternative is reported as a separate candidate convention; it is not treated as an established resolver rule.",
            "Bare mission-image object names have no package prefix and remain unresolved by this basename join.",
        ],
    }
    summary_path = out / f"{args.prefix}-summary.json"
    temp = summary_path.with_suffix(summary_path.suffix + ".part")
    temp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temp.replace(summary_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
