---
id: EXP-0083
title: Exact-build single Texture2D disk export and Assets MCP object-list comparison
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can pinned UModel write one real asset file from a hash-identified package, and does the connected Assets MCP object catalog expose the same object?"
---

# EXP-0083 — Exact-build single Texture2D disk export and Assets MCP object-list comparison

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Source package: `DishonoredGame/CookedPCConsole/UI_Map_Boyle_SF.upk`, 239,045 bytes, SHA-256 `4F81D90DB9D102896E5E6A84418CF9F6F3B0BE8A04898B2A90F297E247989BD3`.
- Scope: compare direct UModel `-pkginfo`/`-list` with the connected Assets MCP package-info/object-list/search results, then perform one actual `-export` of the listed `Texture2D LevelMap_Ext_Boyle` into ignored extraction storage.
- Exclusions: no broad package export, no visual/gameplay correctness claim, no game launch, and no modification of source packages. `_excluded_coop_project/` was not accessed.
- Tool: pinned UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; connected `dishonored_assets` MCP version 2.1.0.
- Output: [`LevelMap_Ext_Boyle.tga`](../assets/extracted/umodel-real-export-sample/UI_Map_Boyle_SF/Texture2D/LevelMap_Ext_Boyle.tga), SHA-256 `1442E2AF02CC624A635C77F8F887693BD287D0D534A35B3AAF6195EA72F80D13`, 1,192,609 bytes.

## Procedure

1. Re-read status, Blink activation graph, and build record; verify the executable and UModel hashes.
2. Verify the package SHA-256 and compare the direct CLI's package summary/object listing with the Assets MCP `get_package_info`, `list_package_objects`, and `search_objects` results for `LevelMap_Ext_Boyle`.
3. Run UModel `-export` for the exact object name and route output to a previously absent directory under `assets/extracted/`.
4. Record the exit code, emitted file path, output hash, byte length, and TGA header dimensions/format fields.

Reproduce from the repository root in PowerShell:

```powershell
third_party\ueviewer-gildor\umodel.exe `
  -export -game=dis `
  -path="Dishonored RHCP\DishonoredGame\CookedPCConsole" `
  -out="assets\extracted\umodel-real-export-sample" `
  UI_Map_Boyle_SF.upk LevelMap_Ext_Boyle
```

## Observations

- Direct UModel `-list` reports four exports in the package: `ObjectReferencer ObjectReferencer_40`, two `Package` rows, and `Texture2D LevelMap_Ext_Boyle`. The direct package summary reports version `801/30`, engine `9098`, 30 names, four exports, and five imports.
- The connected Assets MCP `get_package_info` reports the same four exports and a histogram containing one `Texture2D`, but returns `object_count=0`. `list_package_objects` returns zero items and `search_objects("LevelMap_Ext_Boyle")` returns zero items. The direct CLI does list the named Texture2D. This is a package-scoped MCP catalog/list discrepancy; it does not establish the cause or behavior for all packages.
- The real UModel `-export` command exited 0, found the named object, and wrote `LevelMap_Ext_Boyle.tga` under ignored extraction storage. The file is 1,192,609 bytes with SHA-256 `1442E2AF02CC624A635C77F8F887693BD287D0D534A35B3AAF6195EA72F80D13`.
- The TGA header reports image type 10 (RLE true-color), width 800, height 500, 32 bits per pixel, and descriptor 0. A small structural pass over the RLE packets accounts for exactly 400,000 pixels and consumes all 1,192,591 bytes after the 18-byte header, with no trailing bytes. UModel also logged `UTexture2D LevelMap_Ext_Boyle: dropping 4 bytes`; the meaning and effect of those bytes are unknown.

## Interpretation and claim limits

- **Observed:** this one named Texture2D can be exported to a non-empty TGA file with the pinned UModel build; its header and complete RLE packet stream are structurally valid, and the output hash is reproducible.
- **Observed:** the connected MCP's object-list/search output omits this CLI-listed object even though its package-info class histogram reports the Texture2D export. This is direct evidence of a discrepancy for this package, not proof of a general MCP coverage rate.
- **Unknown:** whether the image pixels match the game's intended rendering, whether the dropped four bytes are benign, whether other object classes/packages export correctly, and whether MCP's empty result is due to cache/index state or parser/list behavior.
- **Limit:** a successful single-object export does not establish whole-package or all-install export compatibility and does not validate package property or bytecode parsing.

## Links

- [EXP-0053 all-install UModel export-object catalog](EXP-0053-all-install-upk-object-catalog.md)
- [EXP-0054 Assets MCP package path indexing](EXP-0054-assets-mcp-full-package-paths.md)
- [EXP-0082 fake-export compatibility census](EXP-0082-umodel-fake-export-census.md)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
