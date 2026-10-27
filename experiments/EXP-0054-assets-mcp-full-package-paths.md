---
id: EXP-0054
title: Extend Assets MCP package resolution to all installed UPKs
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can the package index and Assets MCP code resolve all installed CookedPCConsole and nested DLC UPKs without conflating duplicate filenames?"
---

# EXP-0054 — Extend Assets MCP package resolution to all installed UPKs

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: expand the asset package manifest to all 904 installed UPKs; support exact game-root-relative paths, reject ambiguous basenames, dispatch UModel in a package's containing directory, and query the generated full-install export catalog.
- Exclusions: no export or modification of game data, no game launch or runtime attach; `_excluded_coop_project/` was not accessed.
- Tools: workspace Python sources under `mcp_servers/assets/` and `mcp_servers/common/`; UModel census/export catalog generated in EXP-0052/0053.

## Procedure

1. Confirmed the installed package census contains 904 relative paths and that duplicate basenames occur, including four `GlobalPersistentCookerData.upk` files.
2. Updated `assets/manifests/packages.csv` to contain all 904 UPKs, retaining each full relative path, byte length, and SHA-256.
3. Updated `PackageIndex` to resolve exact relative paths or unique basenames, and to return `ambiguous_package` with candidate paths for repeated basenames. Added cache refresh on CSV replacement.
4. Updated the UModel subprocess wrapper to validate the target stays under the configured game root and to set UModel's `-path` to the package's parent directory.
5. Changed the object cache key to use full relative paths. Updated the Assets MCP package-info/list/search/export calls and the generated catalog queries to preserve package path identity.
6. In a fresh workspace Python process, loaded the Assets MCP tool functions with a stub `MCPServer` constructor and called them against the local package index/catalog. Separately called UModel on the nested DLC06 package through the updated subprocess wrapper.
7. Re-ran the UModel census with `--package-index-output assets/manifests/packages.csv` and validated the experiment frontmatter.

## Observations

- The package manifest contains 904 paths: 470 CookedPCConsole and 434 DLC. The manifest rows preserve build-manifest sizes and hashes.
- Fresh local package resolution returns the exact DLC06 `DLC06_DishonoredGameFull_P.upk` path and shows four candidate paths when passed the duplicate basename `GlobalPersistentCookerData.upk`.
- Fresh local MCP function calls return UModel metadata and object rows from the full SQLite catalog for a nested DLC path. Search for `DisItemContext_UsePower` returns its two object labels from `DishonoredGame.upk`.
- The revised UModel wrapper ran `-pkginfo` against the nested DLC06 package, with exit code 0 and the expected package summary.
- The connected Assets MCP tool instance continued to return the prior `invalid_package` response for directory-qualified paths, indicating that it had not loaded the edited server/index source during this session. No server restart control is exposed through the available tools.
- `python tools/validate_experiments.py` checked 53 experiments with zero errors and warnings.

## Interpretation / claims

- **Confirmed in the current workspace source and local process:** the full manifest, relative-path package resolver, nested UModel wrapper, and generated object-catalog queries identify packages by complete path; ambiguous basenames are reported with candidates.
- **Observed:** the connected MCP process still runs the previous package-argument behavior and requires a server reload before the connected tool surface uses these changes.
- **Unknown:** behavior after that host-side reload has not been observed through the connected MCP endpoint.

## Reproduction and limitations

- Regenerate the package census and full path index from the repository root:

  ```powershell
  python tools/umodel_pkginfo_census.py `
    --umodel "third_party/ueviewer-gildor/umodel.exe" `
    --game-root "Dishonored RHCP" `
    --manifest "research/builds/BUILD-STEAM-10256413/files.csv" `
    --output "research/packages/installed-upk-pkginfo-census.csv" `
    --package-index-output "assets/manifests/packages.csv"
  ```
- Run an Assets MCP reload, then query `list_packages`, `get_package_info`, and `list_package_objects` with `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DishonoredGameFull_P.upk`. Confirm that the health version is 2.2.0. The current connected instance had not reloaded.
- Full export listing metadata is not property, dependency, script-body, native, or runtime evidence. Those remain separate work.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Metadata census: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- Full object catalog: [EXP-0053](EXP-0053-all-install-upk-object-catalog.md)
- Package index: [packages.csv](../assets/manifests/packages.csv)
- Package archaeology: [README](../research/packages/README.md)
- Assets MCP server: [server.py](../mcp_servers/assets/server.py)
- Package resolver: [csv_index.py](../mcp_servers/common/csv_index.py)
- UModel wrapper: [umodel.py](../mcp_servers/common/umodel.py)
