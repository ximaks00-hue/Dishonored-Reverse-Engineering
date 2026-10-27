#!/usr/bin/env python3
"""Build a metadata-only UModel census for every installed Dishonored UPK.

UModel resolves wildcard packages within one directory, so the installed
CookedPCConsole directory and each DLC directory are queried separately.
Original package files are read only; the CSV contains parser summaries plus
manifest identity, not exported game data.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
from collections import Counter
from pathlib import Path

SUMMARY_RE = re.compile(
    r"Loading package:\s*(.*?)\s+Ver:\s+(\S+)\s+Engine:\s+(\d+)"
    r"\s+Names:\s+(\d+)\s+Exports:\s+(\d+)\s+Imports:\s+(\d+)"
    r"\s+Game:\s+(\d+)"
)
WARNING_RE = re.compile(r"WARNING:\s*([^:]+):")
ERROR_RE = re.compile(r"(?:ERROR|FATAL):\s*([^:]+):")


def run_folder(umodel: Path, game_root: Path, relative_folder: str) -> tuple[str, str]:
    folder = game_root / Path(relative_folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"package directory not found: {folder}")
    proc = subprocess.run(
        [str(umodel), "-game=dis", f"-path={folder}", "-pkginfo", "*.upk"],
        cwd=folder,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = proc.stdout + "\n" + proc.stderr
    if proc.returncode != 0:
        raise RuntimeError(
            f"UModel failed for {folder} (exit {proc.returncode}): "
            + output[-2000:]
        )
    return relative_folder.replace("\\", "/").rstrip("/") + "/", output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--umodel", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--package-index-output", type=Path)
    args = parser.parse_args()

    umodel = args.umodel.resolve(strict=True)
    game_root = args.game_root.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True)

    folders = [
        "DishonoredGame/CookedPCConsole",
        "DishonoredGame/DLC/PCConsole/DLC05",
        "DishonoredGame/DLC/PCConsole/DLC06",
        "DishonoredGame/DLC/PCConsole/DLC07",
    ]
    package_metadata: dict[str, dict[str, object]] = {}
    warning_counts: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()
    folder_outputs: dict[str, str] = {}

    for relative_folder in folders:
        prefix, output = run_folder(umodel, game_root, relative_folder)
        folder_outputs[prefix] = output
        for match in SUMMARY_RE.finditer(output):
            name, version, engine, names, exports, imports, game = match.groups()
            key = f"{prefix}{name}".casefold()
            package_metadata[key] = {
                "package_version": version,
                "engine": engine,
                "names": names,
                "exports": exports,
                "imports": imports,
                "game": game,
            }
        for line in output.splitlines():
            match = WARNING_RE.search(line)
            if match:
                warning_counts[f"{prefix}{match.group(1)}".casefold()] += 1
            match = ERROR_RE.search(line)
            if match:
                error_counts[f"{prefix}{match.group(1)}".casefold()] += 1

    output_rows: list[dict[str, object]] = []
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            relative_path = item["relative_path"].replace("\\", "/")
            if not relative_path.casefold().endswith(".upk"):
                continue
            relative_lower = relative_path.casefold()
            if not any(relative_lower.startswith(f"{folder}/".casefold()) for folder in folders):
                continue

            metadata = package_metadata.get(relative_lower)
            warning_count = warning_counts[relative_lower]
            error_count = error_counts[relative_lower]
            if metadata is None:
                status = "not_loaded"
            elif error_count:
                status = "loaded_with_errors"
            elif warning_count:
                status = "loaded_with_warnings"
            else:
                status = "loaded"

            output_rows.append(
                {
                    "relative_path": relative_path,
                    "bytes": item["bytes"],
                    "sha256": item["sha256"],
                    "pkginfo_status": status,
                    "package_version": metadata.get("package_version", "") if metadata else "",
                    "engine": metadata.get("engine", "") if metadata else "",
                    "names": metadata.get("names", "") if metadata else "",
                    "exports": metadata.get("exports", "") if metadata else "",
                    "imports": metadata.get("imports", "") if metadata else "",
                    "game": metadata.get("game", "") if metadata else "",
                    "warning_lines": warning_count,
                    "error_lines": error_count,
                }
            )

    output_rows.sort(key=lambda row: str(row["relative_path"]).casefold())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "relative_path",
        "bytes",
        "sha256",
        "pkginfo_status",
        "package_version",
        "engine",
        "names",
        "exports",
        "imports",
        "game",
        "warning_lines",
        "error_lines",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)

    if args.package_index_output is not None:
        args.package_index_output.parent.mkdir(parents=True, exist_ok=True)
        with args.package_index_output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("RelativePath", "Length", "SHA256"))
            for row in output_rows:
                writer.writerow((row["relative_path"], row["bytes"], row["sha256"]))

    statuses = Counter(str(row["pkginfo_status"]) for row in output_rows)
    engines = Counter(str(row["engine"]) for row in output_rows if row["engine"])
    total_warnings = sum(int(row["warning_lines"]) for row in output_rows)
    total_errors = sum(int(row["error_lines"]) for row in output_rows)
    print(f"Packages in manifest scope: {len(output_rows)}")
    print(f"Package statuses: {dict(sorted(statuses.items()))}")
    print(f"Engine metadata counts: {dict(sorted(engines.items()))}")
    print(f"Warning lines: {total_warnings}; error lines: {total_errors}")
    print(f"Census: {args.output.resolve()}")
    if args.package_index_output is not None:
        print(f"Package index: {args.package_index_output.resolve()}")


if __name__ == "__main__":
    main()
