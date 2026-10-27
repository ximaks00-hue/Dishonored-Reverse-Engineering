"""Back-compat path exports. Prefer mcp_servers.common.config.get_settings()."""

from __future__ import annotations

from mcp_servers.common.config import get_settings

_settings = get_settings()

ROOT = _settings.root
GAME_ROOT = _settings.game_root
GAME_EXE = _settings.game_exe
COOKED = _settings.cooked
PACKAGES_INDEX = _settings.packages_index
EXPORT_ROOT = _settings.export_root
DECOMPRESSED_DISHONORED_GAME = _settings.decompressed_dishonored_game
RESEARCH_DB = _settings.research_db
GHIDRA_PROJECT = _settings.ghidra_project
FUNCTIONS_CSV = _settings.functions_csv
UMODEL_EXE = _settings.umodel_exe
GHIDRA_HEADLESS = _settings.ghidra_headless
BUILD_ID = _settings.build_id
EXECUTABLE_SHA256 = _settings.executable_sha256


def path_health():
    return get_settings().path_report()
