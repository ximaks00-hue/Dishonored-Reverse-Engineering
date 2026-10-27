"""Typed workspace configuration for Dishonored MCP servers."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser().resolve() if raw else default.resolve()


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable resolved paths and build identity for one MCP process."""

    root: Path
    game_root: Path
    game_exe: Path
    cooked: Path
    packages_index: Path
    export_root: Path
    decompressed_dishonored_game: Path
    research_db: Path
    schema_sql: Path
    callgraph_db: Path
    package_cache_db: Path
    decompile_cache_dir: Path
    ghidra_project: Path
    ghidra_project_name: str
    ghidra_program: str
    functions_csv: Path
    umodel_exe: Path
    ghidra_headless: Path
    build_id: str
    executable_sha256: str
    image_base: int = 0x00400000
    max_memory_read: int = 4096
    max_list_limit: int = 200
    max_trace_queue: int = 1000
    max_batch_reads: int = 32

    def path_report(self) -> dict[str, Any]:
        checks = {
            "repo_root": self.root,
            "game_root": self.game_root,
            "game_exe": self.game_exe,
            "cooked": self.cooked,
            "packages_index": self.packages_index,
            "export_root": self.export_root,
            "decompressed_dishonored_game": self.decompressed_dishonored_game,
            "research_db": self.research_db,
            "schema_sql": self.schema_sql,
            "callgraph_db": self.callgraph_db,
            "package_cache_db": self.package_cache_db,
            "decompile_cache_dir": self.decompile_cache_dir,
            "ghidra_project": self.ghidra_project,
            "functions_csv": self.functions_csv,
            "umodel_exe": self.umodel_exe,
            "ghidra_headless": self.ghidra_headless,
        }
        return {
            "build_id": self.build_id,
            "executable_sha256": self.executable_sha256,
            "image_base": f"0x{self.image_base:08X}",
            "paths": {
                key: {"path": str(path), "exists": path.exists()}
                for key, path in checks.items()
            },
        }

    def require_exists(self, *attrs: str) -> None:
        missing: list[str] = []
        for attr in attrs:
            path = getattr(self, attr)
            if not isinstance(path, Path) or not path.exists():
                missing.append(f"{attr}={path}")
        if missing:
            from mcp_servers.common.errors import ToolError

            raise ToolError(
                "missing_dependency",
                "Required workspace path(s) are missing",
                missing=missing,
            )


_LOCK = threading.Lock()
_SETTINGS: Settings | None = None


def build_settings(root: Path | None = None) -> Settings:
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    game_root = _env_path("DISHONORED_ROOT", repo / "Dishonored RHCP")
    return Settings(
        root=repo,
        game_root=game_root,
        game_exe=_env_path(
            "DISHONORED_EXE",
            game_root / "Binaries" / "Win32" / "Dishonored.exe",
        ),
        cooked=(game_root / "DishonoredGame" / "CookedPCConsole").resolve(),
        packages_index=(repo / "assets" / "manifests" / "packages.csv").resolve(),
        export_root=(repo / "assets" / "extracted").resolve(),
        decompressed_dishonored_game=(
            repo / "assets" / "extracted" / "dishonored-blink" / "DishonoredGame.upk"
        ).resolve(),
        research_db=_env_path(
            "DISHONORED_RESEARCH_DB",
            repo / "knowledge" / "database" / "dishonored-research.sqlite",
        ),
        schema_sql=(repo / "knowledge" / "database" / "schema.sql").resolve(),
        callgraph_db=_env_path(
            "DISHONORED_CALLGRAPH_DB",
            repo / "knowledge" / "database" / "callgraph.sqlite",
        ),
        package_cache_db=_env_path(
            "DISHONORED_PACKAGE_CACHE_DB",
            repo / "knowledge" / "database" / "package-cache.sqlite",
        ),
        decompile_cache_dir=_env_path(
            "DISHONORED_DECOMPILE_CACHE",
            repo / "knowledge" / "cache" / "decompiles",
        ),
        ghidra_project=_env_path(
            "DISHONORED_GHIDRA_PROJECT",
            repo / "research" / "executable" / "ghidra-project",
        ),
        ghidra_project_name=_env_str(
            "DISHONORED_GHIDRA_PROJECT_NAME", "Dishonored-RHCP-10256413"
        ),
        ghidra_program=_env_str("DISHONORED_GHIDRA_PROGRAM", "Dishonored.exe"),
        functions_csv=(
            repo / "research" / "executable" / "functions.csv"
        ).resolve(),
        umodel_exe=_env_path(
            "UMODEL_EXE",
            repo / "third_party" / "ueviewer-gildor" / "umodel.exe",
        ),
        ghidra_headless=_env_path(
            "GHIDRA_HEADLESS",
            Path(r"C:\Users\Max\Tools\ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"),
        ),
        build_id=_env_str("DISHONORED_BUILD_ID", "10256413"),
        executable_sha256=_env_str(
            "DISHONORED_EXE_SHA256",
            "66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E",
        ),
    )


def get_settings(*, refresh: bool = False) -> Settings:
    """Return process-wide settings; refresh=True rebuilds from current env."""
    global _SETTINGS
    with _LOCK:
        if _SETTINGS is None or refresh:
            _SETTINGS = build_settings()
        return _SETTINGS


# Back-compat aliases used by older imports.
@lru_cache(maxsize=1)
def _legacy() -> Settings:
    return get_settings()
