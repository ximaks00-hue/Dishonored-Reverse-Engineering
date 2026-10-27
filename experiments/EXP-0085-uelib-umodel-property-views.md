---
id: EXP-0085
title: Selected UELib and UModel property-view comparison
experiment_status: done
claim_status: mixed
build: "10256413"
question: "For three selected objects, how do UELib initialized property rows compare with UModel formatted property dumps?"
---

# EXP-0085 — Selected UELib and UModel property-view comparison

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: compare UELib's all-install initialized-object/default-property JSONL rows with UModel `.props.txt` dumps for three exact objects selected from EXP-0084; compare field-name sets and four selected scalar values.
- Exclusions: this compares parser-produced views, not raw serialized property bytes; no runtime behavior, dependency ownership, or semantic correctness claim. No game launch or source package modification; `_excluded_coop_project/` was not accessed.
- Inputs: [sample definitions](../research/packages/uelib-umodel-property-comparison/selected-objects.csv), [comparison table](../research/packages/uelib-umodel-property-comparison/comparison.csv), [summary](../research/packages/uelib-umodel-property-comparison/summary.json); UELib corpus under ignored `assets/extracted/uelib-object-init-full/` and UModel dumps under ignored `assets/extracted/umodel-real-class-samples/`.
- Source package identities from the exact-build manifest: `Engine.upk` SHA-256 `8BFB32268205FB1AB94D8AEDE034BF13977FA6496A2701E979C24AF9900E7AE8`; `L_Pub_Night_P.upk` SHA-256 `A0006B2220A0E2729F77E4EEB050EBADED0E69B8B7144057DC9E8DE9E2276556`.
- Tool: [comparison script](../tools/compare_uelib_umodel_properties.py), Python 3 standard library.

## Procedure

1. Match initialized UELib export rows by package path and object name; require one row with the expected export class.
2. Collect `default-properties.jsonl` rows by package and package index.
3. Extract top-level field names from the matching UModel `.props.txt` dump and compare sets; normalize decimal formatting for the four explicitly selected scalar checks.

Reproduce from the repository root:

```powershell
python tools\compare_uelib_umodel_properties.py `
  --uelib-run-dir assets\extracted\uelib-object-init-full `
  --samples research\packages\uelib-umodel-property-comparison\selected-objects.csv `
  --output-dir research\packages\uelib-umodel-property-comparison
```

## Observations

- Three sample objects resolved uniquely in the UELib corpus. `Skm_Player` (Engine.upk, package index 20592) is a `SkeletalMesh` with `Deserialized` state and two UELib property rows: `LODInfo` and `Sockets`. UModel reports seven top-level fields; the shared names are `LODInfo` and `Sockets`, with five additional UModel names.
- All four selected scalar checks for `Skm_Player` match across both parser views: `DisplayFactor=0`, `LODHysteresis=0.02`, `SocketName=RightHandWpn`, and `BoneName=handAttachment_R_jnt`.
- `Moon_PMAT` (L_Pub_Night_P.upk, index 124) has UELib class `Material`, `UMaterial` object type, state `0`, and no rows in the selected default-property table; its UModel dump has 19 top-level fields.
- `Moon_HUB_Night_INST` (same package, index 132) has UELib class `MaterialInstanceConstant`, `UnknownObject` type, state `0`, and no selected default-property rows; its UModel dump has 16 top-level fields.
- No sample has an identical full field-name set. The summary reports 3 samples, 4 selected scalar checks, and 4 cross-parser matches.

## Interpretation and claim limits

- **Observed:** the selected `Skm_Player` values agree across these UELib and UModel formatted views, while the field-name sets differ.
- **Observed:** for the two selected material objects, UELib's current initialized/default-property corpus exposes no rows while UModel emits populated property dumps. This demonstrates a coverage difference in these parser outputs; the comparison does not identify which output is complete or correct.
- **Unknown:** raw serialized property correctness, full property coverage, and whether fields omitted from one view are absent from package bytes. Material references in formatted dumps are not evidence of runtime dependency ownership.
- **Limit:** three objects, two packages, and four selected scalar values; results do not generalize to all object classes or packages.

## Links

- [EXP-0070 UELib all-install object initialization](EXP-0070-all-install-uelib-object-initialization-profile.md)
- [EXP-0084 selected real UModel exports](EXP-0084-umodel-real-export-class-samples.md)
- [Comparison script](../tools/compare_uelib_umodel_properties.py)
