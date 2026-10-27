#!/usr/bin/env python3
"""Compare fake-export selection and real one-object exports across classes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_UMODEL_SHA256 = "44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0"
FAKE_EXPORT_RE = re.compile(r"^Exporting\s+(\S+)\s+(.+?)\s+to\s+(.+)$", re.IGNORECASE)
WARNING_RE = re.compile(r"\bWARNING:")
ERROR_RE = re.compile(r"(?:\*{3}\s*)?\b(?:ERROR|FATAL):|Access violation", re.IGNORECASE)


def rows_from(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run(command: list[str], cwd: Path, timeout: int) -> tuple[int | str, str]:
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout + "\n" + proc.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return "timeout", stdout + "\n" + stderr


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--umodel", type=Path, required=True)
    ap.add_argument("--game-root", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--fake-census", type=Path, required=True)
    ap.add_argument("--samples", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True,
                    help="new output directory under assets/extracted")
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--timeout-seconds", type=int, default=120)
    args = ap.parse_args()

    repo = Path.cwd().resolve()
    umodel = args.umodel.resolve(strict=True)
    game_root = args.game_root.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    fake_census_path = args.fake_census.resolve(strict=True)
    samples_path = args.samples.resolve(strict=True)
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    extracted_root = (repo / "assets" / "extracted").resolve()
    try:
        output_root.relative_to(extracted_root)
    except ValueError as exc:
        raise SystemExit("--output-root must be under assets/extracted") from exc
    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output root: {output_root}")
    if report_dir.exists() and any((report_dir / name).exists() for name in ("per-object.csv", "summary.json")):
        raise SystemExit(f"refusing to overwrite existing result files in: {report_dir}")
    if sha256_file(umodel) != EXPECTED_UMODEL_SHA256:
        raise SystemExit("UModel SHA-256 does not match the pinned build")

    manifest = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in rows_from(manifest_path)
        if row["relative_path"].casefold().endswith(".upk")
    }
    fake_census = {
        row["relative_path"].replace("\\", "/").casefold(): row
        for row in rows_from(args.fake_census.resolve(strict=True).parent / "per-package.csv")
    }
    sample_rows = rows_from(samples_path)
    if len(sample_rows) != 7 or len({r["sample_id"] for r in sample_rows}) != 7:
        raise SystemExit("expected seven uniquely named sample objects")

    output_root.mkdir(parents=True, exist_ok=False)
    report_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    class_attempts: Counter[str] = Counter()

    for sample in sample_rows:
        rel = sample["relative_path"].replace("\\", "/")
        key = rel.casefold()
        if key not in manifest or key not in fake_census:
            raise SystemExit(f"sample package is absent from manifest/census: {rel}")
        source = game_root / Path(rel)
        expected = manifest[key]
        expected_sha = expected["sha256"].upper()
        source_sha = sha256_file(source)
        source_bytes = source.stat().st_size
        if source_sha != expected_sha or source_bytes != int(expected["bytes"]):
            raise SystemExit(f"source identity mismatch for sample package {rel}")

        class_counts = json.loads(fake_census[key]["class_counts_json"])
        if int(class_counts.get(sample["fake_export_class"], 0)) < 1:
            raise SystemExit(f"sample class was absent from the full fake-export census: {sample}")

        cwd = source.parent
        package_name = source.name
        fake_rc, fake_output = run(
            [str(umodel), "-game=dis", f"-path={cwd}", "-testexport", package_name],
            cwd,
            args.timeout_seconds,
        )
        fake_lines = fake_output.splitlines()
        fake_matches = []
        for line in fake_lines:
            if match := FAKE_EXPORT_RE.search(line):
                if (match.group(1).casefold() == sample["fake_export_class"].casefold()
                        and match.group(2).strip().casefold() == sample["object_name"].casefold()):
                    fake_matches.append(line)
        if len(fake_matches) != 1:
            results.append({
                "sample_id": sample["sample_id"],
                "fake_export_class": sample["fake_export_class"],
                "relative_path": rel,
                "source_sha256": source_sha,
                "object_name": sample["object_name"],
                "fake_return_code": fake_rc,
                "fake_match_count": len(fake_matches),
                "fake_warning_lines": sum(bool(WARNING_RE.search(line)) for line in fake_lines),
                "fake_error_lines": sum(bool(ERROR_RE.search(line)) for line in fake_lines),
                "real_return_code": "not_run",
                "real_warning_lines": 0,
                "real_error_lines": 0,
                "output_files_json": "[]",
                "result_status": "fake_selection_not_confirmed",
            })
            continue

        class_attempts[sample["fake_export_class"]] += 1
        destination = output_root / sample["sample_id"]
        destination.mkdir(parents=True, exist_ok=False)
        real_rc, real_output = run(
            [str(umodel), "-export", "-game=dis", f"-path={cwd}",
             f"-out={destination}", package_name, sample["object_name"]],
            cwd,
            args.timeout_seconds,
        )
        real_lines = real_output.splitlines()
        files = []
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                files.append({
                    "relative_path": path.relative_to(output_root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
        if real_rc == "timeout":
            result_status = "real_export_timeout"
        elif int(real_rc) != 0:
            result_status = "real_export_error"
        elif files:
            result_status = "file_written"
        else:
            result_status = "no_file_written"
        results.append({
            "sample_id": sample["sample_id"],
            "fake_export_class": sample["fake_export_class"],
            "relative_path": rel,
            "source_sha256": source_sha,
            "object_name": sample["object_name"],
            "fake_return_code": fake_rc,
            "fake_match_count": len(fake_matches),
            "fake_warning_lines": sum(bool(WARNING_RE.search(line)) for line in fake_lines),
            "fake_error_lines": sum(bool(ERROR_RE.search(line)) for line in fake_lines),
            "real_return_code": real_rc,
            "real_warning_lines": sum(bool(WARNING_RE.search(line)) for line in real_lines),
            "real_error_lines": sum(bool(ERROR_RE.search(line)) for line in real_lines),
            "output_files_json": json.dumps(files, separators=(",", ":")),
            "result_status": result_status,
        })
        print(f"sample={sample['sample_id']} status={result_status} files={len(files)}", flush=True)

    if len(results) != 7:
        raise SystemExit(f"expected seven result rows, got {len(results)}")
    result_path = report_dir / "per-object.csv"
    with result_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    summary = {
        "sample_count": len(results),
        "fake_selection_confirmed": sum(int(r["fake_match_count"]) == 1 for r in results),
        "real_file_written": sum(r["result_status"] == "file_written" for r in results),
        "result_status_counts": dict(Counter(r["result_status"] for r in results)),
        "fake_export_classes": sorted(class_attempts),
        "limitations": [
            "This is a selected one-object sample, not package-wide or all-install real-export coverage.",
            "A written file does not prove visual/runtime correctness or complete property/bytecode parsing.",
            "Source package identity is checked against the current build manifest; source packages are not modified.",
        ],
    }
    (report_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
