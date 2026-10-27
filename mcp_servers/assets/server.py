"""Dishonored assets MCP — UModel package inspection/export (read-mostly)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from mcp_servers.common import package_cache
from mcp_servers.common.address import clamp_limit
from mcp_servers.common.config import get_settings
from mcp_servers.common.csv_index import PackageIndex, ensure_under
from mcp_servers.common.decorators import mcp_tool
from mcp_servers.common.logging_setup import configure_logging
from mcp_servers.common.pkginfo import parse_pkginfo
from mcp_servers.common.umodel import run_umodel

_log = configure_logging("assets")
_settings = get_settings()
_packages = PackageIndex()


def _health_payload() -> dict[str, Any]:
    report = _settings.path_report()
    report["server"] = "dishonored-assets"
    report["version"] = "2.2.0"
    report["ready"] = all(
        report["paths"][key]["exists"]
        for key in ("game_root", "cooked", "packages_index", "umodel_exe")
    )
    report["package_cache_db"] = str(_settings.package_cache_db)
    return report


@mcp_tool(_log)
def health() -> dict[str, Any]:
    return _health_payload()


@mcp_tool(_log)
def list_packages(query: str = "", limit: int = 50) -> list[dict[str, str]]:
    return _packages.search(query, limit=clamp_limit(limit))


@mcp_tool(_log)
def get_package_info(package: str) -> dict[str, Any]:
    row = _packages.resolve_upk(package)
    filename = Path(row["RelativePath"]).name
    catalog = package_cache.get_catalog_package(row["RelativePath"])
    if catalog is not None:
        return {
            "package": row["RelativePath"],
            "parsed": {
                "package_version": catalog["package_version"],
                "engine": catalog["engine"],
                "names": catalog["names"],
                "exports": catalog["exports"],
                "imports": catalog["imports"],
                "game": catalog["game"],
            },
            "object_count": catalog["object_count"],
            "cache_hit": True,
            "source": "full UModel object catalog",
        }
    cached = package_cache.ensure_package(filename, row["RelativePath"])
    parsed = cached.get("parsed") or package_cache.get_cached_parsed(row["RelativePath"])
    if parsed is None:
        result = run_umodel(row["RelativePath"], "-pkginfo")
        parsed = parse_pkginfo(str(result.get("output", "")))
        return {
            "package": row["RelativePath"],
            "parsed": parsed,
            "exit_code": result.get("exit_code"),
            "cache_hit": False,
        }
    return {
        "package": row["RelativePath"],
        "parsed": parsed,
        "cache_hit": cached.get("cache_hit", False),
        "object_count": cached.get("object_count"),
    }


@mcp_tool(_log)
def list_package_objects(package: str, limit: int = 200) -> dict[str, Any]:
    row = _packages.resolve_upk(package)
    filename = Path(row["RelativePath"]).name
    catalog = package_cache.get_catalog_package(row["RelativePath"])
    if catalog is not None:
        items = package_cache.list_catalog_objects(
            row["RelativePath"], limit=clamp_limit(limit, maximum=500)
        )
        cache_hit = True
        object_count = catalog["object_count"]
    else:
        meta = package_cache.ensure_package(filename, row["RelativePath"])
        items = package_cache.list_cached_objects(
            row["RelativePath"], limit=clamp_limit(limit, maximum=500)
        )
        cache_hit = meta.get("cache_hit", False)
        object_count = meta.get("object_count")
    return {
        "package": row["RelativePath"],
        "count": len(items),
        "items": items,
        "cache_hit": cache_hit,
        "object_count": object_count,
    }


@mcp_tool(_log)
def search_objects(query: str, limit: int = 50) -> dict[str, Any]:
    items = package_cache.search_objects(query, limit=clamp_limit(limit))
    return {"query": query, "count": len(items), "items": items}


@mcp_tool(_log)
def export_package(
    package: str,
    textures_as_png: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    row = _packages.resolve_upk(package)
    safe_name = row["RelativePath"].replace("\\", "/").removesuffix(".upk").replace("/", "__")
    output_dir = ensure_under(_settings.export_root, _settings.export_root / safe_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    options = ["-export", f"-out={output_dir}"]
    if textures_as_png:
        options.append("-png")
    result = run_umodel(
        row["RelativePath"], *options, timeout=max(30, min(timeout, 600))
    )
    result["package"] = row["RelativePath"]
    result["output_directory"] = str(output_dir)
    if "command" in result:
        cmd = list(result["command"])
        cmd[0] = Path(cmd[0]).name
        result["command"] = cmd
    return result


def register(server: MCPServer, *, include_health: bool = True) -> None:
    if include_health:
        server.add_tool(health, description="Report path readiness for the assets MCP server.")
    server.add_tool(
        list_packages,
        description="Search indexed CookedPCConsole and DLC .upk packages by relative path.",
    )
    server.add_tool(
        get_package_info,
        description="Read UModel package statistics for a unique filename or exact game-root-relative UPK path.",
    )
    server.add_tool(
        list_package_objects,
        description="List export names/classes for a unique filename or exact game-root-relative UPK path.",
    )
    server.add_tool(
        search_objects,
        description="Search cached package objects by name/class across refreshed packages.",
    )
    server.add_tool(
        export_package,
        description="Export one UPK into ignored assets/extracted/<name>/.",
    )


def create_server() -> MCPServer:
    mcp = MCPServer(
        name="dishonored-assets",
        version="2.2.0",
        instructions=(
            "Inspect the Dishonored UE3 package index and invoke UModel for one "
            "manifest-listed .upk at a time. Object lists are cached in SQLite. "
            f"Game root: {_settings.game_root}."
        ),
    )
    register(mcp, include_health=True)
    return mcp


server = create_server()


if __name__ == "__main__":
    _log.info("starting dishonored-assets MCP (stdio)")
    server.run("stdio")
