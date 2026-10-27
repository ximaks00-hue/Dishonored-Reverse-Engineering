---
id: EXP-0070
title: All-install UELib object initialization and default property profile
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What object categories and default-property output does UELib 1.13.3 produce when initialized across all 904 installed UPKs, and how does that output reconcile with package inventories?"
---

# EXP-0070 — All-install UELib object initialization and default property profile

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: run Eliot.UELib 1.13.3 package initialization on all 904 manifest-listed UPKs; emit object/type/path and relation records, parser-reported default properties and textual reference mentions, then reconcile source hashes/sizes and per-package table counts against the manifest and independent UModel census.
- Exclusions: no game launch, runtime claim, package mutation, complete UE3 payload-decoding claim, or source-code recovery; `_excluded_coop_project/` was not accessed.
- Tools: .NET/UELib 1.13.3 via [package extractor](../tools/uelib-package-relations/Program.cs), [initialization summarizer](../tools/summarize_uelib_object_initialization.py), UE package decompressor, full UPK manifest, and EXP-0052 UModel package census.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256 against the recorded build.
2. Ran the package extractor with `--initialize` across all 904 `.upk` manifest rows. For each package the tool checked source size/hash, decompressed to a temporary directory, loaded and initialized the package, emitted JSONL records under ignored `assets/extracted/uelib-object-init-full/`, and removed the temporary package in cleanup.
3. Ran the summarizer against the package manifest and EXP-0052 UModel census. It checked full package path coverage, per-package hashes/sizes and import/export counts, aggregated initialized CLR object categories and states, read default-property records, matched parser-formatted reference mentions to same-corpus object paths/classes, and recorded console diagnostics separately because the log does not attribute them to packages.
4. Kept compact package/group CSVs, UnknownObject export-class label counts, and aggregate JSON under [uelib-object-initialization](../research/packages/uelib-object-initialization/). The full JSONL and console log are generated, ignored data.

Reproduce in PowerShell from the repository root:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-package-relations -- `
  --game-root 'Dishonored RHCP' `
  --manifest assets\manifests\packages.csv `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-dir assets\extracted\uelib-object-init-full `
  --initialize *> assets\extracted\uelib-object-init-full-run.log

python tools\summarize_uelib_object_initialization.py `
  --run-dir assets\extracted\uelib-object-init-full `
  --manifest assets\manifests\packages.csv `
  --pkginfo-census research\packages\installed-upk-pkginfo-census.csv `
  --output-dir research\packages\uelib-object-initialization `
  --run-log assets\extracted\uelib-object-init-full-run.log
```

## Observations

