#!/usr/bin/env python3
"""Import ExportCallGraph.java CSV into knowledge/database/callgraph.sqlite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_servers.common.callgraph import SCHEMA, callgraph_path, ensure_schema
from mcp_servers.common.config import get_settings


def _norm_addr(raw: str) -> str:
    text = (raw or "").strip().replace("0x", "").replace("0X", "")
    if not text:
        return ""
    try:
        return f"{int(text, 16):08X}"
    except ValueError:
        # Ghidra emits symbolic external locations (for example
        # EXTERNAL:000001a4) and labels such as "Entry Point" for xrefs that
        # do not have a normal image VA. Preserve those endpoints verbatim;
        # callgraph queries for image functions still normalize their input
        # addresses to eight-digit hex.
        if text.upper().startswith("EXTERNAL:") or text.lower() == "entry point":
            return text.upper()
        raise ValueError(f"Unsupported Ghidra address token: {raw!r}")


def import_csv(csv_path: Path, db_path: Path | None = None) -> dict:
    settings = get_settings()
    target = db_path or callgraph_path()
    ensure_schema(target)
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)

    with sqlite3.connect(target) as db:
        db.executescript(SCHEMA)
        db.execute("DELETE FROM edges")
        db.execute("DELETE FROM meta")
        batch = []
        for row in rows:
            kind = (row.get("kind") or "call").strip().lower()
            if kind not in {"call", "data"}:
                continue
            from_addr = _norm_addr(row.get("from_addr", ""))
            to_addr = _norm_addr(row.get("to_addr", ""))
            if not from_addr or not to_addr:
                continue
            batch.append(
                (
                    kind,
                    from_addr,
                    to_addr,
                    (row.get("from_name") or "").strip(),
                    (row.get("to_name") or "").strip(),
                    _norm_addr(row.get("site_addr", "")) or "",
                )
            )
        db.executemany(
            "INSERT INTO edges(kind, from_addr, to_addr, from_name, to_name, site_addr) "
            "VALUES(?,?,?,?,?,?)",
            batch,
        )
        db.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?)",
            ("exe_sha256", settings.executable_sha256),
        )
        db.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?)",
            ("build_id", settings.build_id),
        )
        db.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?)",
            ("exported_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        )
        db.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?)",
            ("source_csv", str(csv_path)),
        )
        db.commit()
        count = db.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    return {"db": str(target), "edges": count, "csv": str(csv_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="CSV from ExportCallGraph.java")
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Output SQLite path (default: knowledge/database/callgraph.sqlite)",
    )
    args = parser.parse_args()
    if not args.csv.is_file():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 1
    result = import_csv(args.csv, args.db)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
