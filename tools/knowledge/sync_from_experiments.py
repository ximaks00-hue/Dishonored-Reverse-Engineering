#!/usr/bin/env python3
"""Sync experiment frontmatter and known Blink edges into the research SQLite DB."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mcp_servers._paths import (  # noqa: E402
    BUILD_ID,
    EXECUTABLE_SHA256,
    FUNCTIONS_CSV,
    GAME_EXE,
    IMAGE_BASE,
    RESEARCH_DB,
)

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

FUNCTION_REVIEW_OVERLAY = (
    ROOT
    / "research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0147.csv"
)


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
    # Add columns used by the regenerated progress view before executing schema.sql.
    # SQLite has no ALTER VIEW; the schema drops and rebuilds the derived view.
    for table, name, declaration in (
        ("function_analysis_runs", "is_current", "INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1))"),
        ("function_claims", "is_current", "INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1))"),
        ("function_claims", "evidence_va", "INTEGER CHECK (evidence_va IS NULL OR evidence_va >= 0)"),
        ("function_claims", "evidence_rva", "INTEGER CHECK (evidence_rva IS NULL OR evidence_rva >= 0)"),
    ):
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if exists:
            existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def pe32_image_range(path: Path) -> tuple[int, int]:
    """Return PE32 ImageBase and SizeOfImage without third-party modules."""
    with path.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError(f"not a PE executable: {path}")
        stream.seek(0x3C)
        pe_offset = struct.unpack("<I", stream.read(4))[0]
        stream.seek(pe_offset)
        if stream.read(4) != b"PE\0\0":
            raise ValueError(f"missing PE signature: {path}")
        coff = stream.read(20)
        machine, _, _, _, _, optional_size, _ = struct.unpack("<HHIIIHH", coff)
        optional = stream.read(optional_size)
        if machine != 0x14C or struct.unpack_from("<H", optional, 0)[0] != 0x10B:
            raise ValueError("expected x86 PE32 executable")
        image_base = struct.unpack_from("<I", optional, 28)[0]
        size_of_image = struct.unpack_from("<I", optional, 56)[0]
        return image_base, size_of_image


def stable_key(*parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def sync_function_evidence(db: sqlite3.Connection, build_row_id: int) -> dict[str, int]:
    """Import the exact-build index as L0 and only explicitly reviewed evidence above it."""
    exe_path = GAME_EXE.resolve(strict=True)
    actual_exe_sha = sha256_file(exe_path)
    if actual_exe_sha.upper() != EXECUTABLE_SHA256.upper():
        raise ValueError("current executable hash differs from configured exact-build identity")
    image_base, size_of_image = pe32_image_range(exe_path)
    if image_base != IMAGE_BASE:
        raise ValueError(
            f"PE ImageBase 0x{image_base:08X} differs from configured 0x{IMAGE_BASE:08X}"
        )

    index_path = FUNCTIONS_CSV.resolve(strict=True)
    index_sha = sha256_file(index_path)
    index_ref = str(index_path.relative_to(ROOT)).replace("\\", "/")
    rows: list[tuple] = []
    address_to_id: dict[int, int] = {}
    with index_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            va = int(row["address"], 16)
            size = int(row["size"])
            rva = va - image_base
            if rva < 0 or size <= 0 or rva + size > size_of_image:
                raise ValueError(
                    f"function VA/RVA range is outside the verified PE image: {row['address']}"
                )
            rows.append((
                build_row_id,
                "Dishonored.exe",
                va,
                rva,
                image_base,
                row["name"],
                row["signature"],
                size,
                index_ref,
                index_sha,
            ))
    if len(rows) != 72437:
        raise ValueError(f"expected the EXP-0041 internal-function denominator 72,437; found {len(rows)}")

    db.executemany(
        "INSERT INTO function_inventory(build_id,module,va,rva,image_base,name,signature,size_bytes,index_source,index_sha256) "
        "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(build_id,module,va) DO UPDATE SET "
        "rva=excluded.rva,image_base=excluded.image_base,name=excluded.name,signature=excluded.signature,"
        "size_bytes=excluded.size_bytes,index_source=excluded.index_source,index_sha256=excluded.index_sha256",
        rows,
    )
    for function_id, va in db.execute(
        "SELECT id,va FROM function_inventory WHERE build_id=? AND module=?", (build_row_id, "Dishonored.exe")
    ):
        address_to_id[int(va)] = int(function_id)

    exp_rows = {
        row[0]: (row[1], row[2])
        for row in db.execute("SELECT experiment_key,path,claim_status FROM experiments WHERE experiment_key IS NOT NULL")
    }
    active_analysis_keys: set[str] = set()
    active_claim_keys: set[str] = set()
    managed_function_ids: set[int] = set()
    curated_experiment_keys: set[str] = set()

    def experiment_source(experiment_key: str) -> tuple[str, str]:
        found = exp_rows.get(experiment_key)
        if not found or not found[0]:
            raise ValueError(f"function evidence references missing experiment {experiment_key}")
        rel_path = found[0]
        digest = sha256_file(ROOT / Path(rel_path))
        return rel_path, digest

    def insert_analysis(
        function_id: int,
        va: int,
        kind: str,
        tool: str,
        tool_version: str | None,
        source_ref: str,
        source_sha: str,
        summary: str,
    ) -> None:
        cache_key = stable_key(
            actual_exe_sha.upper(), "Dishonored.exe", f"0x{va:08X}", kind, tool,
            tool_version or "", "",
        )
        active_analysis_keys.add(cache_key)
        db.execute(
            "INSERT INTO function_analysis_runs(function_id,analysis_kind,tool_name,tool_version,status,input_sha256,"
            "options_sha256,cache_key,source_ref,source_sha256,summary) VALUES(?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(cache_key) DO UPDATE SET status=excluded.status,is_current=1,source_ref=excluded.source_ref,"
            "source_sha256=excluded.source_sha256,summary=excluded.summary",
            (function_id, kind, tool, tool_version, "complete", actual_exe_sha.upper(), None,
             cache_key, source_ref, source_sha, summary),
        )

    # Existing curated static roles are explicit evidence-backed claim records.
    curated = db.execute(
        "SELECT module,address,summary,source,confidence,status FROM functions WHERE module='Dishonored.exe'"
    ).fetchall()
    for module, address, statement, experiment_key, confidence, status in curated:
        va = int(address, 0)
        function_id = address_to_id.get(va)
        if function_id is None:
            raise ValueError(f"curated function address is missing from the exact-build index: {address}")
        source_ref, source_sha = experiment_source(experiment_key)
        managed_function_ids.add(function_id)
        curated_experiment_keys.add(experiment_key)
        insert_analysis(function_id, va, "manual_body_review", "Ghidra", None, source_ref, source_sha,
                        f"Existing curated static function record; claim status={status}.")
        if status not in {"confirmed", "observed", "inferred", "unknown", "superseded", "rejected"}:
            raise ValueError(f"unsupported function claim status: {status}")
        claim_key = stable_key(actual_exe_sha.upper(), module, f"0x{va:08X}", "role", experiment_key, statement)
        active_claim_keys.add(claim_key)
        db.execute(
            "INSERT INTO function_claims(function_id,claim_kind,claim_status,statement,confidence,evidence_va,evidence_rva,"
            "evidence_ref,evidence_sha256,experiment_key,pointer_provenance,claim_key) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(claim_key) DO UPDATE SET claim_status=excluded.claim_status,is_current=1,"
            "statement=excluded.statement,confidence=excluded.confidence,evidence_va=excluded.evidence_va,"
            "evidence_rva=excluded.evidence_rva,"
            "evidence_ref=excluded.evidence_ref,evidence_sha256=excluded.evidence_sha256",
            (function_id, "role", status, statement, confidence, va, va - image_base, source_ref, source_sha,
             experiment_key, "", claim_key),
        )

    # The cumulative reviewed bodies are analysis coverage only. Their subsystem labels
    # remain candidates/unassigned in the source overlay, so they are not
    # imported as confirmed semantic claims.
    overlay_path = FUNCTION_REVIEW_OVERLAY.resolve(strict=True)
    overlay_ref = str(overlay_path.relative_to(ROOT)).replace("\\", "/")
    overlay_sha = sha256_file(overlay_path)
    overlay_rows = list(csv.DictReader(overlay_path.open("r", encoding="utf-8-sig", newline="")))
    for row in overlay_rows:
        va = int(row["address"], 16)
        function_id = address_to_id.get(va)
        if function_id is None:
            raise ValueError(f"reviewed function address is missing from the exact-build index: {row['address']}")
        managed_function_ids.add(function_id)
        summary = (
            f"{row['review_status']}; static_role_candidate={row['static_role_candidate']}; "
            f"source_claim_status={row['claim_status']}"
        )
        insert_analysis(function_id, va, "manual_body_review", "Ghidra (manual review)", "not-recorded",
                        overlay_ref, overlay_sha, summary)

    current_experiment_paths = {
        str(path.relative_to(ROOT)).replace("\\", "/") for path in EXPERIMENTS.glob("EXP-*.md")
    }
    current_source_paths = current_experiment_paths | {overlay_ref}
    for (run_id, source_ref) in db.execute(
        "SELECT id,source_ref FROM function_analysis_runs WHERE source_ref LIKE 'experiments/%' OR source_ref=?",
        (overlay_ref,),
    ).fetchall():
        if source_ref not in current_source_paths:
            db.execute("UPDATE function_analysis_runs SET is_current=0 WHERE id=?", (run_id,))
    if managed_function_ids:
        placeholders = ",".join("?" for _ in managed_function_ids)
        for (run_id, cache_key) in db.execute(
            f"SELECT id,cache_key FROM function_analysis_runs WHERE function_id IN ({placeholders}) "
            "AND analysis_kind='manual_body_review' AND tool_name IN ('Ghidra','Ghidra (manual review)')",
            tuple(sorted(managed_function_ids)),
        ).fetchall():
            if cache_key not in active_analysis_keys:
                db.execute("UPDATE function_analysis_runs SET is_current=0 WHERE id=?", (run_id,))
    for (claim_id, evidence_ref) in db.execute(
        "SELECT id,evidence_ref FROM function_claims WHERE evidence_ref LIKE 'experiments/%'"
    ).fetchall():
        if evidence_ref not in current_experiment_paths:
            db.execute(
                "UPDATE function_claims SET is_current=0,claim_status='superseded' WHERE id=?",
                (claim_id,),
            )
    if managed_function_ids and curated_experiment_keys:
        f_placeholders = ",".join("?" for _ in managed_function_ids)
        e_placeholders = ",".join("?" for _ in curated_experiment_keys)
        query = (
            f"SELECT id,claim_key FROM function_claims WHERE function_id IN ({f_placeholders}) "
            f"AND claim_kind='role' AND experiment_key IN ({e_placeholders})"
        )
        params = tuple(sorted(managed_function_ids)) + tuple(sorted(curated_experiment_keys))
        for claim_id, claim_key in db.execute(query, params).fetchall():
            if claim_key not in active_claim_keys:
                db.execute(
                    "UPDATE function_claims SET is_current=0,claim_status='superseded' WHERE id=?",
                    (claim_id,),
                )

    level_counts = {
        row[0]: int(row[1])
        for row in db.execute(
            "SELECT gated_level,COUNT(*) FROM function_research_progress "
            "WHERE build_id=? GROUP BY gated_level", (BUILD_ID,)
        )
    }
    return {
        "function_indexed": len(rows),
        "function_analysis_records": int(db.execute(
            "SELECT COUNT(*) FROM function_analysis_runs a JOIN function_inventory f ON f.id=a.function_id "
            "WHERE f.build_id=? AND a.is_current=1",
            (build_row_id,),
        ).fetchone()[0]),
        "function_claims": int(db.execute(
            "SELECT COUNT(*) FROM function_claims c JOIN function_inventory f ON f.id=c.function_id "
            "WHERE f.build_id=? AND c.is_current=1",
            (build_row_id,),
        ).fetchone()[0]),
        "function_superseded_analysis_records": int(db.execute(
            "SELECT COUNT(*) FROM function_analysis_runs a JOIN function_inventory f ON f.id=a.function_id "
            "WHERE f.build_id=? AND a.is_current=0",
            (build_row_id,),
        ).fetchone()[0]),
        "function_superseded_claims": int(db.execute(
            "SELECT COUNT(*) FROM function_claims c JOIN function_inventory f ON f.id=c.function_id "
            "WHERE f.build_id=? AND c.is_current=0",
            (build_row_id,),
        ).fetchone()[0]),
        "function_edges": int(db.execute(
            "SELECT COUNT(*) FROM function_edges e JOIN function_inventory f ON f.id=e.source_function_id WHERE f.build_id=?",
            (build_row_id,),
        ).fetchone()[0]),
        "function_runtime_records": int(db.execute(
            "SELECT COUNT(*) FROM function_runtime_evidence r JOIN function_inventory f ON f.id=r.function_id WHERE f.build_id=?",
            (build_row_id,),
        ).fetchone()[0]),
        **{f"functions_{level}": level_counts.get(level, 0) for level in ("L0", "L1", "L2", "L3", "L4")},
    }


def sync() -> dict[str, int]:
    counts = {"experiments": 0, "curated_functions": 0, "edges": 0, "hypotheses": 0}
    with connect() as db:
        db.execute(
            "INSERT INTO game_build(app_id, build_id, executable_sha256, architecture) "
            "VALUES(?,?,?,?) ON CONFLICT(app_id, build_id, executable_sha256) DO NOTHING",
            ("217980", BUILD_ID, EXECUTABLE_SHA256, "x86"),
        )
        build_row_id = int(db.execute(
            "SELECT id FROM game_build WHERE app_id=? AND build_id=? AND executable_sha256=?",
            ("217980", BUILD_ID, EXECUTABLE_SHA256),
        ).fetchone()[0])

        for path in sorted(EXPERIMENTS.glob("EXP-*.md")):
            text = path.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            if not meta.get("id"):
                raise ValueError(f"experiment lacks required YAML frontmatter id: {path}")
            key = meta["id"]
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

        active_paths = {
            str(path.relative_to(ROOT)).replace("\\", "/") for path in EXPERIMENTS.glob("EXP-*.md")
        }
        for (experiment_id, path) in db.execute(
            "SELECT id,path FROM experiments WHERE path LIKE 'experiments/%'"
        ).fetchall():
            if path not in active_paths:
                db.execute(
                    "UPDATE experiments SET status='superseded',experiment_status='superseded',"
                    "claim_status='superseded' WHERE id=?",
                    (experiment_id,),
                )

        for module, address, name, summary, exp, confidence, status in FUNCTIONS:
            db.execute(
                "INSERT INTO functions(module, name, address, summary, source, confidence, status, experiment_key) "
                "VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(module, address) DO UPDATE SET "
                "name=excluded.name, summary=excluded.summary, source=excluded.source, "
                "confidence=excluded.confidence, status=excluded.status, experiment_key=excluded.experiment_key",
                (module, name, address, summary, exp, confidence, status, exp),
            )
            counts["curated_functions"] += 1

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

        counts.update(sync_function_evidence(db, build_row_id))

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
