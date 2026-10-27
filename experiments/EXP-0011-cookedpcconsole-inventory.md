---
id: EXP-0011
title: CookedPCConsole package inventory and index repair
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "Do all CookedPCConsole .upk files appear in the package index with matching manifest hashes?"
---
# EXP-0011 — CookedPCConsole package inventory and index repair

- Status: completed for the local copy's top-level `DishonoredGame/CookedPCConsole` directory.
- Scope: filename inventory of `.upk` packages only, metadata cross-check against the local build manifest, and verification of the `dishonored_assets` MCP index. The ignored `_excluded_coop_project/` tree was not accessed or counted.
- Game files were read only. The changes in this experiment are research artifacts under `assets/manifests` and `research/packages`.

## Procedure

1. Listed the top-level `CookedPCConsole` directory through `dishonored_filesystem` and selected entries ending in `.upk`.
2. Compared each relative path against `research/builds/BUILD-STEAM-10256413/files.csv` and copied the recorded byte length and SHA-256 into a package-only inventory.
3. Rebuilt `assets/manifests/packages.csv` using the same 470 paths, lengths, and SHA-256 values so `dishonored_assets` can query the full CookedPCConsole package set.
4. Verified all 470 inventory rows match the package index exactly for path, length, and SHA-256. Queried representative substrings (one unique package, an 8-package mission family, a 3-package font family, and a DLC-marked filename); each returned set matched the local listing.

## Confirmed observations

- The directory has 2,131 top-level files and 470 unique `.upk` names.
- All 470 `.upk` relative paths exist in the local build manifest. No package path was missing from that manifest.
- Package-index rows equal the package-only inventory rows (470/470) including length and SHA-256.
- The MCP list operation returned at most 200 rows in an unfiltered call even when passed `limit=500`. Its substring filter returns matching subsets, enabling targeted lookups; representative filtered subsets matched the local names.
- Six packages were inspected with `ue_explorer.inspect_package`: `DishonoredGame`, `Core`, `Engine`, `AkAudio`, `GFxUI`, and `DishonoredGameFull_P`. All parsed as version 801/licensee 30, cooker 133, compression flags 2. The first five were marked `isScript=true`; `DishonoredGameFull_P` was marked `isScript=false`. Their counts are in the tool output for this record. The `DishonoredGameFull_P` engine version differs (9098) from 9411 on the other five; this is an observed metadata distinction, not an attribution of its cause.
- Case-insensitive `Blink` searches returned 20 matches in `DishonoredGame.upk` (limit 20), 1 in `Core.upk`, 8 in `Engine.upk`, and none in `AkAudio`, `GFxUI`, or `DishonoredGameFull_P`. The sample includes `PowerAttributes_Blink`, `DisTweaks_Blink`, `EBlinkMode`, Blink properties, and unrelated audio/UI/core references. This is a search sample, not a full object census; the 20-result cap truncates the game-package results.

## Filename-family counts

Counts below are independent, overlapping filename-pattern matches, not semantic package categories:

| Name pattern | Count | Examples | Interpretation limit |
| --- | ---: | --- | --- |
| Exact base/framework names: AkAudio, Core, DishonoredGame, Engine, GFxUI | 5 | `Core.upk`, `Engine.upk` | Directly classified by exact filename only |
| Names containing delimited SF/MS/LC*/LRUS markers | 93 | `Abbey_01_Keys_SF.upk`, `DisFonts_LCZEHUNPOL_SF.upk` | Marker meaning is not established here |
| UI/HUD/Menu/Frontend/Loading prefixes | 75 | `UI_HUD_SF.upk`, `UI_GamepadMapping.upk` | Prefix-based filename grouping |
| Names containing delimited Twk/Tweak | 9 | `AudioGraph_Twk_SF.upk` | Filename marker only |
| Names beginning with a word plus two digits and underscore | 1 | `Abbey_01_Keys_SF.upk` | Pattern is suggestive of a mission/level family; not validated |

The pattern sets overlap; do not sum these rows to derive a total. A DLC/trials marker search found one filename containing `DLC` (`UI_HUD_DLCTest_SF.upk`), which is not evidence of DLC package coverage. This inventory does not establish whether all DLCs or languages for the edition are present.

## Interpretation

- **Confirmed:** the asset index now covers the 470 top-level CookedPCConsole `.upk` files in this local copy, with manifest-derived byte sizes and SHA-256 values.
- **Inferred:** suffixes and filename fragments can guide later groupings, but their language/platform/content meaning remains a hypothesis until package metadata or object contents corroborate it.
- **Unknown:** completeness against Steam depots, DLC ownership, and localization coverage are not established by this directory-to-manifest check.
- Scope excludes `_excluded_coop_project/` as instructed in EXP-0010.

## Artifacts

- [Package index](../assets/manifests/packages.csv)
- [Package-only inventory](../research/packages/cookedpcconsole-upk-inventory.csv)
- [Build manifest](../research/builds/BUILD-STEAM-10256413/files.csv)
