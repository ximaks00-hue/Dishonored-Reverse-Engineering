---
id: EXP-0099
title: Validate aliased LightMap mip pixels in a third package
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the explicit UELib LightMap parser alias recover and pixel-match external and inline mips for a non-square texture in a third package?"
---

# EXP-0099 — Validate aliased LightMap mip pixels in a third package

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `L_Boyle_Ext_Env.upk`, 18,857,406 bytes, SHA-256 `01606245853FEDACB337E6B7D2D030620E60E597FBB55BED0EEEE5156EF3FF0B`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`. The decompressed UPK used for parsing has SHA-256 `B38CCF3121E144A4BAADEA6070E54A928EDD133EA6CC335A3F62F0C35E50270F`.
- Object: `LightMapTexture2D'L_Boyle_Ext_Env.DirectionalMaxComponent0_10'`, UELib package index 312 and UModel zero-based export ordinal 311. UModel reads a 1024×256 mip from `Lighting.tfc`.
- Tools: UELib 1.13.3, pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, package decompressor SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`, and the mip audit/pixel comparison scripts linked below.
- Durable outputs: [mip census](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.csv), [census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.json), [all-mip audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-boyle-ext-lightmap.json), and [pixel comparison](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.json). UModel logs and image outputs are in ignored `assets/extracted/tfc-lightmap-boyle-ext/`.
- Limits: one non-square LightMap, one additional package, same `Lighting.tfc`, parser alias, and UModel build. The alias emits a trailing-data diagnostic. This does not establish the native class layout, broad parser correctness, or in-game runtime rendering.

## Procedure

1. Verify EXE and package/TFC hashes against the exact build record and manifest.
2. Decompress a separate UPK copy under ignored extraction storage; register `LightMapTexture2D` to `UELib.Engine.UShadowMapTexture2D` in-memory before package initialization.
3. Census object 312 and audit every mip range and DXT1 size/decompression.
4. Export the object with UModel once using the full cooked resource directory and once using an isolated package directory without `Lighting.tfc`.
5. Compare decoded external mip 0 and first inline mip 2 with the corresponding UModel images.

## Observations

- The alias census reports 11 mip levels: two external and nine inline. All ranges are within the TFC or package file; all inline ranges lie in export serial interval `[3,056,116, 3,067,572)`. The full audit successfully decompresses and DXT1-decodes all 11 to their reported dimensions.
- External mip 0 is 1024×256 at `Lighting.tfc` offset 8,388,236 and decodes from one LZO chunk to 131,072 bytes. External mip 1 is 512×128 at offset 8,362,531 and decodes to 32,768 bytes. Inline mip 2 is 256×64 at package offset 3,056,396 and has 8,192 bytes.
- UModel logs `Reading DirectionalMaxComponent0_10 mip level 0 (1024x256) from Lighting.tfc` with the full resource path. The isolated run logs `TFC file "Lighting" is missing` and exports the 256×64 fallback.
- Decoded UELib external mip 0 matches all 262,144 RGB pixels in UModel's with-cache TGA; decoded inline mip 2 matches all 16,384 pixels in the fallback TGA. Both comparisons have zero mean and maximum channel error.

## Interpretation and claim limits

- **Confirmed for this object and parser/export outputs:** the UELib alias-reported external mip 0 and inline mip 2 reproduce UModel pixels exactly; all 11 mip ranges and DXT1 lengths pass the audit.
- **Observed:** UModel cache read and missing-cache fallback behavior recur for a non-square LightMap in a third package. This texture has two external mips, whereas the prior two large samples had three.
- **Inferred, sample-scoped:** the aliased UELib parser locates compatible mip records for this sample. The trailing-data diagnostic remains and no native-class identity claim follows.
- **Unknown:** other LightMap layouts/formats, TFC GUID/index semantics, remaining texture subclasses, and game-runtime selection/rendering.

## Reproduction

```powershell
$outDir = 'assets/extracted/tfc-lightmap-boyle-ext'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
tools/ue-package-decompressor/decompress.exe -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\CookedPCConsole' `
  "-out=$((Resolve-Path $outDir).Path)" L_Boyle_Ext_Env.upk

& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-lightmap-boyle-ext\L_Boyle_Ext_Env.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  -PackageIndex 312 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.json `
  -ClassAliasName LightMapTexture2D `
  -ClassAliasImplementationType UELib.Engine.UShadowMapTexture2D

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.csv `
  --package assets\extracted\tfc-lightmap-boyle-ext\L_Boyle_Ext_Env.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-boyle-ext-lightmap.json
```

The two UModel invocations and byte-to-pixel comparison are recorded in the ignored `assets/extracted/tfc-lightmap-boyle-ext/` logs and outputs; the full command pattern is documented in EXP-0095.

## Links

- [EXP-0096 LightMap alias and control](EXP-0096-lightmap-alias-mip-range-pixel-validation.md)
- [EXP-0097 second-package LightMap replication](EXP-0097-lightmap-alias-second-package-validation.md)
- [EXP-0098 ShadowMap structural audit and UModel class gap](EXP-0098-shadowmap-uelib-mip-census-umodel-gap.md)
- [Mip census helper](../tools/uelib_texture_mip_census.ps1)
- [All-mip audit helper](../tools/audit_uelib_texture_mips.py)
- [Byte-to-pixel comparison helper](../tools/compare_uelib_mip_data_to_umodel_tga.py)
