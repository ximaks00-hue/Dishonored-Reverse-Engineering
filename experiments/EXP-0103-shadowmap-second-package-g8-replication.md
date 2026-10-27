---
id: EXP-0103
title: Replicate the serialized ShadowMap PF_G8 result in a second package
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does a second package's ShadowMapTexture2D serialize PF_G8 with mip payloads whose decoded lengths match width×height?"
---

# EXP-0103 — Replicate the serialized ShadowMap PF_G8 result in a second package

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `Dishonored_MainMenu.upk`, 3,518,959 bytes, SHA-256 `452BD81AC649F611331B312A222557BEF446430C24C30D08A144E015E3769297`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`. Parsed decompressed copy hash is in the census summary.
- Object: `ShadowMapTexture2D'Dishonored_MainMenu.ShadowMapTexture2D_78538'`, UELib package index 776, UModel zero-based ordinal 775.
- Tools: UELib 1.13.3; mip census helper with serialized texture metadata, PF_G8-capable all-mip audit helper, and pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.
- Durable outputs: [census CSV](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu-ShadowMapTexture2D_78538.csv), [census JSON](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu-ShadowMapTexture2D_78538.json), and [all-mip G8 audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-shadowmap-mainmenu.json). UModel log is under ignored `assets/extracted/tfc-shadowmap-mainmenu/`.
- Limits: one additional small, inline-only object in one package. UModel again rejects the class, so no pixel or TFC external-mip comparison is available.

## Procedure

1. Verify source package/TFC identity in the manifest and use the prior exact-build decompressed MainMenu package copy.
2. Run UELib census on index 776 and record serialized texture properties and all mip ranges.
3. Audit every inline payload as PF_G8, requiring decoded length `width × height`.
4. Attempt UModel export for the same export ordinal/name and capture class support outcome.

```powershell
& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-lightmap-probe\decompressed\Dishonored_MainMenu.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  -PackageIndex 776 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu-ShadowMapTexture2D_78538.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu-ShadowMapTexture2D_78538.json

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu-ShadowMapTexture2D_78538.csv `
  --package assets\extracted\tfc-lightmap-probe\decompressed\Dishonored_MainMenu.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  --pixel-format PF_G8 `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-shadowmap-mainmenu.json

third_party\ueviewer-gildor\umodel.exe -export -game=dis `
  -path="Dishonored RHCP\DishonoredGame\CookedPCConsole" `
  -out=assets\extracted\tfc-shadowmap-mainmenu\export `
  Dishonored_MainMenu.upk ShadowMapTexture2D_78538
```

## Observations

- UELib reports serialized `SizeX=32`, `SizeY=32`, and `Format=EPixelFormat.PF_G8`. The parser type is `UELib.Engine.UShadowMapTexture2D`; the actual export class remains `ShadowMapTexture2D`.
- The census reports six inline mip levels and no external mip ranges. All six ranges are in-file and within the export serial interval. Each payload decodes to exactly `width × height` bytes.
- UModel logs `Unknown class "ShadowMapTexture2D" for object "ShadowMapTexture2D_78538"` and reports that the package has no supported objects for the requested export; no image is written.

## Interpretation and claim limits

- **Observed:** a second package/object has the same UELib-reported serialized PF_G8 value as EXP-0102, and all inline payload lengths agree with one byte per pixel.
- **Observed:** UModel's unsupported-class result recurs for this object in a second package.
- **Inferred, sample-scoped:** PF_G8 is a repeated serialized property for these two sampled ShadowMap objects, not a one-object anomaly.
- **Unknown:** image-value correctness, external TFC payload behavior for ShadowMap, pixel visualization, and engine-runtime format handling.
- **Claim status: mixed.** The serialized property and length consistency replicate; independent image validation remains unavailable.

## Links

- [EXP-0098 initial external ShadowMap sample](EXP-0098-shadowmap-uelib-mip-census-umodel-gap.md)
- [EXP-0102 first PF_G8 serialized-property audit](EXP-0102-shadowmap-serialized-g8-format.md)
- [MIP census helper](../tools/uelib_texture_mip_census.ps1)
- [All-mip audit helper](../tools/audit_uelib_texture_mips.py)
