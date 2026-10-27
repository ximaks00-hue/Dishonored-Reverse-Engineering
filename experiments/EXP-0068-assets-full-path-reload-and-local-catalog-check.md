---
id: EXP-0068
title: Verify full-path package handling after Assets MCP reload and locally
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the connected Assets MCP accept nested DLC package paths after reload, and does the local manifest/catalog independently resolve a selected DLC package without basename ambiguity?"
---

# EXP-0068 — Verify full-path package handling after Assets MCP reload and locally

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: test the connected Assets MCP read-only endpoint for its loaded source version and nested-DLC full-path lookup; independently read the local manifest and generated UModel object catalog and run a one-package UModel metadata query.
- Exclusions: no game launch, package export, MCP host restart, or game-data modification; `_excluded_coop_project/` was not accessed.
- Tools: `mcp__dishonored_assets` health/list tools; UModel x86; Python CSV/SQLite read-only inspection; PowerShell SHA-256.

## Procedure

1. Re-read research status, Blink activation graph, and exact-build record; verify the EXE SHA-256.
2. Queried connected Assets MCP `health`, then called `list_packages` with the nested DLC06 package path.
3. Used the repository's `assets/manifests/packages.csv` to check total rows and duplicate basenames.
4. Queried the generated `knowledge/database/umodel-package-objects.sqlite` catalog for the DLC06 package row and object count; compared them to the package metadata census.
5. Ran UModel `-pkginfo` read-only against the same package and compared the target file's current SHA-256 to the catalog.

## Observations

- Connected Assets MCP `health` reports ready with build `10256413` and the expected executable SHA-256, but reports server version `2.1.0`. Workspace source `mcp_servers/assets/server.py` declares version `2.2.0`.
- Connected `list_packages` for `DLC06/DLC06_DishonoredGameFull_P.upk` returned an execution error without package results.
- The local full-path package manifest contains 904 package rows and nine duplicate basenames. `GlobalPersistentCookerData.upk` has four paths: CookedPCConsole and DLC05, DLC06, DLC07.
- The local catalog contains exact row `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DishonoredGameFull_P.upk`, with file size 10,607,295 bytes, SHA-256 `B89C768E7331726DD11BDFDD06E2D6F33209FA47667E7AA84D380390D96B2FF2`, 15,142 export rows, and `list_status=count_match`; the package census also reports 15,142 exports.
- Current on-disk package hash matches that catalog SHA-256. Direct UModel `-pkginfo` returned a package summary and object class counts for the DLC06 package.

## Interpretation / claims

- **Observed:** the connected Assets MCP process has not loaded the current 2.2.0 source and does not yet accept the tested full nested-DLC path.
- **Confirmed locally:** the 904-row manifest and generated catalog preserve the tested DLC package's full path; the package has 15,142 listed export rows, matching its package-info export count and current file hash.
- **Unknown:** behavior of the connected endpoint after a host reload. The available tools expose no Assets MCP restart control, so the reload itself could not be performed in this session.

## Reproduction and limitations

- Call connected `mcp__dishonored_assets__health` and `list_packages` with the full relative path `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DishonoredGameFull_P.upk` after a host-side reload; the desired endpoint check is version `2.2.0` plus successful full-path resolution.
- Local read-only check:

  ```powershell
  python -c "import csv,sqlite3; p='DishonoredGame/DLC/PCConsole/DLC06/DLC06_DishonoredGameFull_P.upk'; rows=list(csv.DictReader(open('research/packages/installed-upk-pkginfo-census.csv',encoding='utf-8-sig'))); c=sqlite3.connect('knowledge/database/umodel-package-objects.sqlite'); print(c.execute('select relative_path,sha256,exports,listed_objects,list_status from packages where relative_path=?',(p,)).fetchone()); print(next((r['exports'] for r in rows if r['relative_path']==p),None))"
  ```
- This checks path identity and count agreement for one DLC package only. It does not establish parsing completeness or connected-server state after reload.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent path-support work: [EXP-0054](EXP-0054-assets-mcp-full-package-paths.md)
- Full package catalog: [EXP-0053](EXP-0053-all-install-upk-object-catalog.md)
- Metadata census: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- Package index: [packages.csv](../assets/manifests/packages.csv)
