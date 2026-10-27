---
id: EXP-0098
title: Census ShadowMapTexture2D mips and record UModel class gap
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can UELib's ShadowMapTexture2D implementation recover bounded mip ranges for an installed object, and can UModel independently export it for pixel validation?"
---

# EXP-0098 — Census ShadowMapTexture2D mips and record UModel class gap

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `L_ArtDealer_Block.upk`, 7,459,099 bytes, SHA-256 `90485964E570B7E1E71B056585FF393DB8C464ED54A86A018B4738C65837049D`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`.
- Object: `ShadowMapTexture2D'L_ArtDealer_Block.ShadowMapTexture2D_91253'`, UELib package index 2110, UModel zero-based export ordinal 2109. Properties report 1024×1024 and cache name `Lighting`.
- Tools: UELib 1.13.3, `uelib_texture_mip_census.ps1`, `audit_uelib_texture_mips.py`, pinned UModel (SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`), Python 3, `lzokay==1.1.7`.
- Durable outputs: [census CSV](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.csv), [census JSON](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.json), and [all-mip range/LZO audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-shadowmap-artdealer.json). Decompressed package and UModel captures are under ignored extraction storage.
- Limits: one object/package; parser ranges and format lengths are audited but there is no independent image comparison. No runtime or TFC index semantics are established.

## Procedure

1. Verify build identity and exact UPK/TFC input hashes.
2. Select the cache-bearing ShadowMapTexture2D object from the UELib corpus; run census with the native `UELib.Engine.UShadowMapTexture2D` implementation.
3. Audit every reported external and inline mip range, LZO payload, and DXT1 decoded size.
4. Attempt UModel export with both the full resource path and an isolated package path; inspect its log and output.

Reproduce census and audit:

```powershell
& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-lightmap-artdealer\decompressed\L_ArtDealer_Block.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  -PackageIndex 2110 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.json

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.csv `
  --package assets\extracted\tfc-lightmap-artdealer\decompressed\L_ArtDealer_Block.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  --pixel-format PF_G8 `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-shadowmap-artdealer.json
```

## Observations

- The export is parsed as `UELib.Engine.UShadowMapTexture2D`, matching its `ShadowMapTexture2D` class without an alias.
- Census reports 11 mips: three external and eight inline. External offsets are 406,588,547; 406,580,459; and 406,578,124 in `Lighting.tfc`. All source ranges are within their respective files; inline ranges are inside the export serial interval `[2,321,783, 2,344,181)`. The summary records `all_mip_ranges_in_file=true` and `all_inline_ranges_within_export_serial=true`.
- All-mip range and LZO audit passes for 11 records. Decompressed byte lengths equal width×height, but no pixel format is established. An attempted DXT1 size check failed (1024×1024 mip yielded 1,048,576 bytes; DXT1 would require 524,288); therefore no DXT1 or image-decoding claim is made.
- UModel `-export` warns `Unknown class "ShadowMapTexture2D" for object "ShadowMapTexture2D_91253"` and reports no supported objects, both with the full resource directory and isolated package. No TGA was produced for comparison.

## Interpretation and claim limits

- **Observed (updated by EXP-0102):** UELib exposes an 11-mip layout and reports serialized `Format=EPixelFormat.PF_G8`; all ranges and LZO payloads pass, and decoded byte counts equal width×height. This is parser/property evidence, not independent pixel-format validation.
- **Observed:** the tested UModel build does not support this class in this package, preventing independent pixel validation.
- **Unknown:** whether UELib's PF_G8 interpretation matches engine runtime handling, visual pixel correctness, how UModel handles this class elsewhere, TFC GUID/index semantics, and runtime use.
- **Claim status: mixed.** The UELib structural result is positive, while the planned independent export comparison is unavailable due to the observed UModel class limitation.

## Links

- [EXP-0095 LightMap cache selection and default UELib gap](EXP-0095-lightmap-tfc-selection-and-uelib-gap.md)
- [EXP-0096 LightMap alias range and pixel validation](EXP-0096-lightmap-alias-mip-range-pixel-validation.md)
- [EXP-0097 second-package LightMap alias validation](EXP-0097-lightmap-alias-second-package-validation.md)
- [EXP-0102 serialized ShadowMap format follow-up](EXP-0102-shadowmap-serialized-g8-format.md)
- [MIP census helper](../tools/uelib_texture_mip_census.ps1)
- [All-mip audit helper](../tools/audit_uelib_texture_mips.py)
