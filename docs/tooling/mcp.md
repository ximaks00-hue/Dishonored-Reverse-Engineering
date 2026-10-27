# MCP and path configuration

Canonical typed settings live in `mcp_servers/common/config.py` (back-compat exports in `mcp_servers/_paths.py`). Environment variables always override defaults. Server architecture: [`mcp_servers/README.md`](../../mcp_servers/README.md).

## Which tool to call first

Prefer the unified gateway (`dishonored_gateway` → `mcp_servers/gateway/server.py`):

| Agent question | Call first | Then |
| --- | --- | --- |
| What do we know about Blink / activation? | `brief("blink")` | Open linked EXP markdown |
| Who calls / is called by VA `0x…`? | `callers` / `callees` / `path` | Live `ghidra-re-mcp` only if the offline graph is missing or you need renames |
| Full context for one function | `function_dossier(address)` | `decompile_function` on cache miss |
| One experiment’s frontmatter | `experiment(id)` | `include_body=true` only when needed |
| Package object by name | `search_objects` after a package was listed once | `list_package_objects` warms the cache |
| Live memory | `read_game_memory_many` / Frida `read_many` | Never launch the game just to test tooling |

Live **ghidra-re-mcp** remains for writing the Ghidra DB (comments, renames, types). Do not use headless decompile as a second source of truth for names.

## Which server for which job

| Job | Use | Do not use |
| --- | --- | --- |
| Fast agent packs + indexes (recommended) | `dishonored_gateway` | Five separate stdio hosts for routine questions |
| Deep Ghidra decompile / xrefs / rename on the live DB | `ghidra-re-mcp` / `user-ghidra-re-mcp` | Gateway callgraph for *writes* |
| Offline function search / cached headless decompile | Gateway or `dishonored_static` | Second address truth vs live Ghidra |
| Package summary / name search on compressed UPK | `ue_explorer` | Expect object-table decompile on compressed input |
| Property/default dumps | Local UELib on `assets/extracted/dishonored-blink/` | Compressed game UPK via MCP decompile |
| UModel list/export | Gateway / `dishonored_assets` | |
| Read-only running process | Gateway / `dishonored_runtime` / `dishonored_frida` | Launching the game solely to “test” MCP |
| Search recorded EXP/edges | Gateway `search_research` (FTS5) / `brief` | Treat SQLite as authoritative over EXP text |

Broken hosts (missing binaries) are **disabled** in Cursor/Codex configs: `re-lab-mcp`, `ghidra-gui-mcp`. Re-enable only after restoring those paths.

Standalone entrypoints (`assets/server.py`, …) remain thin wrappers for compatibility; the recommended host is **one** `dishonored_gateway` process so indexes stay warm.

## Offline call graph

Build once (read-only Ghidra), then query without JVM:

```text
analyzeHeadless <ghidra-project> Dishonored-RHCP-10256413 -process Dishonored.exe -noanalysis -readOnly ^
  -scriptPath research/executable/scripts -postScript ExportCallGraph.java knowledge/database/callgraph.csv

python tools/import_callgraph_csv.py knowledge/database/callgraph.csv
```

Missing index → tools return `{ok:false, error.code=index_missing}` with the build command hint. Never invent edges from decompiler text.

## Registration

| Host | Config |
| --- | --- |
| Cursor (workspace) | `.cursor/mcp.json` (workspace-local and gitignored) — prefer `dishonored_gateway` |
| Cursor (user) | `%USERPROFILE%\.cursor\mcp.json` — keep `ghidra-re-mcp`; Dishonored servers come from the workspace file |
| Codex | `%USERPROFILE%\.codex\config.toml` |

After edits: reload MCP / restart the host. Verify with `python tools/mcp_smoke_test.py`, `python -m pytest tests/mcp -q`, and optionally `python tools/mcp_bench.py`.

## Workspace defaults

| Variable | Default (under repo root) |
| --- | --- |
| `DISHONORED_ROOT` | `Dishonored RHCP/` |
| `DISHONORED_EXE` | `Dishonored RHCP/Binaries/Win32/Dishonored.exe` |
| `DISHONORED_RESEARCH_DB` | `knowledge/database/dishonored-research.sqlite` |
| `DISHONORED_CALLGRAPH_DB` | `knowledge/database/callgraph.sqlite` |
| `DISHONORED_PACKAGE_CACHE_DB` | `knowledge/database/package-cache.sqlite` |
| `DISHONORED_DECOMPILE_CACHE` | `knowledge/cache/decompiles/` |
| `DISHONORED_GHIDRA_PROJECT` | `research/executable/ghidra-project` |
| `DISHONORED_BUILD_ID` | `10256413` |
| `UMODEL_EXE` / `UMODEL_PATH` | `third_party/ueviewer-gildor/umodel.exe` |
| `GHIDRA_HEADLESS` | local Ghidra `analyzeHeadless.bat` |

Copy [`.env.example`](../../.env.example) into host env blocks when needed.

## Servers (project-owned)

| Server | Entry | Role |
| --- | --- | --- |
| **`dishonored_gateway`** | `mcp_servers/gateway/server.py` | **Recommended** — all indexes + packs + live read |
| `dishonored_assets` | `mcp_servers/assets/server.py` | UModel package list/info/export and full-install object catalog (compat) |
| `dishonored_knowledge` | `mcp_servers/knowledge/server.py` | SQLite research store (compat) |
| `dishonored_runtime` | `mcp_servers/runtime/server.py` | Read-only process inspection (compat) |
| `dishonored_frida` | `mcp_servers/frida_runtime/server.py` | Read-only Frida attach/trace (compat) |
| `dishonored_static` | `mcp_servers/static/server.py` | Function index + cached headless decompile (compat) |
| `ue_explorer` | `tools/ueexplorer-mcp/` | UE3 package metadata / UnrealScript |

Response envelope (all tools): success `{ok, data, meta}`, error `{ok:false, error:{code,message}, meta}`.

Compatibility: `research/executable/mcp/server.py` only launches the canonical static server.

## Package index and decompile boundary

- `assets/manifests/packages.csv` indexes all 904 installed UPKs by full game-root-relative path, byte size, and SHA-256. Pass a full path when a basename repeats; bare filenames work only when unique. The connected assets server must reload to pick up the 2.2.0 path-aware implementation (EXP-0054).
- The local export-name catalog is `knowledge/database/umodel-package-objects.sqlite` (gitignored); it has count-matched UModel listings for all 904 packages (EXP-0053).
- Compressed `DishonoredGame.upk` under the game root: summary and object list are available; deeper bytecode/property analysis still uses an appropriate parser and, where required, a decompressed analysis copy.
- Decompressed analysis copy: `assets/extracted/dishonored-blink/DishonoredGame.upk` (gitignored).
