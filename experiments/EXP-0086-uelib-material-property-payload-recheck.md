---
id: EXP-0086
title: Recheck material property payload views with UELib and UModel dump
experiment_status: done
claim_status: observed
build: "10256413"
question: "On an exact-hash material package, does a fresh UELib initialization expose the property views that UModel emits for two selected material exports?"
---

# EXP-0086 — Recheck material property payload views with UELib and UModel dump

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: freshly decompress and initialize one source package with Eliot.UELib 1.13.3; compare two named exports with UModel's independent `-dump` output and recorded export-table serial ranges.
- Exclusions: no claim that either tool is complete/correct, that formatted references are runtime dependencies, or that the loaded textures are used in-game. No game launch or package mutation; `_excluded_coop_project/` was not accessed.
- Source: `DishonoredGame/CookedPCConsole/L_Pub_Night_P.upk`, 955,615 bytes, SHA-256 `A0006B2220A0E2729F77E4EEB050EBADED0E69B8B7144057DC9E8DE9E2276556`, matching the exact-build manifest.
- Tools: Eliot.UELib 1.13.3 through [package extractor](../tools/uelib-package-relations/Program.cs); Gildor UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; UE package decompressor SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`.
- Ignored fresh UELib outputs: `assets/extracted/uelib-property-recheck/`.

## Procedure

1. Ran the extractor against only the exact-hash package, using its manifest row, the pinned decompressor and `--initialize`:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-package-relations -- `
  --game-root 'Dishonored RHCP' `
  --manifest assets\manifests\packages.csv `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-dir assets\extracted\uelib-property-recheck `
  --initialize `
  --only DishonoredGame/CookedPCConsole/L_Pub_Night_P.upk
```

2. Invoked UModel's developer dump on the same package and `Moon_PMAT`:

```powershell
third_party\ueviewer-gildor\umodel.exe -dump -game=dis `
  -path='Dishonored RHCP/DishonoredGame/CookedPCConsole' `
  L_Pub_Night_P.upk Moon_PMAT
```

3. Matched named export rows to the re-extracted package/export table and to UELib's initialized object rows by package index.

## Observations

- UELib processed one package with 320 export/import object rows and 550 package-table relation rows; the initialization summary lists 320 initialized objects, zero default properties, zero formatted reference mentions, and no top-level initialization error. All object states in this package were `0`.
- `Moon_PMAT` is export index 124, class `Material`, serial size 488, serial offset 964970. UELib initialized it as `UMaterial`, state `0`, with zero default-property rows.
- `Moon_HUB_Night_INST` is export index 132, class `MaterialInstanceConstant`, serial size 648, serial offset 966667. UELib initialized it as `UnknownObject`, state `0`, with zero default-property rows.
- UModel `-dump` found `Moon_PMAT` as `Material3`, printed `TwoSided=false`, `ReferencedTextures[2]`, `Expressions[18]`, blend/opacity values, and collected parameter fields. It printed two texture references: `Vfx_Materials.Textures.Moon` and `Skies02.FLOODED.Sky_Flooded_Rafinery_d`.
- During that dump UModel also logged loading the two named Texture2D objects and reported “dropping 4 bytes” for each texture. This records tool behavior, not validated texture content or dependency ownership.

## Interpretation and claim limits

- **Observed:** for this exact package and these two exports, a fresh UELib 1.13.3 initialization emitted no default-property rows, while UModel's dump path produced a populated property view for `Moon_PMAT` and loaded two named textures.
- **Unknown:** why UELib returns state `0` and no rows here; whether its class/object setup, legacy format handling, or call path explains the difference; whether UModel's formatted fields faithfully represent every serialized field; and whether any listed references are selected or used at runtime.
- **Limit:** one package and two exports. Serial size/offset identify the table ranges, not decoded property boundaries. The `-dump` output and its texture-load side effects do not independently confirm rendering, completeness, or runtime dependency resolution.

## Links

- [EXP-0085 selected UELib/UModel property-view comparison](EXP-0085-uelib-umodel-property-views.md)
- [UELib extractor](../tools/uelib-package-relations/Program.cs)
- [UELib all-install initialization profile](EXP-0070-all-install-uelib-object-initialization-profile.md)
