---
id: EXP-0122
title: Assets MCP nested DLC package path reprobe
experiment_status: done
claim_status: observed
build: "10256413"
question: Does the connected Assets MCP's current package-info endpoint resolve a manifest-listed DLC package by full path or unique basename?
---

# EXP-0122 — Assets MCP nested DLC package path reprobe

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; Assets MCP health reports the recorded EXE SHA-256.
- Scope: read-only `health` and `get_package_info` requests for the manifest-listed `DLC06_DaudBase_Script.upk`.
- Exclusions: no package export or mutation; this probes the connected tool's path behavior, not UModel's general ability to parse DLC packages.
- Inputs: current 904-row [package manifest](../assets/manifests/packages.csv), refreshed full-tree [file inventory](../research/builds/BUILD-STEAM-10256413/files.csv), and connected `dishonored-assets` tools.

## Procedure

1. Read `AGENTS.md`, research status, Blink graph, build record, and MCP matrix; confirm build ID and EXE SHA-256.
2. Call Assets MCP `health`.
3. Call `get_package_info` with `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DaudBase_Script.upk`, then with the unique basename `DLC06_DaudBase_Script.upk`.
4. Compare the package path, size, and hash against the current full install inventory and package manifest.

## Observations

- `health` reports `ok=true`, `ready=true`, build `10256413`, the expected EXE hash, and Assets MCP version `2.1.0`.
- The full manifest path request returns `invalid_package` with the message that directory components are not accepted.
- The basename request passes manifest lookup and resolves to `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DaudBase_Script.upk`, then returns `package_unavailable`, identifying `CookedPCConsole` as the allowed root.
- The file exists in the local install and current manifest at 18,674,760 bytes with SHA-256 `62E46C0F78E5C7D2FFC4EBAB6006A557D9B444AD964A7818AA8DBB6AD602D306`.
- Both responses come from the same read-only package-info endpoint; neither request exported package contents.

## Interpretation / claims

- **Observed:** the connected 2.1.0 endpoint rejects full relative paths and fails on a valid DLC basename after resolving it outside its CookedPCConsole-only guard.
- **Confirmed:** the tested DLC file is present in the current install and exactly matches the package manifest by size and SHA-256.
- **Unknown:** whether a server reload to the documented 2.2.0 implementation will resolve nested DLC paths; the available integration exposes no reload control in this probe.
- **Limit:** this is one valid DLC package and one endpoint. It establishes the current failure mode for this case, not every endpoint or package family.

## Reproduction

Call `mcp__dishonored_assets__health({})`, then:

```text
get_package_info(package="DishonoredGame/DLC/PCConsole/DLC06/DLC06_DaudBase_Script.upk")
get_package_info(package="DLC06_DaudBase_Script.upk")
```

Expected on the observed server: `invalid_package`, then `package_unavailable` with resolved DLC path and `CookedPCConsole` as the allowed root.

## Links

- Build record: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package index: [packages.csv](../assets/manifests/packages.csv)
- MCP matrix: [mcp.md](../docs/tooling/mcp.md)
- Prior package-index work: [EXP-0054](EXP-0054-assets-mcp-full-package-paths.md)
- Project completion contract: [roadmap](../docs/roadmap.md)
