---
id: EXP-0069
title: All-install UELib import/export table relation census
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can UELib parse import/export object-table indices across all installed UPKs, and how do the resulting counts reconcile with the manifest and independent UModel package census?"
---

# EXP-0069 — All-install UELib import/export table relation census

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: parse UELib 1.13.3 import/export tables for all 904 manifest-listed UPKs without initializing package objects; emit package-local outer/class/super/template/archetype signed table-index relations; reconcile package hashes and import/export counts against the manifest and prior UModel census; derive candidate import-root-to-UPK filename-stem joins.
- Exclusions: no game launch, package mutation, asset export, runtime reachability check, or property-payload/bytecode object-reference extraction; `_excluded_coop_project/` was not accessed.
- Tools: UELib 1.13.3; `tools/uelib-package-relations/`; `tools/summarize_uelib_package_relations.py`; existing `tools/ue-package-decompressor/decompress.exe`; package manifest and EXP-0052 metadata census.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify local executable identity.
2. Used .NET reflection on the installed UELib 1.13.3 assembly to inspect the public table model. `UObjectTableItem` exposes `ObjectName` and signed `OuterIndex`; `UExportTableItem` exposes `ClassIndex`, `SuperIndex`, `TemplateIndex`, and `ArchetypeIndex`; `UImportTableItem` exposes class/package names.
3. Probed `Core.upk`, then ran the relation extractor across all `.upk` rows in the build manifest. For each package it streamed SHA-256, compared size/hash to the full-path package manifest, decompressed to a temporary directory, loaded import/export tables with `FileAccess.Read`, emitted JSONL metadata, and removed the decompressed package in a `finally` block. `InitializePackage()` was not called.
4. Emitted one object-table row for each import/export item and one edge row for each non-null import outer or export outer/class/super/template/archetype index. Target indices are resolved only against the same package's import/export table rows.
5. Ran the summarizer to compare every UELib export/import count and source hash/size against the independent UModel package census and package manifest. It also grouped import table root package names and matched them to installed UPK filename stems, retaining ambiguous or unmatched results as such.
6. Saved compact summaries and per-package CSVs under [uelib-package-relations](../research/packages/uelib-package-relations/); full generated object and edge JSONL remains under ignored `assets/extracted/uelib-package-relations-full/`.

## Observations

- UELib loaded all 904 manifest-listed packages; 904/904 source byte lengths and SHA-256 values matched the package manifest. The run reported zero package failures.
- UELib parsed 2,885,414 export-table rows and 225,535 import-table rows. For every package, the UELib export/import counts match the independent EXP-0052 UModel `-pkginfo` census; total package count, exports, and imports all reconcile with zero mismatches.
- The table extractor recorded 3,110,949 combined import/export object rows and 6,278,432 non-null relation indices: 213,955 import outers; 2,783,003 export outers; 2,880,410 export class indices; 5,355 export super indices; zero export template indices; and 395,709 export archetype indices. All 6,278,432 non-null indices resolve to a row in the same package's import/export tables; the generated edge file contains zero `unresolved` targets.
- All 904 source packages contain at least one distinct import-root package-name group. The import table produces 2,416 source-package/import-root-name pairs. Of these, 2,287 names have exactly one installed UPK filename-stem candidate; 129 have no filename-stem match; none are ambiguous under this exact stem-match rule.
- Example: imports from `DishonoredGame/CookedPCConsole/DishonoredGame.upk` include rows whose import root is `Engine` and `AkAudio`; the manifest has unique candidate UPKs `Engine.upk` and `AkAudio.upk`. This is a candidate path association derived from import records and filenames.
- Package version fields read by UELib are 801 and licensee version 30 for all 904 rows.

## Interpretation / claims

- **Confirmed for this named manifest and parser pass:** UELib 1.13.3 parsed import/export table rows for 904/904 packages with exact source hash/size agreement and per-package export/import counts matching the independent UModel census.
- **Confirmed for this UELib output:** all 6,278,432 non-null signed package-table indices resolve against a row in that package's import/export tables. The JSONL preserves each source index, relation field, resolved table kind/index/name, package path, and input hash.
- **Inferred candidate only:** a distinct import-root package name matching one installed UPK filename stem suggests a possible package-file association. It does not prove that the file is loaded, that all imports resolve at runtime, or that the filename is the only source of that namespace.
- **Unknown:** property values and references embedded in serialized payloads, bytecode object operands, cross-package runtime resolution, and actual load/reachability behavior.
- **Limit:** all-install count/hash reconciliation validates this measured parser path and table counts; it does not independently prove every UELib field interpretation against original source or cover non-table dependencies.

## Reproduction and limitations

From the repository root in PowerShell:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-package-relations -- `
  --game-root 'Dishonored RHCP' `
  --manifest research\builds\BUILD-STEAM-10256413\files.csv `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-dir assets\extracted\uelib-package-relations-full

python tools\summarize_uelib_package_relations.py `
  --relations-dir assets\extracted\uelib-package-relations-full `
  --manifest assets\manifests\packages.csv `
  --pkginfo-census research\packages\installed-upk-pkginfo-census.csv `
  --output-dir research\packages\uelib-package-relations
```

The temporary decompressed copy is removed after each package. Use `--only <relative-upk-path>` for a one-package probe. The default output is JSONL under ignored extracted data because the full object/edge rows are large; checked-in summaries preserve the per-package denominator and the aggregate counts.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent package inventory: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- Export catalog: [EXP-0053](EXP-0053-all-install-upk-object-catalog.md)
- Parser initialization limits: [EXP-0062](EXP-0062-uelib-object-initialization-profile.md)
- Summary files: [package relation census](../research/packages/uelib-package-relations/README.md)
- Extractor: [Program.cs](../tools/uelib-package-relations/Program.cs)
- Summarizer: [summarize_uelib_package_relations.py](../tools/summarize_uelib_package_relations.py)
