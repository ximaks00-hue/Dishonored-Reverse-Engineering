---
id: EXP-0082
title: Exact-build UModel fake-export compatibility census across installed UPKs
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Across the 904 hash-identified installed UPKs, which resources does the pinned UModel select for fake export, and which packages report warnings or terminate with errors?"
---

# EXP-0082 — Exact-build UModel fake-export compatibility census across installed UPKs

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: run the pinned UModel `-testexport` mode separately on each of the 904 manifest-listed UPKs, after verifying package size/SHA-256 against both the build manifest and EXP-0052 census; collect selected fake-export requests and package-specific warnings/errors.
- Exclusions: no game launch, no claim of successful real asset-file serialization, no property/bytecode completeness claim, no runtime reachability, and no package modification. `_excluded_coop_project/` was not accessed.
- Tools: UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; Python 3 standard library; [census script](../tools/umodel_testexport_census.py).
- Outputs: [summary](../research/packages/umodel-testexport-census/summary.json), [per-package results](../research/packages/umodel-testexport-census/per-package.csv), and [selected resource-class counts](../research/packages/umodel-testexport-census/fake-export-attempts-by-class.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the exact executable hash and pinned UModel hash.
2. Read all 904 UPK entries from `files.csv` and `installed-upk-pkginfo-census.csv`; require matching path sets.
3. Before each invocation, re-hash the package and require byte size/SHA-256 agreement with both recorded sources.
4. Run UModel `-game=dis -testexport <package>` one package at a time, passing `-out` under ignored `assets/extracted/`; capture output in memory and retain per-package counts/samples instead of full logs.
5. Aggregate lines shaped as `Exporting <class> <object> to ...` as **fake-export requests**. Classify warnings, errors, return codes, and packages with no such request. Confirm that the designated output directory contains no files after the pass.

Reproduce from the repository root in PowerShell:

```powershell
python -u tools\umodel_testexport_census.py `
  --umodel third_party\ueviewer-gildor\umodel.exe `
  --game-root 'Dishonored RHCP' `
  --manifest research\builds\BUILD-STEAM-10256413\files.csv `
  --pkginfo-census research\packages\installed-upk-pkginfo-census.csv `
  --out-dir assets\extracted\umodel-testexport-output `
  --output-dir research\packages\umodel-testexport-census
```

## Observations

- All 904 current package files matched their manifest and EXP-0052 census sizes/SHA-256 values at invocation time. UModel loaded all 904 packages in this mode.
- UModel emitted 205,165 fake-export request lines from 721 packages across seven selected resource classes: `Texture2D` 94,305; `MaterialInstanceConstant` 39,078; `StaticMesh3` 33,944; `LightMapTexture2D` 31,442; `SkeletalMesh3` 4,055; `Material3` 2,321; `AnimSet` 20.
- Package outcomes: 485 packages had at least one warning line; 472 ended with warnings and no error, 236 had fake-export requests without a reported warning/error, 183 loaded with no fake-export request line, and 13 terminated with an error (all 13 also emitted warnings). The corpus emitted 64,874 warning lines and 13 error lines. Twelve failures were `Access violation (C0000005)` at `umodel.exe+0x870E`; one was `General Protection Fault`. The 13 errors cover two CookedPCConsole packages, three DLC05, four DLC06, and four DLC07 packages. Exact paths and per-package request/error counts are in the CSV.
- The designated ignored output directory contained zero files after the complete run. `-testexport` logs intended output paths but did not persist asset files in this pass.

## Interpretation and claim limits

- **Observed:** the pinned UModel build selected the recorded resource classes for fake-export handling in the stated packages and returned the recorded warnings and errors on the current hash-identified package set.
- **Unknown:** whether a corresponding real disk export succeeds, whether unselected package classes are exportable by other handlers, completeness/correctness of property or bytecode decoding, and whether any package resource is loaded at runtime.
- **Limit:** the 205,165 count is a count of fake-export request lines, not successful asset files or all package exports. The 183 zero-request packages were nevertheless loadable by the same UModel build. This is not independent payload validation.

## Links

- [EXP-0052 package metadata census](EXP-0052-installed-dlc-package-inventory.md)
- [EXP-0053 export-object catalog](EXP-0053-all-install-upk-object-catalog.md)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [Package archaeology summary](../research/packages/README.md)
