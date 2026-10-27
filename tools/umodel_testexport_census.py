#!/usr/bin/env python3
"""Measure UModel's no-file fake-export path for all installed Dishonored UPKs.

`-testexport` runs UModel's export selection/decoder path but does not write
the selected asset files. The output counts attempted fake exports and parser
diagnostics; it is not evidence that real asset serialization succeeds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_UMODEL_SHA256 = "44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0"
EXPORT_RE = re.compile(r"^Exporting\s+([A-Za-z0-9_]+)\s+(.+?)\s+to\s+", re.IGNORECASE)
PACKAGE_RE = re.compile(r"^Loading package:\s*(.*?)\s+Ver:\s+", re.IGNORECASE)
WARNING_RE = re.compile(r"\bWARNING:")
ERROR_RE = re.compile(r"(?:\*{3}\s*)?\b(?:ERROR|FATAL):|Access violation", re.IGNORECASE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def decode_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def clip_examples(values: list[str], limit: int = 3, width: int = 220) -> str:
    return " | ".join(v.strip()[:width] for v in values[:limit])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--umodel", type=Path, required=True)
    ap.add_argument("--game-root", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--pkginfo-census", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="ignored assets/extracted directory for any accidental output")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--timeout-seconds", type=int, default=90)
    ap.add_argument("--progress-every", type=int, default=25)
    args = ap.parse_args()

    repo = Path.cwd().resolve()
    umodel = args.umodel.resolve(strict=True)
    game_root = args.game_root.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    census_path = args.pkginfo_census.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    out_dir = args.out_dir.resolve()
    extracted_root = (repo / "assets" / "extracted").resolve()
    try:
        out_dir.relative_to(extracted_root)
    except ValueError as exc:
        raise SystemExit("--out-dir must stay under assets/extracted") from exc
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {output_dir}")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"refusing to use non-empty fake-export output directory: {out_dir}")

    tool_hash = sha256_file(umodel)
    if tool_hash != EXPECTED_UMODEL_SHA256:
        raise SystemExit(f"UModel hash mismatch: expected {EXPECTED_UMODEL_SHA256}, got {tool_hash}")

    manifest: dict[str, dict[str, str]] = {}
    for row in read_csv(manifest_path):
        path = row.get("relative_path", row.get("RelativePath", "")).replace("\\", "/")
        if path.casefold().endswith(".upk"):
            manifest[path.casefold()] = {
                "relative_path": path,
                "bytes": row.get("bytes", row.get("Length", "")),
                "sha256": row.get("sha256", row.get("SHA256", "")).upper(),
            }
    census = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in read_csv(census_path)
    }
    if len(manifest) != 904 or set(manifest) != set(census):
        raise SystemExit(f"expected matching 904-package sets; manifest={len(manifest)}, census={len(census)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    package_rows: list[dict[str, Any]] = []
    class_totals: Counter[str] = Counter()
    terminal_counts: Counter[str] = Counter()
    package_items = sorted(manifest.values(), key=lambda r: r["relative_path"].casefold())

    for number, item in enumerate(package_items, 1):
        relative = item["relative_path"]
        package_file = game_root / Path(relative)
        row: dict[str, Any] = {
            "relative_path": relative,
            "expected_bytes": item["bytes"],
            "observed_bytes": "",
            "expected_sha256": item["sha256"],
            "observed_sha256": "",
            "identity_match": False,
            "pkginfo_exports": census[relative.casefold()].get("exports", ""),
            "umodel_loaded": False,
            "return_code": "",
            "fake_export_requests": 0,
            "attempted_classes": 0,
            "class_counts_json": "{}",
            "warning_lines": 0,
            "error_lines": 0,
            "terminal_status": "not_run_identity_mismatch",
            "warning_samples": "",
            "error_samples": "",
        }
        if not package_file.is_file():
            row["terminal_status"] = "source_missing"
            package_rows.append(row)
            terminal_counts[row["terminal_status"]] += 1
            continue

        row["observed_bytes"] = package_file.stat().st_size
        row["observed_sha256"] = sha256_file(package_file)
        row["identity_match"] = (
            str(row["observed_bytes"]) == item["bytes"]
            and row["observed_sha256"].casefold() == item["sha256"].casefold()
            and row["observed_sha256"].casefold()
            == census[relative.casefold()].get("sha256", "").casefold()
        )
        if not row["identity_match"]:
            row["terminal_status"] = "not_run_identity_mismatch"
            package_rows.append(row)
            terminal_counts[row["terminal_status"]] += 1
            continue

        folder = package_file.parent
        command = [
            str(umodel),
            "-game=dis",
            f"-path={folder}",
            f"-out={out_dir}",
            "-testexport",
            package_file.name,
        ]
        try:
            proc = subprocess.run(
                command,
                cwd=folder,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=args.timeout_seconds,
                check=False,
            )
            combined = proc.stdout + "\n" + proc.stderr
            row["return_code"] = proc.returncode
        except subprocess.TimeoutExpired as exc:
            combined = decode_output(exc.stdout) + "\n" + decode_output(exc.stderr)
            row["return_code"] = "timeout"

        lines = combined.splitlines()
        package_names = [m.group(1).strip() for line in lines if (m := PACKAGE_RE.search(line))]
        row["umodel_loaded"] = any(Path(name).name.casefold() == package_file.name.casefold()
                                    for name in package_names)
        class_counts = Counter()
        for line in lines:
            if match := EXPORT_RE.search(line):
                class_counts[match.group(1)] += 1
        class_totals.update(class_counts)
        warnings = [line for line in lines if WARNING_RE.search(line)]
        errors = [line for line in lines if ERROR_RE.search(line)]
        row["fake_export_requests"] = sum(class_counts.values())
        row["attempted_classes"] = len(class_counts)
        row["class_counts_json"] = json.dumps(dict(sorted(class_counts.items())), separators=(",", ":"))
        row["warning_lines"] = len(warnings)
        row["error_lines"] = len(errors)
        row["warning_samples"] = clip_examples(warnings)
        row["error_samples"] = clip_examples(errors)

        if row["return_code"] == "timeout":
            row["terminal_status"] = "timed_out"
        elif int(row["return_code"]) != 0 or errors:
            row["terminal_status"] = "error"
        elif not row["umodel_loaded"]:
            row["terminal_status"] = "not_loaded"
        elif any("has no supported objects" in line.casefold() for line in lines):
            row["terminal_status"] = "no_supported_objects"
        elif warnings:
            row["terminal_status"] = "attempted_with_warnings"
        elif class_counts:
            row["terminal_status"] = "fake_export_attempts_no_reported_diagnostic"
        else:
            row["terminal_status"] = "loaded_no_fake_export_attempts"
        package_rows.append(row)
        terminal_counts[row["terminal_status"]] += 1

        if number % args.progress_every == 0 or number == len(package_items):
            print(f"processed={number}/{len(package_items)} status={dict(terminal_counts)}", flush=True)

    package_path = output_dir / "per-package.csv"
    with package_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(package_rows[0]))
        writer.writeheader()
        writer.writerows(package_rows)

    class_path = output_dir / "fake-export-attempts-by-class.csv"
    with class_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("class_name", "fake_export_request_count"))
        writer.writerows(sorted(class_totals.items(), key=lambda pair: (-pair[1], pair[0].casefold())))

    summary = {
        "scope": "904 manifest-listed UPKs in BUILD-STEAM-10256413",
        "umodel_sha256": tool_hash,
        "fake_export_mode": "-testexport; selected asset serializers are exercised without writing output files",
        "package_count": len(package_rows),
        "source_identity_matches": sum(row["identity_match"] is True for row in package_rows),
        "packages_loaded": sum(row["umodel_loaded"] is True for row in package_rows),
        "fake_export_request_count": sum(row["fake_export_requests"] for row in package_rows),
        "packages_with_fake_export_requests": sum(row["fake_export_requests"] > 0 for row in package_rows),
        "warning_lines": sum(row["warning_lines"] for row in package_rows),
        "error_lines": sum(row["error_lines"] for row in package_rows),
        "terminal_status_counts": dict(sorted(terminal_counts.items())),
        "class_count": len(class_totals),
        "limitations": [
            "Fake-export request counts are not counts of successfully serialized files.",
            "-testexport does not write assets; this is not a full disk-export validation.",
            "A zero fake-export request count only says this UModel build selected no supported resource for that package invocation.",
            "UModel parsing and fake serialization are not independent validation of original package payload semantics.",
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
