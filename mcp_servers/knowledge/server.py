"""Dishonored knowledge MCP — SQLite research mirror (not source of truth)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from mcp_servers.common import agent_packs
from mcp_servers.common.address import clamp_limit
from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import PackageIndex
from mcp_servers.common.database import connect, row_dicts
from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.errors import ToolError
from mcp_servers.common.fts import rebuild_fts, search_fts
from mcp_servers.common.logging_setup import configure_logging

_log = configure_logging("knowledge")
_settings = get_settings()
_packages = PackageIndex()


def _require_confidence(confidence: float) -> float:
    if not 0 <= confidence <= 1:
        raise ToolError(
            "invalid_confidence",
            "confidence must be between 0 and 1",
            confidence=confidence,
        )
    return confidence


def _health_payload() -> dict[str, Any]:
    report = _settings.path_report()
    report["server"] = "dishonored-research"
    report["version"] = "2.1.0"
    with connect(write=False) as db:
        report["counts"] = {
            "experiments": db.execute("SELECT COUNT(*) FROM experiments").fetchone()[0],
            "functions": db.execute("SELECT COUNT(*) FROM functions").fetchone()[0],
            "hypotheses": db.execute("SELECT COUNT(*) FROM hypotheses").fetchone()[0],
            "evidence": db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0],
            "evidence_edges": db.execute(
                "SELECT COUNT(*) FROM evidence_edges"
            ).fetchone()[0],
            "game_build": db.execute("SELECT COUNT(*) FROM game_build").fetchone()[0],
            "research_fts": db.execute("SELECT COUNT(*) FROM research_fts").fetchone()[0],
        }
    report["ready"] = _settings.schema_sql.is_file()
    return report


@mcp_tool(_log)
def health() -> dict[str, Any]:
    return _health_payload()


@mcp_tool(_log)
def search_research(query: str, limit: int = 20) -> list[dict]:
    return search_fts(query, limit=clamp_limit(limit, maximum=100))


@mcp_tool(_log)
def rebuild_research_fts() -> dict[str, Any]:
    with connect() as db:
        count = rebuild_fts(db)
    return {"rows": count}


@mcp_tool(_log)
def research_summary() -> dict[str, Any]:
    return agent_packs.research_summary()


@mcp_tool(_log)
def brief(topic: str) -> dict[str, Any]:
    return agent_packs.brief(topic)


@mcp_tool(_log)
def function_dossier(address: str) -> dict[str, Any]:
    return agent_packs.function_dossier(address)


@mcp_tool(_log)
def experiment(experiment_id: str, include_body: bool = False) -> dict[str, Any]:
    return agent_packs.experiment(experiment_id, include_body=include_body)


@mcp_tool(_log)
def list_game_builds() -> list[dict]:
    with connect(write=False) as db:
        return row_dicts(
            db.execute(
                "SELECT app_id, build_id, executable_sha256, architecture, recorded_at "
                "FROM game_build ORDER BY id DESC"
            ).fetchall()
        )


@mcp_tool(_log)
def list_evidence_edges(status: str = "") -> list[dict]:
    with connect(write=False) as db:
        if status:
            rows = db.execute(
                "SELECT edge_key, source_node, target_node, status, summary, experiment_key "
                "FROM evidence_edges WHERE status = ? ORDER BY edge_key",
                (status,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT edge_key, source_node, target_node, status, summary, experiment_key "
                "FROM evidence_edges ORDER BY edge_key"
            ).fetchall()
    return row_dicts(rows)


@mcp_tool(_log)
def list_experiments(query: str = "", limit: int = 50) -> list[dict]:
    limit = clamp_limit(limit)
    pattern = f"%{query}%"
    with connect(write=False) as db:
        rows = db.execute(
            "SELECT experiment_key, title, experiment_status, claim_status, game_build, path, "
            "procedure AS question FROM experiments "
            "WHERE coalesce(experiment_key,'') LIKE ? OR title LIKE ? OR procedure LIKE ? "
            "ORDER BY experiment_key LIMIT ?",
            (pattern, pattern, pattern, limit),
        ).fetchall()
    return row_dicts(rows)


@mcp_tool(_log)
def search_assets(query: str, limit: int = 30) -> list[dict]:
    if not query.strip():
        raise ToolError("invalid_query", "query must be non-empty")
    return _packages.search(query, limit=clamp_limit(limit, maximum=100), upk_only=False)


@mcp_tool(_log)
def record_hypothesis(
    title: str, claim: str, scope: str = "", confidence: float = 0.25
) -> dict:
    if not title.strip() or not claim.strip():
        raise ToolError("invalid_input", "title and claim are required")
    confidence = _require_confidence(confidence)
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO hypotheses(title, claim, scope, confidence) VALUES(?,?,?,?)",
            (title, claim, scope, confidence),
        )
        return {"id": cursor.lastrowid, "status": "open", "title": title}


@mcp_tool(_log)
def attach_evidence(
    hypothesis_id: int,
    source_type: str,
    source_ref: str,
    observation: str,
    confidence: float = 0.5,
) -> dict:
    confidence = _require_confidence(confidence)
    if hypothesis_id < 1:
        raise ToolError("invalid_input", "hypothesis_id must be positive")
    with connect() as db:
        exists = db.execute(
            "SELECT 1 FROM hypotheses WHERE id = ?", (hypothesis_id,)
        ).fetchone()
        if exists is None:
            raise ToolError(
                "hypothesis_not_found",
                f"No hypothesis with id={hypothesis_id}",
                hypothesis_id=hypothesis_id,
            )
        cursor = db.execute(
            "INSERT INTO evidence(hypothesis_id,source_type,source_ref,observation,confidence) "
            "VALUES(?,?,?,?,?)",
            (hypothesis_id, source_type, source_ref, observation, confidence),
        )
        return {
            "id": cursor.lastrowid,
            "hypothesis_id": hypothesis_id,
            "source_ref": source_ref,
        }


@mcp_tool(_log)
def record_function(
    module: str,
    address: str,
    name: str = "",
    signature: str = "",
    summary: str = "",
    source: str = "",
    confidence: float = 0.5,
) -> dict:
    confidence = _require_confidence(confidence)
    if not module.strip() or not address.strip():
        raise ToolError("invalid_input", "module and address are required")
    with connect() as db:
        db.execute(
            "INSERT INTO functions(module,name,address,signature,summary,source,confidence) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(module,address) DO UPDATE SET "
            "name=excluded.name, signature=excluded.signature, summary=excluded.summary, "
            "source=excluded.source, confidence=excluded.confidence",
            (module, name or None, address, signature, summary, source, confidence),
        )
        return {
            "module": module,
            "address": address,
            "name": name,
            "confidence": confidence,
        }


@mcp_tool(_log)
def record_experiment(
    title: str,
    procedure: str,
    result: str = "",
    game_build: str = "",
    save_id: str = "",
    experiment_key: str = "",
    status: str = "observed",
    experiment_status: str = "done",
    claim_status: str = "",
) -> dict:
    if not title.strip():
        raise ToolError("invalid_input", "title is required")
    build = game_build or _settings.build_id
    claim = claim_status or status
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO experiments(title,procedure,result,game_build,save_id,experiment_key,"
            "status,experiment_status,claim_status) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                title,
                procedure,
                result,
                build,
                save_id,
                experiment_key or None,
                claim,
                experiment_status,
                claim,
            ),
        )
        return {
            "id": cursor.lastrowid,
            "game_build": build,
            "experiment_key": experiment_key or None,
            "experiment_status": experiment_status,
            "claim_status": claim,
        }


def register(server: MCPServer, *, include_health: bool = True) -> None:
    if include_health:
        server.add_tool(health, description="Report DB/schema readiness and table counts.")
    server.add_tool(
        search_research,
        description="FTS5 search across experiments, functions, and evidence edges.",
    )
    server.add_tool(
        rebuild_research_fts,
        description="Rebuild the research FTS5 index from mirror tables.",
    )
    server.add_tool(
        research_summary,
        description="Counts by claim/edge status for a fast research snapshot.",
    )
    server.add_tool(
        brief,
        description="Agent pack: open edges, related EXP, and functions for a topic.",
    )
    server.add_tool(
        function_dossier,
        description="Agent pack: function index + callers/callees + cached decompile + EXP mentions.",
    )
    server.add_tool(
        experiment,
        description="Agent pack: experiment frontmatter/path (include_body for full markdown).",
    )
    server.add_tool(list_game_builds, description="List recorded executable builds.")
    server.add_tool(
        list_evidence_edges,
        description="List Blink activation evidence edges; optional status filter.",
    )
    server.add_tool(list_experiments, description="List synced experiment records.")
    server.add_tool(
        search_assets,
        description="Search package index paths without reading package contents.",
    )
    server.add_tool(
        record_hypothesis, description="Add an explicitly unconfirmed research hypothesis."
    )
    server.add_tool(
        attach_evidence, description="Attach a traceable observation to a hypothesis."
    )
    server.add_tool(
        record_function, description="Upsert a binary function record by module+address."
    )
    server.add_tool(
        record_experiment, description="Insert an experiment row into the mirror DB."
    )


def create_server() -> MCPServer:
    mcp = MCPServer(
        name="dishonored-research",
        version="2.1.0",
        instructions=(
            "Search and update the SQLite research mirror for Dishonored RE. "
            "Prefer brief / function_dossier / experiment for agent context. "
            "Experiment markdown remains the source of truth; never promote an "
            "unverified hypothesis to fact."
        ),
    )
    register(mcp, include_health=True)
    return mcp


server = create_server()


if __name__ == "__main__":
    with connect():
        pass
    _log.info("starting dishonored-research MCP (stdio)")
    server.run("stdio")
