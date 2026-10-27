---
id: EXP-0087
title: All-install UModel fake-export cohorts against UELib class/property coverage
experiment_status: done
claim_status: observed
build: "10256413"
question: "Across seven UModel fake-export classes, how do aggregate UELib export labels, wrapper types, deserialization states, and formatted default-property rows compare over the same 904-package install?"
---

# EXP-0087 — All-install UModel fake-export cohorts against UELib class/property coverage

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: aggregate seven UModel fake-export class request counts by package and compare them with selected export-class labels, UELib wrapper types/states, and UELib formatted default-property rows across all 904 manifest-listed UPKs. This uses the EXP-0070 initialization-only corpus; it does not explicitly invoke `UObject.Load()` on `ShouldDeserializeOnDemand` objects.
- Exclusions: no object-level UModel-to-UELib join; fake-export requests are selection/serialization attempts, not successful file exports. No claim that UELib's formatted defaults represent all serialized fields, or that either parser is correct/complete. No runtime claim; `_excluded_coop_project/` was not accessed.
- Inputs: EXP-0052 exact-build UModel object census, EXP-0070 UELib initialized corpus, EXP-0082 per-package fake-export census, and current exact-build manifest.
- Tools: [cohort summarizer](../tools/summarize_export_class_property_coverage.py), Python 3 standard library. Full outputs: [CSV](../research/packages/uelib-umodel-class-property-coverage/class-coverage.csv) and [summary JSON](../research/packages/uelib-umodel-class-property-coverage/summary.json).

## Procedure

1. Require the package paths in the manifest, UELib package summaries, and UModel fake-export census to match all 904 UPKs.
2. Require every UELib source size/hash and UModel observed source size/hash/identity flag to match the build manifest.
3. For each package, count UELib export rows matching the explicit class-label crosswalk below, wrapper type `UnknownObject` vs other, `Deserialized` states, and owner-index matches in `default-properties.jsonl`.
4. Sum UModel fake-export requests and count packages with requests by class. Report same-package overlap only; do not treat the aggregate as object-level equivalence.

Reproduce from the repository root:

```powershell
python tools\summarize_export_class_property_coverage.py `
  --manifest assets\manifests\packages.csv `
  --uelib-run-dir assets\extracted\uelib-object-init-full `
  --umodel-per-package research\packages\umodel-testexport-census\per-package.csv `
  --output-dir research\packages\uelib-umodel-class-property-coverage
```

Crosswalk used: UModel `Texture2D` → UELib label `Texture2D`; `MaterialInstanceConstant` → same label; `StaticMesh3` → `StaticMesh`; `LightMapTexture2D` → same label; `SkeletalMesh3` → `SkeletalMesh`; `Material3` → `Material`; `AnimSet` → same label. These are aggregate naming correspondences, not proof of identical object sets.

## Observations

- All 904 manifest paths have one UELib package summary and one UModel census row. For every package, UELib-recorded size/SHA-256 and UModel-observed size/SHA-256 match the manifest; the UModel identity flag is true.
- The selected UModel classes account for 205,165 fake-export requests. The mapped UELib class labels account for 219,802 export rows. These totals have different definitions and are not expected to be equal.

| UModel class | UELib class label | UELib exports | UELib `UnknownObject` | UELib `Deserialized` | Objects with default-property rows / rows | UModel requests | UELib class packages | UModel request packages | Shared packages |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Texture2D | Texture2D | 92,846 | 0 | 0 | 0 / 0 | 94,305 | 720 | 721 | 720 |
| MaterialInstanceConstant | MaterialInstanceConstant | 45,120 | 45,120 | 0 | 0 / 0 | 39,078 | 483 | 481 | 481 |
| StaticMesh3 | StaticMesh | 34,856 | 34,856 | 0 | 0 / 0 | 33,944 | 460 | 452 | 452 |
| LightMapTexture2D | LightMapTexture2D | 31,442 | 31,442 | 0 | 0 / 0 | 31,442 | 325 | 325 | 325 |
| SkeletalMesh3 | SkeletalMesh | 4,323 | 4,321 | 2 | 2 / 8 | 4,055 | 275 | 267 | 267 |
| Material3 | Material | 3,667 | 0 | 0 | 0 / 0 | 2,321 | 427 | 374 | 372 |
| AnimSet | AnimSet | 7,548 | 7,547 | 1 | 0 / 0 | 20 | 260 | 19 | 19 |

- The two skeletal-mesh rows with UELib state `Deserialized` are `Engine.Default__SkeletalMesh` (six property rows) and `Ply_Player.Skm_Player` (two property rows). The single AnimSet row with state `Deserialized` has no formatted default-property rows.
- For Material and Texture2D labels, UELib emits non-`UnknownObject` wrapper types in this corpus, but none of the selected export rows has state `Deserialized` or an associated formatted default-property row.
- For the other mapped export classes, UELib's object type is `UnknownObject` for every mapped row except the two skeletal-mesh rows and one AnimSet row described above.

## Interpretation and claim limits

- **Observed, initialization-only:** seven large resource-class cohorts have sparse or zero formatted default-property output in the `InitializePackage()` corpus. Five mapped UELib classes are entirely `UnknownObject`; the Material and Texture2D labels have non-`UnknownObject` wrappers but no `Deserialized` state or default-property rows in this pass. These counts do not measure coverage after explicit on-demand loading.
- **Observed:** all package identities reconcile across the three inputs, and the same-package overlap counts show that class labels/requests are present in broadly similar—but not identical—package sets for these mappings.
- **Clarified by [EXP-0088](EXP-0088-uelib-all-install-on-demand-object-load.md):** the initialization-only gap substantially reflects the omitted `UObject.Load()` path: the full on-demand pass deserialized the selected seven mapped cohorts and emitted property rows for them. Array/value coverage remains incomplete. UModel fake-export attempts still do not prove successful file output, and the mapped labels still do not identify one-to-one object sets.
- **Limit:** aggregate class-label crosswalk over seven cohorts. Same-package overlap is not object identity. Fake-export counts are not success counts. Formatted `default-properties` rows are not a complete inventory of serialized resource fields.

## Links

- [EXP-0070 all-install UELib initialization](EXP-0070-all-install-uelib-object-initialization-profile.md)
- [EXP-0082 UModel fake-export census](EXP-0082-umodel-fake-export-census.md)
- [EXP-0084 selected real UModel exports](EXP-0084-umodel-real-export-class-samples.md)
- [EXP-0088 all-install UELib on-demand object loading](EXP-0088-uelib-all-install-on-demand-object-load.md)
- [Cohort summarizer](../tools/summarize_export_class_property_coverage.py)
