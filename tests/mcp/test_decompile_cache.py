from __future__ import annotations

from pathlib import Path

import pytest

from mcp_servers.common import decompile_cache
from mcp_servers.common.config import get_settings


def test_store_load_and_sha_invalidation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cache_dir = tmp_path / "decompiles"
    monkeypatch.setenv("DISHONORED_DECOMPILE_CACHE", str(cache_dir))
    monkeypatch.setenv(
        "DISHONORED_EXE_SHA256",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    get_settings(refresh=True)

    stored = decompile_cache.store(
        "0x00BFC990",
        {
            "address": "0x00BFC990",
            "name": "FUN_00BFC990",
            "signature": "void FUN_00BFC990(void)",
            "pseudocode": "void FUN_00BFC990(void)\n{\n  return;\n}\n",
        },
    )
    assert stored["cache_hit"] is False
    assert Path(stored["cache_path"]).is_file()

    loaded = decompile_cache.load("0x00BFC990")
    assert loaded is not None
    assert loaded["cache_hit"] is True
    assert "FUN_00BFC990" in loaded["pseudocode"]

    monkeypatch.setenv(
        "DISHONORED_EXE_SHA256",
        "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    )
    get_settings(refresh=True)
    assert decompile_cache.load("0x00BFC990") is None
