---
id: EXP-0101
title: Validate LightMap alias against the DLC05 TFC cache
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the explicit LightMap parser alias recover and pixel-match a DLC05 object's external and inline mips from Lighting_DLC05.tfc?"
---

# EXP-0101 — Validate LightMap alias against the DLC05 TFC cache

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `DLC05/L_DLC05_Arena_Env.upk`, 10,402,253 bytes, SHA-256 `222DB9812B1C7F4389BFCBD7F93A4BAC908EF45162B6B8B92A5AA9CACB3554CA`; `DLC05/Lighting_DLC05.tfc`, 73,883,321 bytes, SHA-256 `87F375E758B244FBF55589CA8112201FB8B2FE666D8209721BC30E8F667FACC5`. The decompressed UPK used by UELib has SHA-256 `9DE6319F0BA03073C903ACA154A6A5EABB9092C87DE92B90B86E3AAF29D8E04F`.
- Object: `LightMapTexture2D'L_DLC05_Arena_Env.DirectionalMaxComponent0_1'`, UELib package index 77, UModel zero-based export ordinal 76. UModel reports a 1024×1024 external mip read from `Lighting_DLC05.tfc`.
- Tools: UELib 1.13.3, pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, package decompressor SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`, and the mip census, all-mip audit, and pixel comparison scripts.
- Durable outputs: [mip census](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_DLC05_Arena_Env-DirectionalMaxComponent0_10-lightmap.csv), [census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_DLC05_Arena_Env-DirectionalMaxComponent0_10-lightmap.json), [all-mip audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-dlc05-lightmap.json), and [pixel comparison](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-L_DLC05_Arena_Env-DirectionalMaxComponent0_1-lightmap.json). UModel logs and images are under ignored `assets/extracted/tfc-lightmap-dlc05/`.
- Limits: one DLC05 LightMap and one DLC cache; same parser alias and UModel version. The alias emits trailing data. This does not establish all DLC layouts, TFC index semantics, or game-runtime selection/rendering.

## Procedure

1. Verify the EXE, DLC package, and DLC TFC hashes against the exact build record/manifest.
2. Decompress a separate copy under ignored storage and census object index 77 with the LightMap-to-UShadowMap alias registered before initialization.
3. Audit all reported mip ranges and DXT1 decompression sizes.
4. Export the object from the DLC05 cooked directory with UModel, then repeat with the package alone and no TFC present.
5. Compare external mip 0 and first inline mip 3 against the matching UModel TGAs.

```powershell
$outDir = 'assets/extracted/tfc-lightmap-dlc05'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
tools/ue-package-decompressor/decompress.exe -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\DLC\PCConsole\DLC05' `
  "-out=$((Resolve-Path $outDir).Path)" L_DLC05_Arena_Env.upk

& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-lightmap-dlc05\L_DLC05_Arena_Env.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\DLC\PCConsole\DLC05\Lighting_DLC05.tfc" `
  -PackageIndex 77 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_DLC05_Arena_Env-DirectionalMaxComponent0_10-lightmap.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_DLC05_Arena_Env-DirectionalMaxComponent0_10-lightmap.json `
  -ClassAliasName LightMapTexture2D `
  -ClassAliasImplementationType UELib.Engine.UShadowMapTexture2D

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_DLC05_Arena_Env-DirectionalMaxComponent0_10-lightmap.csv `
  --package assets\extracted\tfc-lightmap-dlc05\L_DLC05_Arena_Env.upk `
  --tfc "Dishonored RHCP\DishonoredGame\DLC\PCConsole\DLC05\Lighting_DLC05.tfc" `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-dlc05-lightmap.json
```

The UModel command pattern and byte-to-pixel comparison are documented in EXP-0095; the exact runs are preserved in the ignored output tree.

## Observations

- The alias census reports 11 mips: three external and eight inline. All ranges fall within the TFC/package boundaries; inline ranges fall within export serial interval `[1,036,815, 1,048,255)`. The all-mip audit decompresses and DXT1-decodes all 11 payloads to the reported dimensions.
- External mip 0 is 1024×1024 at TFC offset 3,282,055, stored as a four-chunk LZO block whose chunks each decode to 131,072 bytes. External mips 1 and 2 are at offsets 3,211,969 and 3,192,394. Inline mip 3 is 128×128 at package offset 1,037,119.
- UModel logs `Reading DirectionalMaxComponent0_1 mip level 0 (1024x1024) from Lighting_DLC05.tfc` in the full DLC path run. In the package-only run it logs `TFC file "Lighting_DLC05" is missing` and exports the 128×128 fallback.
- Decoded external mip 0 matches 1,048,576/1,048,576 RGB pixels in the with-cache TGA. Inline mip 3 matches 16,384/16,384 pixels in the fallback. Both have zero mean and maximum channel error.

## Interpretation and claim limits

- **Confirmed for this object and these parser/export outputs:** alias-reported external mip 0 and inline mip 3 reproduce UModel pixels exactly; every reported mip passes range and DXT1 length/decompression checks.
- **Observed:** UModel selects a separately named DLC05 TFC and uses a lower-resolution inline fallback when the TFC is absent from its search path.
- **Inferred, sample-scoped:** UELib's aliased mip parser is structurally compatible with this DLC05 sample. The trailing-data diagnostic remains; native class-layout identity is not established.
- **Unknown:** other DLC package/cache variations, TFC GUID/index semantics, and engine-runtime use.

## Links

- [EXP-0099 non-square LightMap in a third package](EXP-0099-lightmap-third-package-mip-pixel-validation.md)
- [EXP-0100 LightMap tail/GUID byte audit](EXP-0100-lightmap-trailing-guid-byte-audit.md)
- [Mip census helper](../tools/uelib_texture_mip_census.ps1)
- [All-mip audit helper](../tools/audit_uelib_texture_mips.py)
- [Pixel comparison helper](../tools/compare_uelib_mip_data_to_umodel_tga.py)
