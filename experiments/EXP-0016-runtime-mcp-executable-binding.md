---
id: EXP-0016
title: Runtime MCP executable binding
experiment_status: done
claim_status: observed
build: "10256413"
question: "Why did runtime/Frida MCP miss the research process, and are corrected paths sufficient without live attach?"
---
# EXP-0016 — Runtime MCP executable binding

- Status: local configuration and knowledge schema repaired; active MCP reload and live-process access not yet verified.
- Date: 2026-10-26.
- Purpose: identify why the read-only runtime and Frida MCP lookups did not find the research process.
- Scope: inspect `%USERPROFILE%\\.codex\\config.toml`, verify Dishonored MCP executable/root/interpreter paths and current process presence, repair local configuration and the missing knowledge schema, and validate the result. This does not claim that the already-running Codex MCP instances reloaded the changed configuration.

## Findings

- Before the correction, both `dishonored_runtime` and `dishonored_frida` pointed at `E:\SteamLibrary\steamapps\common\Dishonored RHCP\Binaries\Win32\Dishonored.exe`. `Test-Path` confirmed that target does not exist in this environment.
- The exact workspace executable exists at `E:\Dishonored Reverse Engineering\Dishonored RHCP\Binaries\Win32\Dishonored.exe`; its SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the build record.
- Updated both stale `DISHONORED_EXE` values to the existing workspace executable.
- The `dishonored_assets` server also pointed `DISHONORED_ROOT` at the nonexistent SteamLibrary directory. Updated it to the workspace game root. The configured UModel executable exists, and running its read-only `-pkginfo` command against the workspace package root succeeds with version `801/30`, engine `9411`, game `800033`, 30,049 exports, and 652 imports. The live MCP `get_package_info` call still returned a generic error after the file edit; the existing server instance's environment/reload state is unknown, so that call is not evidence of successful post-fix operation.
- `dishonored_knowledge` used a Python executable under the absent `E:\Dishonored REVERS` checkout. Updated the command to the existing workspace `.venv`. Its server code required `knowledge/database/schema.sql`, which did not exist; added a schema for the tables and fields used by its current queries/inserts, initialized the local SQLite store, and confirmed the six expected tables (`game_build`, `functions`, `structures`, `hypotheses`, `evidence`, `experiments`). The local database is ignored by Git.
- Parsed the resulting TOML with Python `tomllib` and independently verified that all four affected command/root/executable paths resolve to existing files.
- No `Dishonored` process was running at the time of inspection. Therefore no runtime or Frida memory read/trace could be performed in this experiment. Fresh MCP server launches/reloads are required for the processes to inherit corrected settings; this record does not claim that the currently running server instances have reloaded them.

## Follow-up tool verification (2026-10-26)

- The current `dishonored_static.decompile_function` MCP successfully decompiled `0x009EE630` from the persisted workspace Ghidra project in read-only mode. Its body matches the existing Ghidra MCP result: it parses one DWORD and invokes receiver slot `+0x560`. This confirms that the static MCP is live and reads the intended workspace analysis project.
- A fresh local process query still found no `Dishonored` process. `dishonored_runtime.get_game_process` returned a generic tool error, so its live status/result is unresolved; no process read or Frida attachment was attempted. Do not interpret the generic error as evidence that the executable path is still invalid, because the configured EXE exists and the process is absent.
- `research/executable/README.md` previously named the old `E:\Dishonored REVERS` Python environment. It now records the configured workspace `.venv`, whose `mcp` import resolves locally.

## Evidence and limits

The path-existence checks, TOML parse, process query, executable SHA-256, SQLite schema initialization, and direct UModel package-info command are repeatable. The generic MCP errors alone were not enough to diagnose the root causes; stale paths, the absent knowledge schema, and the missing process were established independently from local state and server source. Even after server reload, runtime calls require this exact workspace copy to be running. Do not launch or modify the game as part of this experiment.

No game files were changed, and `_excluded_coop_project/` was not accessed.
