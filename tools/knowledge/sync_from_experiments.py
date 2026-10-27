#!/usr/bin/env python3
"""Sync experiment frontmatter and known Blink edges into the research SQLite DB."""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mcp_servers._paths import BUILD_ID, EXECUTABLE_SHA256, RESEARCH_DB  # noqa: E402

EXPERIMENTS = ROOT / "experiments"
SCHEMA = ROOT / "knowledge" / "database" / "schema.sql"
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)

# Seeded activation-graph edges (docs/gameplay/blink/activation-graph.md).
EDGES = [
    ("E1", "Scaleform.onSelectionChanged", "PowerWheel.OnSelectionChanged", "confirmed", "UI int bridge", "EXP-0019"),
    ("E2", "PowerWheel.+0x1F0", "UpdateItemInfos", "confirmed", "UI refresh only", "EXP-0021"),
    ("E3", "Dis_SelectPower", "FUN_00B51790", "confirmed", "selection/state, not activation", "EXP-0021"),
    ("E4", "Controller.shortcutUse", "Blink.activation", "open", "no static edge", "EXP-0027"),
    ("E5", "DisItemContext_UsePower.+0x134", "Blink.+0x1AC", "confirmed", "static UsePower→move-mode", "EXP-0028"),
    ("E6", "Blink.moveMode", "Pawn.position", "confirmed", "gated write +0xC4/C8/CC", "EXP-0024"),
    ("E7", "Player.inputOrAnim", "UsePowerOrBlink.+0x340", "open", "caller unknown", "EXP-0028"),
    ("E8", "FUN_00C0CA70", "DisItemContext_UsePower", "open", "open/weakened: receiver unproved; callers weaken Use claim", "EXP-0032"),
    ("E9", "PlayerPawn.manager+0x59C", "DisItemContext_UsePower", "rejected", "ABI incompatible with known UsePower targets; manager path itself is real", "EXP-0037"),
    ("E10", "FUN_00B36CA0", "Blink.activation", "open", "keyed registry unjoined", "EXP-0036"),
]

FUNCTIONS = [
    ("Dishonored.exe", "0x00AB4680", "Dis_SelectPower_target", "Controller +0x560 target", "EXP-0021", 0.9, "confirmed"),
    ("Dishonored.exe", "0x00BCD800", "PowerWheel_OnSelectionChanged_target", "PowerWheel +0x1F0 target", "EXP-0021", 0.9, "confirmed"),
    ("Dishonored.exe", "0x00BFC990", "Blink_set_move_mode", "Blink +0x1AC move-mode entry", "EXP-0024", 0.9, "confirmed"),
    ("Dishonored.exe", "0x00C44D30", "UsePower_slot_134", "DisItemContext_UsePower +0x134", "EXP-0028", 0.9, "confirmed"),
    ("Dishonored.exe", "0x00C0CA70", "keyed_0x30_dispatcher", "0x30-stride array dispatcher", "EXP-0032", 0.5, "observed"),
    ("Dishonored.exe", "0x00C04C30", "pawn_manager_dispatch", "Pawn manager virtual dispatch", "EXP-0037", 0.7, "observed"),
    ("Dishonored.exe", "0x00B36CA0", "keyed_callback_register", "Shared keyed callback helper", "EXP-0036", 0.7, "observed"),
]

HYPOTHESES = [
    (
        "Input reaches UsePower +0x134 or Blink +0x340",
        "Player Use / CastBlink / animation event eventually calls into the confirmed UsePower→Blink move-mode bridge.",
        "build 10256413 Blink activation",
        0.4,
        "open",
        "EXP-0028",
    ),
    (
        "FUN_00C0CA70 dispatches live UsePower contexts",
        "The 0x30-stride dispatcher selects DisItemContext_UsePower instances for user power use.",
        "build 10256413",
        0.2,
        "open",
        "EXP-0032",
    ),
    (
        "PlayerPawn +0x59C manager is Blink Use dispatch",
        "Rejected: observed call ABI incompatible with known UsePower targets.",
        "build 10256413",
        0.05,
        "rejected",
        "EXP-0037",
    ),
]


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def connect() -> sqlite3.Connection:
    RESEARCH_DB.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(RESEARCH_DB)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    # Migrate older DBs that predate new columns.
    columns = {
        "experiments": {
            "experiment_key": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'observed'",
            "experiment_status": "TEXT NOT NULL DEFAULT 'done'",
            "claim_status": "TEXT NOT NULL DEFAULT 'observed'",
            "path": "TEXT NOT NULL DEFAULT ''",
        },
        "functions": {
            "status": "TEXT NOT NULL DEFAULT 'observed'",
            "experiment_key": "TEXT",
        },
        "hypotheses": {"experiment_key": "TEXT"},
    }
    for table, specs in columns.items():
        existing = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, decl in specs.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_experiments_key_unique "
        "ON experiments(experiment_key) WHERE experiment_key IS NOT NULL"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_edges_status ON evidence_edges(status)"
    )
    return connection


