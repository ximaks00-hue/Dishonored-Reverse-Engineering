---
id: EXP-0062
title: UELib object initialization profile across selected script packages
experiment_status: done
claim_status: observed
build: "10256413"
question: "Which reflection object categories does Eliot.UELib 1.13.3 initialize in selected base and DLC packages, and where does its object model stop?"
---

# EXP-0062 — UELib object initialization profile across selected script packages

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: initialize selected already-decompressed package copies with Eliot.UELib 1.13.3 and count reflection object types and unresolved object placeholders; compare package export totals against the independent manifest/UModel census.
- Sample: seven engine/framework packages with standalone function exports, `DishonoredGame.upk`, and four selected DLC script/map packages (DLC05 chain-kill and oil-rain maps, DLC06 Daud base map, DLC07 endgame map).
- Exclusions: not a census of all 904 UPKs; no package properties/defaults/reference graph are claimed complete; no game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: [uelib-function-census](../tools/uelib-function-census/README.md), Eliot.UELib 1.13.3, UEViewer decompressor, local manifest and UModel package census.

## Procedure

1. Re-read the research status and Blink activation graph; verify the build-record EXE hash. The current EXE hash matches the recorded value. Preserve the distinct PowerWheel item 24, UI enum 2, active-array index 0, and `_iPower` identifiers.
2. Use seven previously decompressed script packages under `assets/extracted/uelib_base_packages/`, the previously decompressed `DishonoredGame.upk`, and four previously decompressed DLC packages under `assets/extracted/umodel_uc_probe*`.
3. Extend the read-only census helper to emit package-level export class labels, initialized CLR object types, class/struct/function/enum/property counts, `UnknownObject` count, failures resolving export objects, and package diagnostics. The helper does not mutate source packages.
4. Run UELib initialization and emit local JSON under ignored `assets/extracted/uelib-census/`; derive a compact CSV at [uelib-object-census-12-package.csv](../research/packages/uelib-object-census-12-package.csv).
5. Compare export totals for the eight base packages against `installed-upk-pkginfo-census.csv`. For the four selected DLC packages, use UELib's own package export totals and prior EXP-0055/0058 evidence; this experiment does not claim a fresh independent UModel per-path count comparison for those four.

Reproduce from repository root in PowerShell:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-function-census -- `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-root assets\extracted\uelib-census `
  --json-output assets\extracted\uelib-census\object-census-20261027.json `
  assets\extracted\uelib_base_packages\Core.upk `
  assets\extracted\uelib_base_packages\Engine.upk `
  assets\extracted\uelib_base_packages\GameFramework.upk `
  assets\extracted\uelib_base_packages\GFxUI.upk `
  assets\extracted\uelib_base_packages\IpDrv.upk `
  assets\extracted\uelib_base_packages\OnlineSubsystemPC.upk `
  assets\extracted\uelib_base_packages\OnlineSubsystemSteamworks.upk `
  assets\extracted\dishonored-blink\DishonoredGame.upk `
  assets\extracted\umodel_uc_probe\L_DLC05_ChainKill_Script.upk `
  assets\extracted\umodel_uc_probe_dlc06\DLC06_DaudBase_Script.upk `
  assets\extracted\umodel_uc_probe_dlc07\L_DLC07_Endgame_Script.upk `
  assets\extracted\umodel_uc_probe_oil\L_DLC05_OilRain_Script.upk
```

## Observations

- All 12 selected packages initialized; the helper reported zero exceptions while resolving export objects. This is not a proof that each object's serialized payload was semantically decoded.
- The eight base packages contain 4,772 exported `UFunction` objects, matching the eight-package standalone Function-label total in EXP-0056/0057. `DishonoredGame.upk` contributes 981.
- For the eight base packages, UELib's package export totals are: Core 1,356; Engine 20,704; GameFramework 888; GFxUI 710; IpDrv 21; OnlineSubsystemPC 519; OnlineSubsystemSteamworks 867; DishonoredGame 30,049. These agree with the package-info census values.
- The four DLC samples have package export totals 2,868; 28,111; 11,025; and 4,640. UELib reports `IsScript=false` for all four, zero exported UFunctions, zero enums and zero properties. It initializes 222, 905, 416, and 204 `UClass` objects, respectively, while marking 2,719, 27,510, 10,869, and 4,389 objects as `UnknownObject`.
- `DishonoredGame.upk` initializes 2,284 `UClass`, 698 `UScriptStruct`, 547 `UEnum`, 13,530 `UProperty`, and 981 exported `UFunction` objects. These are UELib initialized-object counts, not confirmed complete export-kind totals.
- The CSV records per-package source SHA-256, initialized objects, relevant object counts, `UnknownObject` counts, export-resolution failures, and diagnostics count. Full JSON and decompiler output remain in ignored extracted data.

## Interpretation / claims

- **Observed:** UELib 1.13.3 initializes a substantial reflection-object model for the eight selected base script packages, and its package export counts agree with the manifest/package-info census for those packages.
- **Observed:** the four selected DLC script/map packages are class-heavy at the UELib API surface but have thousands of `UnknownObject` placeholders and no initialized enum/property/function objects in this run.
- **Unknown:** whether each DLC `UnknownObject` serialized payload contains class defaults, property data, bytecode, or another object format; whether the zeros reflect package format, UELib support limits, package-specific structure, or some combination.
- **Not established:** all-export semantic parse coverage, property/reference recovery, inheritance/default-object completeness, or package-wide coverage across the 904 installed UPKs.

## Reproduction and limitations

- Run the command above using the already decompressed files, or use the helper's normal source-package mode to decompress into a new ignored output folder.
- Compact CSV: [uelib-object-census-12-package.csv](../research/packages/uelib-object-census-12-package.csv).
- Related standalone function census: [EXP-0057](EXP-0057-engine-upk-function-decompile-census.md); DLC object-boundary probes: [EXP-0055](EXP-0055-uelib-dlc-script-package-boundary.md); all-UPK export-label denominator: [EXP-0056](EXP-0056-standalone-function-export-distribution.md).
- `UnknownObject` counts describe the library's initialized CLR wrapper types. They do not describe the underlying Unreal export class labels or prove payload contents are absent.
- The eight base package export totals are compared to the package-info manifest. The four selected DLC package totals are not a newly generated, independent all-export UModel comparison in this experiment.

## Links

- Build record: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package export census: [installed-upk-pkginfo-census.csv](../research/packages/installed-upk-pkginfo-census.csv)
- Selected-package object profile: [uelib-object-census-12-package.csv](../research/packages/uelib-object-census-12-package.csv)
- Helper: [uelib-function-census README](../tools/uelib-function-census/README.md)
- Project completion contract: [roadmap](../docs/roadmap.md)
