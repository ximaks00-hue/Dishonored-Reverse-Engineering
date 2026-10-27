"""Composite context packs for agents (snapshots; EXP markdown remains source of truth)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp_servers.common import callgraph, decompile_cache
from mcp_servers.common.address import normalize_function_entry
from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import FunctionIndex
from mcp_servers.common.database import connect, row_dicts
from mcp_servers.common.errors import ToolError
from mcp_servers.common.fts import search_fts

_ADDR_RE = re.compile(r"0x[0-9A-Fa-f]{6,8}|[0-9A-Fa-f]{8}")
_functions = FunctionIndex()


def research_summary() -> dict[str, Any]:
    settings = get_settings()
    with connect(write=False) as db:
        claims = row_dicts(
            db.execute(
                "SELECT claim_status AS status, COUNT(*) AS count FROM experiments "
                "GROUP BY claim_status ORDER BY count DESC"
            ).fetchall()
        )
        edges = row_dicts(
            db.execute(
                "SELECT status, COUNT(*) AS count FROM evidence_edges "
                "GROUP BY status ORDER BY status"
            ).fetchall()
        )
        open_edges = row_dicts(
            db.execute(
                "SELECT edge_key, summary, experiment_key, status FROM evidence_edges "
                "WHERE status IN ('open', 'unknown', 'inferred') ORDER BY edge_key"
            ).fetchall()
        )
    return {
        "build_id": settings.build_id,
        "claim_status_counts": claims,
        "edge_status_counts": edges,
        "open_edges": open_edges,
        "note": "Markdown experiments remain the source of truth.",
    }


def brief(topic: str) -> dict[str, Any]:
    topic = (topic or "").strip()
    if not topic:
        raise ToolError("invalid_query", "topic must be non-empty")
    settings = get_settings()
    topic_l = topic.casefold()
    with connect(write=False) as db:
        edges = row_dicts(
            db.execute(
                "SELECT edge_key, source_node, target_node, status, summary, experiment_key "
                "FROM evidence_edges ORDER BY edge_key"
            ).fetchall()
        )
        if topic_l in {"blink", "activation", "e1", "power"}:
            relevant_edges = edges
        else:
            relevant_edges = [
                e
                for e in edges
                if topic_l in (e.get("summary") or "").casefold()
                or topic_l in (e.get("edge_key") or "").casefold()
                or topic_l in (e.get("source_node") or "").casefold()
                or topic_l in (e.get("target_node") or "").casefold()
            ]
            if not relevant_edges:
                relevant_edges = edges[:10]

        exp_keys = sorted(
            {
                e["experiment_key"]
                for e in relevant_edges
                if e.get("experiment_key")
            }
        )
        experiments: list[dict[str, Any]] = []
        if exp_keys:
            placeholders = ",".join("?" * len(exp_keys))
            experiments = row_dicts(
                db.execute(
                    f"SELECT experiment_key, title, experiment_status, claim_status, path "
                    f"FROM experiments WHERE experiment_key IN ({placeholders}) "
                    f"ORDER BY experiment_key",
                    exp_keys,
                ).fetchall()
            )

        fts_hits = search_fts(topic, limit=15)
        function_rows: list[dict[str, Any]] = []
        addr_hits = _ADDR_RE.findall(topic)
        for raw in addr_hits[:5]:
            try:
                function_rows.append(_functions.get(raw))
            except ToolError:
                continue
        if not function_rows:
            for hit in fts_hits:
                if hit.get("kind") != "function":
                    continue
                key = str(hit.get("key") or "")
                if "!" in key:
                    address = key.split("!", 1)[1]
                    try:
                        function_rows.append(_functions.get(address))
                    except ToolError:
                        function_rows.append(
                            {
                                "address": address,
                                "name": hit.get("title", ""),
                                "summary": hit.get("body", ""),
                                "source": "research_db",
                            }
                        )
                if len(function_rows) >= 12:
                    break

    by_status: dict[str, list[str]] = {
        "confirmed": [],
        "open": [],
        "rejected": [],
        "other": [],
    }
    for edge in relevant_edges:
        status = (edge.get("status") or "other").casefold()
        bucket = status if status in by_status else "other"
        by_status[bucket].append(edge["edge_key"])

    return {
        "topic": topic,
        "build_id": settings.build_id,
        "note": "Snapshot from SQLite mirror; read linked EXP markdown for claims.",
        "edges": relevant_edges[:20],
        "edge_status_groups": by_status,
        "experiments": experiments[:20],
        "functions": function_rows[:15],
        "fts_hits": fts_hits[:10],
    }


def function_dossier(address: str) -> dict[str, Any]:
    function = _functions.get(address)
    key = normalize_function_entry(function["address"])
    missing: list[str] = []
    callers_payload: dict[str, Any] | None = None
    callees_payload: dict[str, Any] | None = None
    try:
        callers_payload = callgraph.callers(function["address"], limit=30)
        callees_payload = callgraph.callees(function["address"], limit=30)
    except ToolError as exc:
        if exc.code == "index_missing":
            missing.append("callgraph")
            callers_payload = {"available": False, "error": exc.to_dict()["error"]}
            callees_payload = {"available": False, "error": exc.to_dict()["error"]}
        else:
            raise

    cached = decompile_cache.load(function["address"])
    if cached is None:
        missing.append("decompile_cache")

    with connect(write=False) as db:
        mentions = row_dicts(
            db.execute(
                "SELECT experiment_key, title, claim_status, experiment_status, path "
                "FROM experiments WHERE procedure LIKE ? OR result LIKE ? OR title LIKE ? "
                "ORDER BY experiment_key LIMIT 20",
                (f"%{key}%", f"%{key}%", f"%{key}%"),
            ).fetchall()
        )
        # Also match 0x-prefixed form.
        va = function["address"]
        if va:
            extra = row_dicts(
                db.execute(
                    "SELECT experiment_key, title, claim_status, experiment_status, path "
                    "FROM experiments WHERE procedure LIKE ? OR result LIKE ? "
                    "ORDER BY experiment_key LIMIT 20",
                    (f"%{va}%", f"%{va}%"),
                ).fetchall()
            )
            seen = {m.get("experiment_key") for m in mentions}
            for row in extra:
                if row.get("experiment_key") not in seen:
                    mentions.append(row)

        db_fn = row_dicts(
            db.execute(
                "SELECT module, name, address, summary, status, experiment_key, confidence "
                "FROM functions WHERE address LIKE ? LIMIT 5",
                (f"%{key[-6:]}%",),
            ).fetchall()
        )

    return {
        "function": function,
        "research_function_rows": db_fn,
        "callers": callers_payload,
        "callees": callees_payload,
        "decompile": cached,
        "experiments": mentions[:20],
        "missing": missing,
        "note": "Does not elevate claim status; EXP markdown is authoritative.",
    }


def experiment(experiment_id: str, *, include_body: bool = False) -> dict[str, Any]:
    key = (experiment_id or "").strip()
    if not key:
        raise ToolError("invalid_input", "experiment_id is required")
    settings = get_settings()
    with connect(write=False) as db:
        row = db.execute(
            "SELECT experiment_key, title, experiment_status, claim_status, game_build, "
            "path, procedure, result, status "
            "FROM experiments WHERE experiment_key = ? OR cast(id AS text) = ? "
            "LIMIT 1",
            (key, key),
        ).fetchone()
    if row is None:
        # Fall back to filesystem for unsynced EXP.
        path = _resolve_experiment_path(key)
        if path is None:
            raise ToolError(
                "experiment_not_found",
                f"No experiment mirror row or file for {key}",
                experiment_id=key,
            )
        payload: dict[str, Any] = {
            "experiment_key": key,
            "path": str(path.relative_to(settings.root)).replace("\\", "/"),
            "source": "filesystem",
            "frontmatter_hint": "DB row missing; open the markdown file",
        }
        if include_body:
            payload["body"] = path.read_text(encoding="utf-8", errors="replace")
        return payload

    data = dict(row)
    data["source"] = "research_db"
    path_str = data.get("path") or ""
    path = (settings.root / path_str).resolve() if path_str else _resolve_experiment_path(
        data.get("experiment_key") or key
    )
    if path is not None and path.is_file():
        data["path_resolved"] = str(path)
        if include_body:
            data["body"] = path.read_text(encoding="utf-8", errors="replace")
        else:
            # Frontmatter-only peek: first YAML block.
            text = path.read_text(encoding="utf-8", errors="replace")
            if text.startswith("---"):
                end = text.find("\n---", 3)
                data["frontmatter"] = text[: end + 4] if end != -1 else text[:400]
            else:
                data["frontmatter"] = ""
            data.pop("procedure", None)
            data.pop("result", None)
    elif include_body:
        data["body"] = data.get("procedure", "")
    else:
        data.pop("procedure", None)
        data.pop("result", None)
    return data


def _resolve_experiment_path(key: str) -> Path | None:
    settings = get_settings()
    experiments = settings.root / "experiments"
    if not experiments.is_dir():
        return None
    # EXP-0001 or EXP-0001-slug
    normalized = key.upper() if key.upper().startswith("EXP-") else key
    matches = sorted(experiments.glob(f"{normalized}*.md"))
    if matches:
        return matches[0]
    matches = sorted(experiments.glob(f"*{key}*.md"))
    return matches[0] if matches else None
