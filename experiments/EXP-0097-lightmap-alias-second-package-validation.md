---
id: EXP-0097
title: Revalidate LightMap parser alias in a second package
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the explicit LightMap-to-ShadowMap UELib parser alias recover another package's mip ranges and match UModel pixels?"
---

# EXP-0097 — Revalidate LightMap parser alias in a second package

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `L_ArtDealer_Block.upk`, 7,459,099 bytes, SHA-256 `90485964E570B7E1E71B056585FF393DB8C464ED54A86A018B4738C65837049D`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`. Both match the exact-build manifest.
- Object: `LightMapTexture2D'L_ArtDealer_Block.DirectionalMaxComponent0_1'`, UELib package index 364, UModel zero-based export ordinal 363. UELib reports 1024×1024, `PF_DXT1`, cache name `Lighting`.
- Parser method: as in EXP-0096, register `LightMapTexture2D` in memory to UELib `UELib.Engine.UShadowMapTexture2D`. The actual export class remains LightMapTexture2D. The alias emits a trailing-data diagnostic; this sample tests repeated output compatibility, not identity of native class layouts.
- Tools: UELib 1.13.3, pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, chunk-aware byte-to-pixel verifier and [all-mip audit helper](../tools/audit_uelib_texture_mips.py), Python 3, `lzokay==1.1.7`.
- Durable outputs: [mip range table](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.csv), [census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.json), [all-mip decode/range audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-artdealer_large-lightmap.json), and [UModel pixel comparison](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.json). Source copies, exports and logs remain under ignored `assets/extracted/tfc-lightmap-artdealer/`.
- Limits: one second large LightMap in another package, same Lighting TFC, same explicit parser alias, same pinned UModel. It is a targeted replication, not a corpus-wide parser validation or runtime-rendering proof.

## Procedure

1. Re-read AGENTS.md, status, Blink graph, and build record; verify EXE, UPK, and TFC source identities.
2. Decompress an exact package copy under ignored extraction storage. Use UELib's cache-name/property corpus to select `DirectionalMaxComponent0_1` (package index 364); UModel `-list` reports its zero-based ordinal 363.
3. Register the LightMap class alias before UELib package initialization and census all mip ranges. Independently verify every external/inline range and DXT1 decoded size with the all-mip audit helper.
4. Export through UModel once with the full cooked resource directory, once with only the package; compare the top external and first inline mip bytes to the corresponding 24-bit RLE TGAs.

Reproduce census and full mip audit:

```powershell
& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-lightmap-artdealer\decompressed\L_ArtDealer_Block.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  -PackageIndex 364 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.json `
  -ClassAliasName LightMapTexture2D `
  -ClassAliasImplementationType UELib.Engine.UShadowMapTexture2D

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.csv `
  --package assets\extracted\tfc-lightmap-artdealer\decompressed\L_ArtDealer_Block.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Lighting.tfc" `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-artdealer_large-lightmap.json
```

The UModel invocations and pixel verifier use the same with-cache/package-only pattern and flags recorded in EXP-0095/0096, substituting `L_ArtDealer_Block.upk` and `DirectionalMaxComponent0_1`; full command captures are retained in the ignored output tree.

## Observations

- UELib alias census reports 11 mip rows: three external, eight inline. All ranges lie within their source files and all inline ranges lie within export serial interval `[797,743, 809,183)`.
- The external mip offsets in `Lighting.tfc` are 414,080,123 (mip 0, 236,977 bytes), 414,010,991 (mip 1, 69,132 bytes), and 413,990,819 (mip 2, 20,172 bytes). First inline mip is index 3 at package offset 798,047, size 8,192.
- The all-mip audit decodes all 11 mips to the reported DXT1 dimensions. External mip 0 comprises four LZO chunks, 131,072 bytes each after decompression; mip 1 and mip 2 each use one chunk. The eight inline payloads are within the object serial range.
- With `Lighting.tfc` present UModel logs `Reading DirectionalMaxComponent0_1 mip level 0 (1024x1024) from Lighting.tfc`; its TGA is 939,015 bytes, SHA-256 `51E30DB6C18F527BEC9AAEFC0F6E93B4B3AAC8DA99EB4AFC83A5C746FB0C4A11`. Without the cache, UModel logs the missing file and exports 128×128.
- Decoded external mip 0 matches the 1024×1024 UModel TGA exactly: 1,048,576/1,048,576 RGB pixels, zero mean and maximum channel error. Decoded inline mip 3 matches the 128×128 fallback exactly: 16,384/16,384 pixels, zero mean and maximum error.

## Interpretation and claim limits

- **Confirmed for this second object and these parser outputs:** the aliased UELib mip 0 and mip 3 ranges reproduce the corresponding UModel export pixels exactly; all 11 reported ranges and DXT1 lengths pass the audit.
- **Observed:** the UModel LightMap TFC read and missing-cache fallback occur in a second package, and the UELib alias returns a compatible 11-mip layout for this sample.
- **Inferred, sample-scoped:** the UShadowMap deserializer is compatible enough with these two tested LightMap serialization samples to locate their mip records. This does not prove the native class layouts are identical; both alias runs retain a trailing-data diagnostic.
- **Unknown:** remaining LightMap variants, the semantic content of trailing bytes, other non-Texture2D classes, TFC GUID/index semantics, and game-runtime behavior.
- **Scope limit:** two large LightMaps across two packages and one TFC, plus the small inline-only control from EXP-0096. No claim of all-install coverage.

## Links

- [EXP-0096 first LightMap alias validation and inline-only control](EXP-0096-lightmap-alias-mip-range-pixel-validation.md)
- [EXP-0090 all-install cache-name joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [Census helper](../tools/uelib_texture_mip_census.ps1)
- [All-mip range/format audit](../tools/audit_uelib_texture_mips.py)
- [Byte-to-pixel verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py)
