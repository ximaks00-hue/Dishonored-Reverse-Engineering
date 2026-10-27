# Dishonored research MCP servers (v2 gateway)

The assets-server source currently reports version `2.2.0` in `mcp_servers/assets/server.py`. This source version is not proof that a connected MCP host has reloaded: EXP-0122 observed a still-running `2.1.0` host rejecting nested DLC paths. Check `health()` on the actual host before assuming DLC support.

Professional stdio MCP stack for evidence-led Dishonored research on build `10256413`.

## Architecture

```text
mcp_servers/
  gateway/          recommended single host (indexes + packs + live read)
  common/           config, errors, address, CSV indexes, DB/FTS, caches, callgraph
  assets/           UModel package list / info / export (+ object SQLite cache)
  knowledge/        SQLite research mirror + FTS5 + brief/dossier/experiment
  static/           offline Ghidra function index + cached headless decompile
  runtime/          read-only Win32 process inspection (+ batch read)
  frida_runtime/    read-only Frida attach / read_many / temporary traces
  _paths.py         back-compat re-exports of Settings fields
```

Design rules:

- **stdout is MCP JSON-RPC** — all logs go to stderr via `common.logging_setup`.
- **Workspace defaults** live in `common.config.Settings` (env overrides).
- **Unified envelope** — success `{ok, data, meta}`, error `{ok:false, error:{code,message}}`.
- **Hard failures** raise `ToolError(code, message, **details)`.
- **Soft absences** (game not running) return structured `status=not_running` / `process_not_running`.
- **Path traversal guards** on export directories (`ensure_under`).
- **CSV indexes** are mtime-cached. Function lookup is O(1) by entry and O(log n) by body range (~72k functions).
- **Call graph** is offline SQLite (`callers` / `callees` / `xrefs_to` / `path`); missing → `index_missing`.
- **Decompile cache** under `knowledge/cache/decompiles/` keyed by VA + EXE SHA-256.
- **Package object cache** in `package-cache.sqlite`; `search_objects` is index-only after warm-up.
- **Agent packs** — call `brief` / `function_dossier` / `experiment` first; EXP markdown remains authoritative.
- **Read-only runtime/Frida** — no write/patch/suspend/terminate APIs.

## Recommended host

Register **one** gateway process so indexes stay in memory:

```json
"dishonored_gateway": {
  "command": ".../.venv/Scripts/python.exe",
  "args": [".../mcp_servers/gateway/server.py"]
}
```

Standalone servers remain for compatibility with older host configs.

## Servers

| MCP name | Module | Notes |
| --- | --- | --- |
| `dishonored-gateway` | `gateway/server.py` | All tools; one `health` |
| `dishonored-assets` | `assets/server.py` | Requires `umodel.exe` + packages.csv |
| `dishonored-research` | `knowledge/server.py` | Auto-applies schema + FTS5 |
| `dishonored-static-analysis` | `static/server.py` | Headless decompile serialized + cached |
| `dishonored-runtime` | `runtime/server.py` | Windows-only memory read / batch |
| `dishonored-frida-runtime` | `frida_runtime/server.py` | Traces require Ghidra-indexed VAs |

## Host registration

- Cursor workspace: `.cursor/mcp.json` (workspace-local, gitignored)
- Codex: `~/.codex/config.toml`
- Matrix: [`docs/tooling/mcp.md`](../docs/tooling/mcp.md)

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest tests/mcp -q
.\.venv\Scripts\python.exe tools\mcp_smoke_test.py
.\.venv\Scripts\python.exe tools\mcp_bench.py
```

Index tools on a warm gateway should land under ~50 ms p50; headless Ghidra only on decompile cache miss.

## Call-graph export

```powershell
# After ExportCallGraph.java via analyzeHeadless -readOnly:
.\.venv\Scripts\python.exe tools\import_callgraph_csv.py knowledge\database\callgraph.csv
```

## Dependencies

See [`requirements-mcp.txt`](../requirements-mcp.txt). Use the repo `.venv`.
