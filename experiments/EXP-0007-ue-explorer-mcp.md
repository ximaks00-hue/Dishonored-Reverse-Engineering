---
id: EXP-0007
title: UE Explorer MCP package access
experiment_status: done
claim_status: observed
build: "10256413"
question: "Can UE Explorer MCP inspect package summary/objects on the compressed DishonoredGame.upk?"
---
# EXP-0007 — UE Explorer MCP package access

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`
- Tools: UE Explorer MCP 1.0.0, Eliot.UELib 1.13.3, UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.
- Question: Can Codex use a local MCP server to inspect the package, search objects, and decompile an object?

## Procedure

1. Parse the local Codex `config.toml` as TOML and verify the `ue_explorer` server command, game root, and UModel path.
2. Build `tools/ueexplorer-mcp` in Release mode.
3. Start the MCP executable and exchange JSON-RPC `initialize`, `tools/list`, and `tools/call` messages over stdio.
4. Call `inspect_package`, search for `PowerBlink`, and request decompilation of `PowerBlink`.

## Observations

- The Release build completed with zero warnings and zero errors.
- The MCP handshake returned server `ue-explorer` version `1.0.0` and tools `inspect_package`, `search_objects`, and `decompile_object`.
- `inspect_package` reported version `801/30`, engine `9411`, cooker `133`, 24,432 names, 30,049 exports, 652 imports, 16 compressed chunks, and compression flags `2`.
- `search_objects` returned three `PowerBlink` export entries through UModel.
- `decompile_object` returned an explicit compressed-package limitation. It did not report an empty decompilation as a successful result.
- In the current desktop conversation, all three `ue_explorer` tools are available and callable. A fresh `inspect_package` call on the workspace copy returned the same summary as above: version `801/30`, engine `9411`, cooker `133`, 24,432 names, 30,049 exports, 652 imports, 16 compressed chunks, compression flags `2`.
- A fresh `search_objects` query for `PowerBlink` returned three exports, all displayed by UModel with class `DishonoredActivePowerComponent_Blink`, at package-list positions/offsets `18320 / 0x4E097C`, `28549 / 0x105C82B`, and `29598 / 0x107FE07`.
- Searching `DishonoredActivePowerComponent_Blink` returned the class at `6411 / 0x3778EB`, `Default__DishonoredActivePowerComponent_Blink` at `6412 / 0x37796F`, and the same three `PowerBlink` entries.
- Searching `m_fBlinkDistanceMax` returned `6410 / 0x3778C3`, displayed as `FloatProperty m_fBlinkDistanceMax`.
- Calling `decompile_object` for `PowerBlink` again returned the explicit error that compressed object tables cannot be loaded by UELib. Thus the search listing exposes useful names/class labels and package-list offsets, but not script body or property values.
- The workspace copy's package index reports `DishonoredGame.upk` length `5,928,252` and SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`; this agrees with the existing package archaeology record.
- `dishonored_assets.get_package_info` returned only the generic text `Error executing tool get_package_info` for this package. The exact underlying exception was not exposed. Its `list_packages` operation succeeds for the same package. The active `C:\Users\Max\.codex\config.toml` points `dishonored_assets` at `E:\Dishonored REVERS\mcp_servers\assets\server.py`, root `E:\SteamLibrary\steamapps\common\Dishonored RHCP`, and UModel `E:\Dishonored REVERS\third_party\ueviewer-gildor\umodel.exe`; in contrast, `ue_explorer` uses this workspace's `Dishonored RHCP` tree. This is a confirmed configuration difference, but is not proven to be the cause of the generic error.
- Inspection of the same package through `ue_explorer` confirms the API reports one compressed chunk for `Core.upk` (flags `2`) and sixteen for `DishonoredGame.upk` (flags `2`).
- UELib writes package diagnostics to `stdout`; the MCP host redirects `Console.Out` so protocol frames remain valid JSON-RPC.
- Initial `codex exec` called the server but blocked on approval because the tools lacked read-only annotations and this environment uses approval policy `never`.
- The three tools now declare `ReadOnly = true`. A subsequent `codex exec` called `inspect_package` successfully and returned the exact package counts above.
- The `ue_explorer` tools are still absent from the tool inventory of the already-open desktop conversation; the Codex CLI invocation confirms that configuration and server calls work.

## Interpretation

- **Observed:** the local server implements MCP stdio, is registered by Codex, and a non-interactive Codex call successfully reads this package summary; object search succeeds through UModel.
- **Unknown:** whether an already-open desktop conversation refreshes its tool inventory after the server configuration changes. The complete Codex TOML parses successfully.
- **Limitation:** UELib 1.13.3 stops before compressed object tables. Decompilation remains unavailable for this cooked package through the current API path.
- **Observed:** the already-open desktop conversation now exposes `inspect_package`, `search_objects`, and `decompile_object`; the earlier absence in the prior experiment is no longer current.
- **Unknown:** why `dishonored_assets.get_package_info` returns a generic execution error while its index operation works. Available logs/configuration establish path differences but not the thrown exception. Do not infer a server restart is needed or repeat one without new evidence.
- **Limitation:** UModel's display of a class alongside a property name, and the nearby default-object listing, do not by themselves establish UE outer ownership, default property values, or bytecode. Listed offsets are package-list offsets, not executable RVAs.

## Reproduction

From the repository root, build with `dotnet build tools/ueexplorer-mcp/ueexplorer-mcp.csproj --configuration Release`. Run the configured executable with `DISHONORED_GAME_ROOT` and `UMODEL_PATH` set, then send the MCP calls listed above. Package access is read-only.

## Links

- Package and parser triage: [EXP-0004](EXP-0004-umodel-blink-triage.md), [EXP-0006](EXP-0006-core-package-metadata.md)
- Server implementation: [`tools/ueexplorer-mcp`](../tools/ueexplorer-mcp/README.md)
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)

