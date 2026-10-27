---
id: EXP-0088
title: All-install UELib on-demand object loading and property coverage
experiment_status: done
claim_status: mixed
build: "10256413"
question: "When UELib's flagged export objects are explicitly loaded, how many deserialize, what property-tag output is emitted, and where do failures/diagnostics remain across all 904 packages?"
---

# EXP-0088 — All-install UELib on-demand object loading and property coverage

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: replay package extraction/initialization for all 904 build-manifest UPKs and explicitly call `UObject.Load()` on every positive export object whose `ShouldDeserializeOnDemand` flag is true. Record object states, UELib exceptions/diagnostics, and formatted property-tag values; reconcile exact package identities/counts and the EXP-0070 default-property baseline.
- Exclusions: these are Eliot.UELib 1.13.3 parser outputs, not independent raw-property decoding or proof of complete field semantics. A `Deserialized` state does not guarantee every tag value was decoded without diagnostics. No runtime behavior or asset correctness claim. `_excluded_coop_project/` was not accessed.
- Tools: Eliot.UELib 1.13.3 from NuGet; pinned repository commit `8e58ffb772547b5fdfe99ba0dbb3331ac3b0a122`; [its UObject implementation](https://github.com/EliotVU/Unreal-Library/blob/8e58ffb772547b5fdfe99ba0dbb3331ac3b0a122/src/Core/Classes/UObject.cs) sets `UnknownObject.ShouldDeserializeOnDemand` and documents those objects as deserialized on demand. UE package decompressor SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`; Python 3 standard library.
- Updated extractor: [UELib package/object extractor](../tools/uelib-package-relations/Program.cs). The `--load-on-demand` mode records the flag, attempt, state, exceptions and parser diagnostics, evaluates/emits properties, then disposes each loaded object buffer after its rows are written.
- Full output is ignored under `assets/extracted/uelib-object-init-ondemand-full/`; full run log is `assets/extracted/uelib-object-init-ondemand-full-run.log`. Durable outputs: [summary JSON](../research/packages/uelib-on-demand-coverage/summary.json), [package matrix](../research/packages/uelib-on-demand-coverage/by-package.csv), [group matrix](../research/packages/uelib-on-demand-coverage/by-group.csv), [seven fake-export class crosswalk](../research/packages/uelib-on-demand-coverage/by-export-class.csv), [all on-demand export-class results](../research/packages/uelib-on-demand-coverage/on-demand-by-export-class.csv), [object failures](../research/packages/uelib-on-demand-coverage/on-demand-failures.csv), and [baseline-owner overlap](../research/packages/uelib-on-demand-coverage/baseline-on-demand-overlap.csv).

## Procedure

1. Re-read research status, Blink graph, build record, and repo instructions; verify the EXE SHA-256.
2. Rebuilt/reran the package extractor against all paths in `assets/manifests/packages.csv`, using source size/hash checks, the pinned decompressor, `--initialize`, and `--load-on-demand`:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-package-relations -- `
  --game-root 'Dishonored RHCP' `
  --manifest assets\manifests\packages.csv `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-dir assets\extracted\uelib-object-init-ondemand-full `
  --initialize `
  --load-on-demand *> assets\extracted\uelib-object-init-ondemand-full-run.log
```

3. For each positive-index export with `ShouldDeserializeOnDemand=true`, the extractor invokes `obj.Load()`, captures both `Console.Out` and `Console.Error` diagnostics, emits object/property state and values, and disposes the loaded object buffer after property rows are written. Imports are not passed to `Load()`.
4. Ran the [coverage summarizer](../tools/summarize_uelib_on_demand_coverage.py). It requires 904 exact package paths; matches every UELib source size/hash to the manifest; reconciles each UELib import/export count to the UModel package census; verifies the terminal run summary; compares every EXP-0070 property owner/count to the new output; and writes package, group, class and failure tables.

Reproduce the durable summary:

```powershell
python tools\summarize_uelib_on_demand_coverage.py `
  --manifest assets\manifests\packages.csv `
  --pkginfo-census research\packages\installed-upk-pkginfo-census.csv `
  --prior-profile research\packages\uelib-object-initialization\uelib-object-initialization-by-package.csv `
  --prior-default-properties assets\extracted\uelib-object-init-full\default-properties.jsonl `
  --run-dir assets\extracted\uelib-object-init-ondemand-full `
  --run-log assets\extracted\uelib-object-init-ondemand-full-run.log `
  --output-dir research\packages\uelib-on-demand-coverage
```

## Observations

- Terminal run: 904 packages in scope, 904 processed, 0 package extraction failures. For all 904, source bytes/SHA-256 matched the build manifest, and UELib import/export totals matched the independent UModel census. There were 0 top-level initialization errors and 0 per-package row-reconciliation errors. The run emitted 3,110,949 import/export rows and 6,278,432 initialized-relation rows.
- The extractor attempted `Load()` on 2,842,054 flagged export objects. UELib marked 2,839,406 `Deserialized` and 2,648 `Errorlized`; no exception escaped the `Load()` call because UELib records deserialization exceptions on the object. The failed-object records all contain `DeserializationException`.
- A total of 2,430,566 on-demand-attempted objects have formatted property rows, comprising 13,414,061 rows. Another 4,827 rows belong to objects outside the on-demand attempts. Including the EXP-0070 baseline gives 13,418,888 total rows.
- The EXP-0070 baseline comprised 4,846 rows across 1,065 property owners. All 1,065 owners were found in the new run, with 0 per-owner row-count mismatches. Nineteen baseline rows belong to 12 owners that were also flagged/attempted for on-demand loading; after subtracting that overlap, the pass added a net 13,414,042 property rows over EXP-0070.
- The all-object output reports 325 `valueError` records. For on-demand-loaded rows, the extractor captured 9,220,977 property-value diagnostic lines across 2,048,157 rows; object-load diagnostics total 843,223 lines. Many loaded rows therefore carry a `Deserialized` state while their property values still emit parse diagnostics.

| Install group | On-demand attempts | `Deserialized` | `Errorlized` | Property rows after load |
|---|---:|---:|---:|---:|
| CookedPCConsole | 1,295,965 | 1,293,879 | 2,086 | 6,367,586 |
| DLC05 | 573,292 | 573,065 | 227 | 2,538,604 |
| DLC06 | 415,341 | 415,126 | 215 | 1,946,845 |
| DLC07 | 557,456 | 557,336 | 120 | 2,565,853 |

For the seven crosswalk classes from EXP-0087, explicit loading marked every on-demand attempt `Deserialized` (zero `Errorlized` in these cohorts):

| UModel fake-export class | UELib label | On-demand attempts | UELib objects with property rows | Property rows |
|---|---|---:|---:|---:|
| Texture2D | Texture2D | 92,846 | 92,846 | 908,585 |
| MaterialInstanceConstant | MaterialInstanceConstant | 45,120 | 45,119 | 337,485 |
| StaticMesh3 | StaticMesh | 34,856 | 34,850 | 95,280 |
| LightMapTexture2D | LightMapTexture2D | 31,442 | 31,442 | 163,170 |
| SkeletalMesh3 | SkeletalMesh | 4,321 | 4,323* | 8,034 |
| Material3 | Material | 3,667 | 3,667 | 36,117 |
| AnimSet | AnimSet | 7,547 | 7,545 | 15,090 |

\* The SkeletalMesh label has 4,323 total exports: 4,321 on-demand attempts plus two earlier `Deserialized` objects with existing property rows.

- Of 2,648 `Errorlized` object loads, 2,611 exception messages are enum-name parse failures (`Requested value ... was not found`) and 37 are `EndOfStreamException`. The largest failing export labels are `DisNPCDistractionComponent` (1,821), `DisFogComponent` (267), `DisAmbushRenderProxyComponent` (235), `DisFleeComponent` (205), `DisRatLightComponent` (48), and `ArkComponentContainer` (38). See the object-level CSV for package/index/name/message evidence.
- Selected material array tags remain incomplete after successful object loading. For `Moon_PMAT`, UELib emits the `Expressions` and `ReferencedTextureGuids` tags but reports that the array type was not detected and the expected value size does not match the bytes read. For `Moon_HUB_Night_INST`, its three parameter arrays and `ReferencedTextureGuids` likewise have undetected array types; the scalar `Parent` object reference resolves to `Moon_PMAT`. UModel's separate dump output in EXP-0086 is not used to certify UELib array contents.

## Interpretation and claim limits

- **Observed:** the original EXP-0070/0087 initialization pass did not capture the complete UELib property-tag output for objects flagged on demand. Calling the public `UObject.Load()` path makes large numbers of such object rows available; the 904-package attempt/result counts above are directly reproducible.
- **Observed:** successful UELib object state and emitted tags do not mean every array/property value decoded correctly. The captured diagnostics, 325 value errors, and 2,648 failed loads remain part of the result.
- **Observed:** the seven selected fake-export class label cohorts from EXP-0087 all deserialize in this pass, while that aggregate crosswalk is still not a one-to-one UModel object mapping and does not prove the UModel requests all succeeded.
- **Unknown:** completeness and semantic correctness of the 13.4 million formatted property rows; how to resolve unsupported array element types and the remaining object failures; references' runtime ownership/use; all asset payload semantics and runtime dependencies.
- **Limit:** UELib 1.13.3 only, exact recorded build 10256413, parser-emitted values; no raw serialized-byte decoder or runtime validation. `ShouldDeserializeOnDemand` is an API path indicator, not proof of game behavior.

## Links

- [EXP-0070 initialization/default-property baseline](EXP-0070-all-install-uelib-object-initialization-profile.md)
- [EXP-0085 selected UELib/UModel property views](EXP-0085-uelib-umodel-property-views.md)
- [EXP-0086 fresh material property recheck](EXP-0086-uelib-material-property-payload-recheck.md)
- [EXP-0087 fake-export class property coverage before explicit on-demand loads](EXP-0087-umodel-uelib-export-class-property-coverage.md)
- [Coverage summarizer](../tools/summarize_uelib_on_demand_coverage.py)
