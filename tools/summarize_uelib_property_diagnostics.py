#!/usr/bin/env python3
"""Stream UELib default-property JSONL into compact diagnostic cohorts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def owner_class(path: str) -> str:
    return path.split("'", 1)[0] if "'" in path else "<untyped>"


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    property_counts: Counter[tuple[str, str, str]] = Counter()
    error_counts: Counter[tuple[str, str, str, str]] = Counter()
    diagnostic_counts: Counter[tuple[str, str, str]] = Counter()
    diagnostic_samples: dict[tuple[str, str, str], str] = {}
    rows = 0
    value_errors = 0
    diagnostic_rows = 0
    diagnostic_lines = 0
    with args.input.open("r", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            rows += 1
            package = record.get("package", "")
            cls = owner_class(record.get("ownerObjectPath", ""))
            prop = record.get("propertyName", "")
            typ = record.get("propertyType", "")
            property_counts[(cls, typ, prop)] += 1
            error = record.get("valueError")
            if error:
                value_errors += 1
                error_counts[(cls, typ, prop, str(error).splitlines()[0][:240])] += 1
            count = int(record.get("valueDiagnosticLineCount") or 0)
            if count:
                diagnostic_rows += 1
                diagnostic_lines += count
                key = (cls, typ, prop)
                diagnostic_counts[key] += 1
                sample = str(record.get("valueDiagnosticSample") or "").splitlines()
                if key not in diagnostic_samples:
                    diagnostic_samples[key] = sample[0][:240] if sample else "<no sample>"

    common = ["owner_class", "property_type", "property_name"]
    diagnostic_fields = common + ["affected_rows", "diagnostic_sample"]
    write_csv(
        args.output_dir / "property-diagnostic-cohorts.csv",
        [dict(zip(diagnostic_fields, (*key, n, diagnostic_samples[key]))) for key, n in diagnostic_counts.most_common()],
        diagnostic_fields,
    )
    error_fields = common + ["error_rows", "value_error"]
    write_csv(
        args.output_dir / "property-value-error-cohorts.csv",
        [dict(zip(error_fields, (*key[:3], n, key[3]))) for key, n in error_counts.most_common()],
        error_fields,
    )
    type_fields = common + ["row_count"]
    write_csv(
        args.output_dir / "property-field-frequency.csv",
        [dict(zip(type_fields, (*key, n))) for key, n in property_counts.most_common()],
        type_fields,
    )
    summary = {
        "input": str(args.input),
        "property_rows": rows,
        "value_error_rows": value_errors,
        "rows_with_value_diagnostics": diagnostic_rows,
        "captured_value_diagnostic_lines": diagnostic_lines,
        "distinct_property_field_groups": len(property_counts),
        "distinct_value_error_cohorts": len(error_counts),
        "distinct_diagnostic_cohorts": len(diagnostic_counts),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "diagnostic-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
