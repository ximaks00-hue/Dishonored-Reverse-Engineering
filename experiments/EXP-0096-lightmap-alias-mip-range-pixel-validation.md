---
id: EXP-0096
title: Validate LightMap mip ranges using an explicit UELib parser alias
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can a UELib UShadowMapTexture2D parser alias recover LightMap mip ranges that reproduce UModel pixels?"
---

# EXP-0096 — Validate LightMap mip ranges using an explicit UELib parser alias

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `Dishonored_MainMenu_Env.upk`, 16,252,497 bytes, SHA-256 `C47769160A26F1986D2077D9C2F8F51A64A0AD695577D4546610EC0A1B79A788`; `Dishonored_MainMenu.upk`, 3,518,959 bytes, SHA-256 `452BD81AC649F611331B312A222557BEF446430C24C30D08A144E015E3769297`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`. Each source hash and size matches the build manifest.
- Object samples: `LightMapTexture2D'Dishonored_MainMenu_Env.DirectionalMaxComponent0_3'` (UELib package index 228, UModel zero-based list ordinal 227), and small inline-only control `LightMapTexture2D'Dishonored_MainMenu.DirectionalMaxComponent0_289'` (UELib package index 209, UModel ordinal 208).
- Parser method: the default UELib class registry constructs `LightMapTexture2D` as `UnknownObject`. For this isolated probe, the enhanced [mip census helper](../tools/uelib_texture_mip_census.ps1) registers an explicit in-memory alias from `LightMapTexture2D` to UELib's `UELib.Engine.UShadowMapTexture2D` parser. The original export class remains recorded as `LightMapTexture2D`; this is a parser compatibility override, not a claim that the engine classes are identical.
- Tools: UELib 1.13.3; pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; [updated LZO/DXT1/TGA verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py), Python 3 and `lzokay==1.1.7`.
- Durable outputs: [large LightMap mip table](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.csv), [census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.json), [all-mip decode/range audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-mainmenu_large-lightmap.json), [pixel verification](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.json), [inline-only control mip table](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu-DirectionalMaxComponent0_289-lightmap.csv), and [control all-mip audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-mainmenu_control-lightmap.json). Decompressed packages, exports, and logs remain under ignored `assets/extracted/tfc-cross-cache-mainmenu/` and `assets/extracted/tfc-lightmap-probe/`.
- Limits: one large and one small LightMap, one TFC, one package family, one explicit parser alias. The top external mip and first inline fallback pixels are verified; no in-game rendering claim is made.

## Procedure

1. Re-read repository instructions, status, Blink graph, build record, and verify EXE/source package/TFC identities against the build manifest.
2. Load the decompressed package with UELib 1.13.3. The default registry returns `UnknownObject` for `LightMapTexture2D` and reports trailing data. Register `LightMapTexture2D` to `UELib.Engine.UShadowMapTexture2D` before package initialization, then load the selected object and record parser type separately from actual export class.
3. Validate all reported mip ranges against the TFC/package files and the export serial range. Do not treat the alias alone as proof that the parser interpretation is correct.
4. UModel-export the object once with the full cooked resource path and once with only the package available. Require explicit cache-read/missing-cache logs and well-formed RLE TGAs.
5. Use the independent byte-to-pixel verifier on external mip 0 and the first inline mip. Separately decompress and DXT1-decode every mip row to ensure its size is consistent with the reported dimensions/format; only claim pixel identity for rows actually compared to UModel TGA output.
6. Apply the same alias to the 32×32 control, whose object has the same cache-name property. Confirm its six mip ranges are inline and its with/without-cache exports are identical.

Reproduce the census and pixel check from repository root:

```powershell
& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-cross-cache-mainmenu\decompressed\Dishonored_MainMenu_Env.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  -PackageIndex 228 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.json `
  -ClassAliasName LightMapTexture2D `
  -ClassAliasImplementationType UELib.Engine.UShadowMapTexture2D

