---
id: EXP-0057
title: UELib function-object and decompiler-output census for all function-bearing UPKs
experiment_status: done
claim_status: observed
build: "10256413"
question: "Across every UPK containing a UModel Function export label, how many exported UELib functions initialize, and how many non-native outputs yield non-comment body lines?"
---

# EXP-0057 — UELib function-object and decompiler-output census for all function-bearing UPKs

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: decompress and initialize all eight packages with standalone `Function` labels from EXP-0056, compare each UELib exported `UFunction` count with UModel labels, and classify function flags and decompiler output.
- Exclusions: decompiler output is not original source; this procedure does not prove semantic equivalence or complete bytecode recovery. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: UEViewer `decompress.exe` SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`; Eliot.UELib 1.13.3; reproducible helper [uelib-function-census](../tools/uelib-function-census/).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the recorded executable hash.
2. Confirm each source package path, size, and hash against the package census/catalog.
3. Decompress the eight packages below to ignored `assets/extracted/uelib_base_packages/`; load each read-only with UELib and call `InitializePackage()`.
4. Count UELib `UFunction` objects, distinguishing those with `ExportTable` from those with `ImportTable`; compare each exported count to UModel `object_class='Function'` rows.
5. For every exported UFunction, inspect the low-level Native flag bit (`0x400` as rendered by UELib), `ScriptSize`, and output of `Decompile()`.
6. Count a non-comment body line using this heuristic: in the decompiled string, locate the first line break followed by `{`; inspect subsequent lines; count the function if any trimmed body line is non-empty, is not `}`, and does not start with `//`.

## Observations

- All eight packages are reported by UELib as `IsScript() == true`.
- For every package, UModel's standalone `Function` export-label count equals the number of UELib exported `UFunction` objects.

| Package | UModel `Function` labels | UELib exported functions | Imported UFunctions | Native | Non-native | Non-native with body lines | Non-native without body lines |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Core.upk` | 272 | 272 | 0 | 251 | 21 | 15 | 6 |
| `Engine.upk` | 2,936 | 2,936 | 18 | 1,221 | 1,715 | 1,201 | 514 |
| `GFxUI.upk` | 161 | 161 | 8 | 132 | 29 | 18 | 11 |
| `GameFramework.upk` | 105 | 105 | 33 | 32 | 73 | 58 | 15 |
| `IpDrv.upk` | 3 | 3 | 0 | 1 | 2 | 1 | 1 |
| `OnlineSubsystemPC.upk` | 153 | 153 | 2 | 5 | 148 | 18 | 130 |
| `OnlineSubsystemSteamworks.upk` | 161 | 161 | 3 | 55 | 106 | 53 | 53 |
| `DishonoredGame.upk` | 981 | 981 | 116 | 875 | 106 | 94 | 12 |
| **Total** | **4,772** | **4,772** | **180** | **2,572** | **2,200** | **1,458** | **742** |

- All eight packages initialized successfully; the 180 imported functions are not included in the 4,772 exported denominator.
- The helper emitted eight UTF-8 JSONL files containing one UELib decompiler record per exported function. A separate JSON parse/count pass validated all 4,772 records: 2,572 Native-flagged and 2,200 non-native. The generated corpus totals 2,874,035 bytes at local run directory `assets/extracted/uelib-census/20261026-223104-799-bffd6b27/` and is ignored by Git.
- For `Engine.upk`, UELib reported 20,704 exports, 145 imports, and 20,849 initialized objects; the decompressed output was 6,507,707 bytes from a 2,506,430-byte source.
- UELib emitted an unrelated `Trailing data for object SkeletalMesh'Ply_Player.Skm_Player'` diagnostic while initializing `Engine.upk`; function counts were returned.
- Example non-native outputs include event stubs (`Destroyed`, `Timer`) with only a commented return and bodies with emitted statements such as `HitWall` and `UsedBy`. Some decompiled bodies contain generated placeholders such as `__NFUN_3970__` for calls UELib did not resolve.

## Interpretation / claims

- **Observed:** UModel's label count equals UELib's exported `UFunction` count in all eight packages: 4,772/4,772; UELib also creates 180 imported UFunction objects.
- **Observed:** 2,572 exported UFunctions have the Native flag set and 2,200 do not. Under the stated textual heuristic, 1,458 non-native decompiler outputs contain at least one non-comment body line.
- **Unknown:** semantic completeness of those 1,458 bodies, correctness of unresolved `__NFUN` placeholders, and whether any output that fails the heuristic still conveys useful script semantics.
- **Not established:** that all 1,458 outputs are complete or correct, that the Native flag categorizes actual implementation ownership without exceptions, or that `ScriptSize` equals bytecode length/source length.
- The heuristic measures emitted text only. It is a reproducible triage metric, not an independent validation of UELib's bytecode decompiler.

## Reproduction and limitations

- From the repository root, run the [UELib census helper](../tools/uelib-function-census/README.md) with the eight source package paths listed in Procedure and `--emit-decompiled-jsonl`. It invokes the recorded Gildor package decompressor, uses unique ignored output directories, emits the JSON counts, and writes one JSONL source record per exported UFunction.
- The helper loads each package with Eliot.UELib 1.13.3 and distinguishes `ExportTable != null` from `ImportTable != null`.
- The helper uses flag raw value bit `0x400` for the Native split. Its `nonNativeWithBodyLines` metric follows the output heuristic specified in Procedure step 6.
- Decompressed packages are local-only under `assets/extracted/`; they are not Git artifacts. This census covers the eight package paths with UModel standalone `Function` labels (4,772 exported labels); it is not a denominator for all 72,437 executable functions or for bytecode embedded in class/unknown-object payloads.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- All-install UModel function-label distribution: [EXP-0056](EXP-0056-standalone-function-export-distribution.md)
- All-install object catalog: [EXP-0053](EXP-0053-all-install-upk-object-catalog.md)
- Package census: [installed-upk-pkginfo-census.csv](../research/packages/installed-upk-pkginfo-census.csv)
- Decompressor provenance: [README](../tools/ue-package-decompressor/README.md)
- Census helper: [README](../tools/uelib-function-census/README.md), [source](../tools/uelib-function-census/Program.cs)