def sync() -> dict[str, int]:
    counts = {"experiments": 0, "functions": 0, "edges": 0, "hypotheses": 0}
    with connect() as db:
        db.execute(
            "INSERT INTO game_build(app_id, build_id, executable_sha256, architecture) "
            "VALUES(?,?,?,?) ON CONFLICT(app_id, build_id, executable_sha256) DO NOTHING",
            ("217980", BUILD_ID, EXECUTABLE_SHA256, "x86"),
        )

        for path in sorted(EXPERIMENTS.glob("EXP-*.md")):
            text = path.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            parts = path.stem.split("-")
            key = meta.get("id") or (f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else path.stem)
            title = meta.get("title") or path.stem
            experiment_status = meta.get("experiment_status") or meta.get("status") or "done"
            claim_status = meta.get("claim_status") or "observed"
            # Legacy single status column stores claim_status for search compatibility.
            status = claim_status
            build = meta.get("build") or BUILD_ID
            question = meta.get("question") or ""
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            existing = db.execute(
                "SELECT id FROM experiments WHERE experiment_key = ?", (key,)
            ).fetchone()
            if existing:
                db.execute(
                    "UPDATE experiments SET title=?, procedure=?, game_build=?, status=?, "
                    "experiment_status=?, claim_status=?, path=? WHERE experiment_key=?",
                    (
                        title,
                        question,
                        build,
                        status,
                        experiment_status,
                        claim_status,
                        rel,
                        key,
                    ),
                )
            else:
                db.execute(
                    "INSERT INTO experiments(experiment_key, title, procedure, result, game_build, "
                    "status, experiment_status, claim_status, path) VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        key,
                        title,
                        question,
                        "",
                        build,
                        status,
                        experiment_status,
                        claim_status,
                        rel,
                    ),
                )
            counts["experiments"] += 1

        for module, address, name, summary, exp, confidence, status in FUNCTIONS:
            db.execute(
                "INSERT INTO functions(module, name, address, summary, source, confidence, status, experiment_key) "
                "VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(module, address) DO UPDATE SET "
                "name=excluded.name, summary=excluded.summary, source=excluded.source, "
                "confidence=excluded.confidence, status=excluded.status, experiment_key=excluded.experiment_key",
                (module, name, address, summary, exp, confidence, status, exp),
            )
            counts["functions"] += 1

        for edge_key, source, target, status, summary, exp in EDGES:
            existing = db.execute(
                "SELECT id FROM evidence_edges WHERE edge_key = ?", (edge_key,)
            ).fetchone()
            if existing:
                db.execute(
                    "UPDATE evidence_edges SET source_node=?, target_node=?, status=?, summary=?, "
                    "experiment_key=?, updated_at=CURRENT_TIMESTAMP WHERE edge_key=?",
                    (source, target, status, summary, exp, edge_key),
                )
            else:
                db.execute(
                    "INSERT INTO evidence_edges(edge_key, source_node, target_node, status, summary, experiment_key) "
                    "VALUES(?,?,?,?,?,?)",
                    (edge_key, source, target, status, summary, exp),
                )
            counts["edges"] += 1

        existing_titles = {
            row[0] for row in db.execute("SELECT title FROM hypotheses").fetchall()
        }
        for title, claim, scope, confidence, status, exp in HYPOTHESES:
            if title in existing_titles:
                db.execute(
                    "UPDATE hypotheses SET claim=?, scope=?, confidence=?, status=?, experiment_key=? WHERE title=?",
                    (claim, scope, confidence, status, exp, title),
                )
            else:
                db.execute(
                    "INSERT INTO hypotheses(title, claim, scope, confidence, status, experiment_key) "
                    "VALUES(?,?,?,?,?,?)",
                    (title, claim, scope, confidence, status, exp),
                )
            counts["hypotheses"] += 1

        db.commit()
    return counts


def main() -> int:
    counts = sync()
    print(f"Synced into {RESEARCH_DB}")
    for key, value in counts.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