python tools\compare_uelib_mip_data_to_umodel_tga.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.csv `
  --package assets\extracted\tfc-cross-cache-mainmenu\decompressed\Dishonored_MainMenu_Env.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  --mip0-tga assets\extracted\tfc-lightmap-probe-large\with-cache\Dishonored_MainMenu_Env\LightMapTexture2D\DirectionalMaxComponent0_3.tga `
  --inline-fallback-tga assets\extracted\tfc-lightmap-probe-large\no-cache\Dishonored_MainMenu_Env\LightMapTexture2D\DirectionalMaxComponent0_3.tga `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-pixel-verification-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.json

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.csv `
  --package assets\extracted\tfc-cross-cache-mainmenu\decompressed\Dishonored_MainMenu_Env.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-mainmenu_large-lightmap.json
```

## Observations

- With the default class registry, UELib reported `UnknownObject`; its mip payload was unavailable. Explicitly registering the `UShadowMapTexture2D` parser alias produced 11 mip rows for the large LightMap, logged the chosen parser type in the JSON summary, and still emitted a trailing-data diagnostic.
- All 11 mip ranges are within their source files; all eight inline mip ranges lie within the export serial interval `[3,047,493, 3,058,933)`. The census reports three external mips and eight inline mips. Their dimensions, in order, are 1024², 512², 256², 128², 64², 32², 16², 8², and three 4² tails.
- External mip ranges in `Lighting.tfc`: mip 0 offset 547,630,451 size 171,345; mip 1 offset 547,578,423 size 52,028; mip 2 offset 547,562,952 size 15,471. The first inline mip is index 3 at package offset 3,047,797 size 8,192.
- All 11 ranges decompress/read to the UELib-declared element counts and DXT1 block sizes. Mip 0's 4 LZO chunks expand to 524,288 bytes; mip 1 and mip 2 each decode as single LZO chunks to 131,072 and 32,768 bytes. All eight inline payloads are 8,192 bytes or smaller and decode at their reported dimensions.
- External mip 0 decoded to the exact 1024×1024 UModel with-cache TGA: 1,048,576/1,048,576 RGB pixels, mean absolute channel error 0, maximum error 0.
- Inline mip 3 decoded to the exact 128×128 no-cache fallback TGA: 16,384/16,384 RGB pixels, mean absolute channel error 0, maximum error 0.
- The 32×32 control's alias-generated census contains six mips, all inline and within its serial range; external mip count is zero. Its UModel with-cache and package-only exports are identical 32×32 TGAs (SHA-256 `39D43D97FCB5F2BC15413542C24AD818A23AA2EEB1EBF5DAD4F2B66F11A08ABC`).

## Interpretation and claim limits

- **Confirmed for this large object and these parser outputs:** the aliased UELib mip 0 and mip 3 byte ranges, after LZO/DXT1 processing, reproduce UModel's with-cache and no-cache output pixels exactly. The UELib-reported external ranges and inline serial ranges pass file-bound checks.
- **Observed:** a `LightMapTexture2D` can use the same external TFC read/fallback path in pinned UModel. The 32×32 control has no external mip range even though its cache-name property is `Lighting`; that object requires no TFC for the observed UModel export.
- **Inferred, sample-scoped:** `UShadowMapTexture2D`'s UELib binary deserializer is compatible enough with this LightMap sample to recover mip records, because dimensions, all range bounds, decoded sizes, and two independent UModel pixel comparisons agree. The trailing-data warning means parser compatibility is not complete proof of identical class layouts.
- **Unknown:** the semantic cause/content of trailing bytes, whether all LightMap objects share this layout, cache GUID lookup semantics, other TFC subclasses/formats, and game-runtime rendering.
- **Scope limit:** one large and one small LightMap object, one package family, one TFC, one explicit in-memory parser alias, and one pinned UModel build. This is not a corpus-wide LightMap parser.

## Links

- [EXP-0095 initial LightMap cache-selection probe](EXP-0095-lightmap-tfc-selection-and-uelib-gap.md)
- [EXP-0097 second large LightMap in another package](EXP-0097-lightmap-alias-second-package-validation.md)
- [EXP-0094 chunked LZO verifier development](EXP-0094-cross-cache-chunked-lzo-mip-pixel-verification.md)
- [Census helper with explicit alias option](../tools/uelib_texture_mip_census.ps1)
- [Chunk-aware byte-to-pixel verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py)