- All 904 manifest package paths appear once in the package-table and initialization outputs. All source byte sizes/SHA-256 values match the manifest, and per-package import/export totals match the independent UModel census: zero mismatching packages. The run emitted zero package-error rows and zero top-level initialization-error packages.
- The corpus contains 3,110,949 import/export object rows and 6,413,586 UELib object-relation edges. These are initialized object-model edges, distinct from EXP-0069's signed package-local table indices.
- UELib classified 2,407,117 rows as `UnknownObject` (77.376% of 3,110,949 rows). Their export-class labels include animation sequences, conversation blurbs, animation notifies, particle objects, meshes and texture/light-map objects; the class label does not establish whether a payload is script, asset data, or successfully decoded.
- Object deserialization states were `0`: 3,067,334; `Deserialized`: 43,614; `Errorlized`: 1. One object exception was recorded: `ArkComponentContainer'DishonoredGame.Default__DishonoredAIBrain.ComponentContainer'`, caused by UELib rejecting enum text `2C_Enable_enable_2 colors_18920`.
- Group distribution: CookedPCConsole 1,448,435 rows / 1,023,481 UnknownObject (70.661%); DLC05 610,643 / 522,404 (85.550%); DLC06 448,053 / 366,405 (81.777%); DLC07 603,818 / 494,827 (81.950%). The DLC groups each produced zero UELib function/property wrapper rows in this initialization pass; each did produce UClass rows. This is a parser-output boundary, not proof that payloads or semantics are absent.
- UELib formatted 4,846 default-property entries, with zero `valueError` records. It emitted 288 formatted-text `// Reference:` mentions targeting 283 distinct paths; all mentions matched an initialized object path and export-class label in the same corpus. This is an internal consistency check within one parser output, not independent reference validation.
- The `DishonoredGame.upk` Blink probe reports `DisTweaks_Blink` extending `DisTweaks_ActivePowerBase`, `m_Levels` typed as `PowerAttributes_Blink`, and 19 parser-formatted defaults in that struct, including `m_Distance=2000`, `m_HorizDistance=1400`, `m_VertDistance=400`, `m_fDefaultBlinkStepDistance=300`, and `m_fDefaultTimeBetweenBlinkSteps=0.01`. The relevant Blink default objects remain `UnknownObject` with zero emitted default-property rows in this pass; these defaults are therefore limited to UELib's parsed struct output.
- The 272-line UELib console log contains 22 property-tag value-size error lines, 12 array-type acquisition warning lines, 4 ImportExportGuidsTable exception headers, 1 trailing-data diagnostic, and 14 deserialization-exception headers under the summarizer's literal patterns. The console output does not associate these lines with package paths; no per-package attribution is claimed. Package-error JSONL and top-level initialization summary likewise do not capture these parser console diagnostics.
- Scope clarification from [EXP-0088](EXP-0088-uelib-all-install-on-demand-object-load.md): this experiment recorded properties available after `InitializePackage()` and did not explicitly call `UObject.Load()` for objects marked `ShouldDeserializeOnDemand`. The pinned Eliot.UELib 1.13.3 source documents `UnknownObject` as loaded on demand. Therefore the 4,846 rows here are the initialization-pass baseline, not total UELib property-tag coverage.

## Interpretation and claim limits

- **Confirmed for this named manifest and parser pass:** all 904 source package hashes/sizes and per-package import/export counts reconcile with the manifest and UModel census, and the stated object/default-property/diagnostic counts are reproducible from the generated corpus.
- **Observed:** the UELib object API leaves a large share of rows as `UnknownObject`, including many asset-like export-class labels; initialized DLC reflection wrappers are sparse relative to the base group. This describes UELib 1.13.3's output, not the full semantic coverage of the packages.
- **Observed, parser-scoped:** 4,846 formatted default-property records and 288 same-corpus textual reference mentions were emitted. These are neither raw serialized-property validation nor independently confirmed cross-package reference edges.
- **Observed after follow-up:** an all-install on-demand pass explicitly loaded 2,842,054 flagged exports and emitted 13,414,061 property rows on those attempted objects; see EXP-0088. This establishes that many wrappers yield generic tagged-property output after `Load()`, not that their full semantics are recovered.
- **Unknown:** complete property/array value coverage, remaining failed payloads, whether the DLC wrapper pattern reflects format variation or parser limitations, full default-object coverage, and runtime loading/reachability/use of any relation/default.
- **Limit:** package hash/count reconciliation checks corpus identity and table totals, not the correctness or completeness of UELib's object interpretations. Console diagnostic counts are global and unassigned to packages. UnknownObject percentages use all import/export rows, including asset/map objects, as the denominator.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related package-table baseline: [EXP-0069](EXP-0069-all-install-uelib-package-table-relations.md)
- Prior selected initialization sample: [EXP-0062](EXP-0062-uelib-object-initialization-profile.md)
- Summary files: [initialization profile](../research/packages/uelib-object-initialization/README.md)
- Extractor: [Program.cs](../tools/uelib-package-relations/Program.cs)
- Summarizer: [summarize_uelib_object_initialization.py](../tools/summarize_uelib_object_initialization.py)
