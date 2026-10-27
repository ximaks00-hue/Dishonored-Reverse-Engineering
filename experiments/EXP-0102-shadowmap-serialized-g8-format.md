---
id: EXP-0102
title: Read the serialized ShadowMap format and audit its G8 mip lengths
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What pixel format does UELib report for the sampled ShadowMapTexture2D, and do its decoded mip lengths agree with that format?"
---

# EXP-0102 — Read the serialized ShadowMap format and audit its G8 mip lengths

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `L_ArtDealer_Block.upk`, 7,459,099 bytes, SHA-256 `90485964E570B7E1E71B056585FF393DB8C464ED54A86A018B4738C65837049D`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`. The parsed decompressed package copy hash is recorded in the census JSON.
- Object: `ShadowMapTexture2D'L_ArtDealer_Block.ShadowMapTexture2D_91253'`, UELib index 2110, matching EXP-0098.
- Tools: UELib 1.13.3; updated `uelib_texture_mip_census.ps1` to emit serialized SizeX/SizeY/Format properties, and `audit_uelib_texture_mips.py` with a `PF_G8` byte-length mode; Python 3 and `lzokay==1.1.7`.
- Durable outputs: [updated census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.json), [mip CSV](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.csv), and [G8 length/range audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-shadowmap-artdealer.json).
- Limits: the reported `PF_G8` value is UELib's interpretation of the serialized `Format` property. UModel does not support this object class; there is no independent image decode/pixel comparison or runtime validation.

## Procedure

1. Re-run the EXP-0098 census on the same decompressed package and object index.
2. Record `SizeX`, `SizeY`, and `Format` from the object's serialized UELib property list, separately from parser class type.
3. Decode all external LZO and inline ranges and require G8 payload length `width × height` for every mip.
4. Preserve UModel's unsupported-class observation as the reason independent image comparison is unavailable.

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

- UELib's serialized object property rows report `SizeX=1024`, `SizeY=1024`, and `Format=EPixelFormat.PF_G8`. The native parser type is `UELib.Engine.UShadowMapTexture2D`; the export class remains `ShadowMapTexture2D`.
- The 11 census mip records comprise three external and eight inline levels. All source bounds pass; all inline ranges lie inside the export serial interval.
- All three external mip LZO streams and eight inline mips decode. For each mip, decoded length exactly equals `width × height`, as expected for the reported one-byte PF_G8 representation.
- UModel continues to report this class unsupported in both the full-resource and isolated-package export attempts documented by EXP-0098; no TGA is available.

## Interpretation and claim limits

- **Observed:** UELib reports serialized `Format=EPixelFormat.PF_G8`; all decoded mip lengths equal one byte per reported pixel.
- **Inferred, sample-scoped:** the parser's reported PF_G8 format is internally consistent with the payload lengths for this object.
- **Unknown:** whether UELib's property interpretation exactly matches engine runtime format handling, the decoded pixel values/visual semantics, and behavior for other ShadowMap objects.
- **Claim status: mixed.** Serialized property text and byte-length consistency are evidenced; independent format/image validation and runtime use are unavailable.

## Links

- [EXP-0098 initial ShadowMap census and UModel gap](EXP-0098-shadowmap-uelib-mip-census-umodel-gap.md)
- [Census helper](../tools/uelib_texture_mip_census.ps1)
- [Mip audit helper](../tools/audit_uelib_texture_mips.py)
- [Census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-ShadowMapTexture2D_91253.json)
- [G8 audit output](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-shadowmap-artdealer.json)
