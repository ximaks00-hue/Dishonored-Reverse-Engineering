"""Provenance-keyed disk cache for headless Ghidra decompilation results."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from mcp_servers.common.address import normalize_function_entry
from mcp_servers.common.config import Settings, get_settings

CACHE_FORMAT_VERSION = 2
DECOMPILE_SCRIPT = Path("research") / "executable" / "scripts" / "DecompileFunction.java"
HEADLESS_OPTIONS = ("-noanalysis", "-readOnly")
POST_SCRIPT = "DecompileFunction.java"
_UNSET = object()


def _cache_dir(settings: Settings | None = None) -> Path:
    path = (settings or get_settings()).decompile_cache_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(address: str) -> Path:
    key = normalize_function_entry(address)
    return _cache_dir() / f"{key}.json"


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def _ghidra_identity(settings: Settings) -> dict[str, Any] | None:
    """Read release/build identity from this Ghidra installation, without launching it."""
    install_root = settings.ghidra_headless.parent.parent
    properties = install_root / "Ghidra" / "application.properties"
    try:
        raw = properties.read_bytes()
    except OSError:
        return None

    values: dict[str, str] = {}
    for line in raw.decode("iso-8859-1").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    version = values.get("application.version")
    revision = values.get("application.revision.ghidra")
    if not version or not revision:
        return None
    components = _decompiler_components(install_root)
    if not components:
        return None
    component_hashes: dict[str, str] = {}
    for component in components:
        digest = _sha256_file(component)
        if digest is None:
            return None
        component_hashes[component.relative_to(install_root).as_posix()] = digest
    return {
        "version": version,
        "revision": revision,
        "binary_revision": values.get("application.revision.ghidra.bin", ""),
        "properties_sha256": hashlib.sha256(raw).hexdigest(),
        "decompiler_components": component_hashes,
    }


def _decompiler_components(install_root: Path) -> list[Path]:
    """Locate the Java and native decompiler components used on this host."""
    system = platform.system().casefold()
    if system == "windows":
        os_name = "win"
        executable = "decompile.exe"
    elif system == "linux":
        os_name = "linux"
        executable = "decompile"
    elif system == "darwin":
        os_name = "mac"
        executable = "decompile"
    else:
        return []

    machine = platform.machine().casefold()
    if machine in {"amd64", "x86_64"}:
        arch = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm_64"
    else:
        return []

    decompiler = install_root / "Ghidra" / "Features" / "Decompiler"
    return [
        decompiler / "lib" / "Decompiler.jar",
        decompiler / "os" / f"{os_name}_{arch}" / executable,
    ]


def _project_revision(settings: Settings) -> str | None:
    """Fingerprint project files by path, size and mtime; hash small project metadata."""
    project_root = settings.ghidra_project / f"{settings.ghidra_project_name}.rep"
    if not project_root.is_dir():
        return None

    files: list[dict[str, Any]] = []
    try:
        project_files = sorted(path for path in project_root.rglob("*") if path.is_file())
        if not project_files:
            return None
        for path in project_files:
            stat = path.stat()
            item: dict[str, Any] = {
                "path": path.relative_to(project_root).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
            # Project property/index files are small and may preserve their size.
            # Hash them so metadata-preserving edits still invalidate the cache.
            if stat.st_size <= 1024 * 1024:
                digest = _sha256_file(path)
                if digest is None:
                    return None
                item["sha256"] = digest
            files.append(item)
    except OSError:
        return None

    revision = {
        "files": files,
        # Optional operator token for project changes on filesystems that preserve
        # timestamps/sizes on large database files.
        "explicit_revision": os.environ.get("DISHONORED_GHIDRA_PROJECT_REVISION", ""),
    }
    encoded = json.dumps(revision, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _index_revision(settings: Settings) -> dict[str, Any] | None:
    try:
        stat = settings.functions_csv.stat()
    except OSError:
        return None
    if not settings.functions_csv.is_file():
        return None
    digest = _sha256_file(settings.functions_csv)
    if digest is None:
        return None
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest}


def cache_identity(address: str, settings: Settings | None = None) -> dict[str, Any] | None:
    """Return cache inputs, or None when provenance cannot be established."""
    cfg = settings or get_settings()
    key = normalize_function_entry(address, cfg)
    ghidra = _ghidra_identity(cfg)
    project_revision = _project_revision(cfg)
    index_revision = _index_revision(cfg)
    script_path = cfg.root / DECOMPILE_SCRIPT
    script_sha256 = _sha256_file(script_path)
    if ghidra is None or project_revision is None or index_revision is None or script_sha256 is None:
        return None

    return {
        "cache_format_version": CACHE_FORMAT_VERSION,
        "address": key,
        "build_id": cfg.build_id,
        "exe_sha256": cfg.executable_sha256,
        "image_base": cfg.image_base,
        "ghidra": ghidra,
        "project_name": cfg.ghidra_project_name,
        "program": cfg.ghidra_program,
        "project_revision": project_revision,
        "function_index": index_revision,
        "headless_options": list(HEADLESS_OPTIONS),
        "post_script": POST_SCRIPT,
        "script_sha256": script_sha256,
        "script_arguments": [key],
    }


def cache_key(address: str, settings: Settings | None = None) -> str | None:
    identity = cache_identity(address, settings)
    if identity is None:
        return None
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load(
    address: str,
    *,
    expected_cache_key: str | None | object = _UNSET,
) -> dict[str, Any] | None:
    settings = get_settings()
    current_key = cache_key(address, settings)
    if current_key is None:
        return None
    if expected_cache_key is not _UNSET and current_key != expected_cache_key:
        return None
    path = _cache_dir(settings) / f"{normalize_function_entry(address, settings)}.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("cache_key") != current_key or cache_key(address, settings) != current_key:
        return None
    if not payload.get("pseudocode"):
        return None
    payload["cache_hit"] = True
    payload["cache_path"] = str(path)
    return payload


def store(
    address: str,
    record: dict[str, Any],
    *,
    expected_cache_key: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    key = cache_key(address, settings)
    payload = {
        "address": record.get("address") or f"0x{normalize_function_entry(address, settings)}",
        "name": record.get("name", ""),
        "signature": record.get("signature", ""),
        "pseudocode": record.get("pseudocode", ""),
        "exe_sha256": settings.executable_sha256,
        "build_id": settings.build_id,
        "cache_key": key,
        "cached_at": time.time(),
    }
    if key is None or expected_cache_key is None or key != expected_cache_key:
        payload["cache_hit"] = False
        payload["cache_stored"] = False
        return payload

    path = _cache_dir(settings) / f"{normalize_function_entry(address, settings)}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    payload["cache_hit"] = False
    payload["cache_stored"] = True
    payload["cache_path"] = str(path)
    return payload
