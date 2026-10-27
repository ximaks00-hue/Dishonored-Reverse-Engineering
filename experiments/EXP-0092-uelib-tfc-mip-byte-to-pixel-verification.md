---
id: EXP-0092
title: Verify one UELib TFC mip range against UModel texture pixels
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do UELib-reported TFC and inline mip ranges for one texture decode to the exact pixels UModel exports with and without the TFC?"
---

# EXP-0092 — Verify one UELib TFC mip range against UModel texture pixels

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: exact-manifest `Abbey_01_Keys_SF.upk`, 38,530 bytes, SHA-256 `D54098F22E7A72B03A9EF91B2B3892B521E065C23026BC101D5A0A5E11298C74`; exact-manifest `Textures.tfc`, 1,209,025,724 bytes, SHA-256 `111AEEF2932BC9679C3262A9D0077BED79784B919AFF04151CED5849BCE62C74`; export index 13, `Texture2D'Keys.key_set_01_d'`.
- Tools: Eliot.UELib 1.13.3 API via [mip census helper](../tools/uelib_texture_mip_census.ps1); UE package decompressor SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`; pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; [byte-to-pixel verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py), Python 3 and `lzokay==1.1.7`.
- Durable data: [per-mip metadata/range table](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_d.csv), [metadata summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_d.json), and [pixel verification summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-Abbey_01_Keys_SF-key_set_01_d.json). Decompressed UPK, raw TFC blocks' derived data, TGA outputs, and logs remain under ignored `assets/extracted/tfc-reference-probe-abbey-keys/`.
- Exclusions: this verifies one exact object and two parser-output paths, not the game's runtime renderer, global TFC directory format, cache GUID semantics, or all texture formats. No source game package/TFC was modified and no game process was launched. `_excluded_coop_project/` was not accessed.

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; verify the EXE hash and source package/TFC identities.
2. Decompress a copy of the exact UPK to ignored storage. The UModel decompressor reports an uncompressed package size of 67,151 bytes.
3. Load the decompressed package through UELib 1.13.3, call `InitializePackage()` and explicitly `Load()` export index 13. Record export serial bounds, the `TextureFileCacheName`, the native `TextureFileCacheGuid` components, and every `MipMap2D.Data` bulk-data flags/size/offset/element count.
4. Check the package serial offsets and external TFC offset against file bounds; hash each stored mip range. In the original probe, bounded candidate skips into the mip 0 range found a 24-byte prefix after which `lzokay` yielded exactly UELib's `ElementCount`. The verifier has since been extended in EXP-0094 to validate the observed LZO chunk table and exact aggregate range for the relevant block layout. Do not assign undocumented semantics to header fields.
5. Decode the resulting DXT1 mip bytes and each UModel type-10 RLE TGA to top-left RGB pixels; compare every pixel. The two TGAs come from EXP-0091's TFC-present and no-TFC isolated search paths.

Reproduce metadata extraction from repository root:

```powershell
tools\ue-package-decompressor\decompress.exe -game=dis `
  -path="Dishonored RHCP\DishonoredGame\CookedPCConsole" `
  -out="assets\extracted\tfc-reference-probe-abbey-keys\decompressed-confirmed" `
  Abbey_01_Keys_SF.upk

& tools\uelib_texture_mip_census.ps1 `
  -PackagePath "assets\extracted\tfc-reference-probe-abbey-keys\decompressed-confirmed\Abbey_01_Keys_SF.upk" `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Textures.tfc" `
  -PackageIndex 13 `
  -UelibAssemblyPath ".nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll" `
  -OutputCsv "research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_d.csv" `
  -SummaryJson "research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_d.json"
```

Reproduce byte-to-pixel checks with the updated verifier (install the pinned optional dependency if absent). It recognizes the one-chunk LZO table while retaining the legacy `--mip1-tga` alias; `--inline-fallback-tga` denotes the first inline mip, not necessarily mip index 1:

```powershell
python -m pip install -r requirements-texture-validation.txt
python tools\compare_uelib_mip_data_to_umodel_tga.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_d.csv `
  --package assets\extracted\tfc-reference-probe-abbey-keys\decompressed-confirmed\Abbey_01_Keys_SF.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Textures.tfc" `
  --mip0-tga assets\extracted\tfc-reference-probe-abbey-keys\capture-with-tfc\Abbey_01_Keys_SF\Texture2D\key_set_01_d.tga `
  --inline-fallback-tga assets\extracted\tfc-reference-probe-abbey-keys\capture-without-tfc\Abbey_01_Keys_SF\Texture2D\key_set_01_d.tga `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-pixel-verification-Abbey_01_Keys_SF-key_set_01_d.json
```

## Observations

- UELib reports `TextureFileCacheName="Textures"`, `TextureFileCacheGuid` numeric components `A=613208755`, `B=1221585566`, `C=2565591207`, `D=2050680652`, and export serial range `[44074, 55518)` in the decompressed package.
- UELib reports nine DXT1 mips. Mip 0 is 256×256, `StoreInSeparateFile, CompressedLZO`, `StorageOffset=52,448,051`, `StorageSize=22,239`, `ElementCount=32,768`; that TFC range lies within the 1,209,025,724-byte file. Mips 1–8 are inline; all eight `StorageOffset/StorageSize` ranges lie within the export serial range. Mip 1 is 128×128, 8,192 raw bytes at package offset 44,386.
- The external mip 0 byte range has SHA-256 `930A8C9CF5E13BABBFFDC3A2FBFCE711537813B3D7D4901AB1AAA0FD9BEB26AD`. A 24-byte prefix skip is the smallest tested prefix for which `lzokay` yields exactly the declared 32,768 output bytes. The prefix/header bytes are not assigned field semantics in this experiment.
- DXT1 decoding of the mip 0 output is pixel-identical to the UModel TFC-present TGA: 65,536/65,536 RGB pixels exact, mean absolute channel error 0, maximum channel error 0.
- DXT1 decoding of the inline mip 1 is pixel-identical to the UModel no-TFC fallback TGA: 16,384/16,384 RGB pixels exact, mean absolute channel error 0, maximum channel error 0.
- UModel's TFC-present log says it reads mip level 0 at 256×256 from `Textures.tfc`; its isolated no-TFC log reports the named cache missing and its output is 128×128. The inline mip 1 comparison identifies that fallback image's source bytes for this sample.

## Interpretation and claim limits

- **Confirmed for this object and these parser outputs:** the UELib-reported TFC range, after LZO decompression and DXT1 decoding, reproduces the exact RGB pixels UModel exports when the cache is available. The UELib-reported inline mip 1 reproduces the exact lower-resolution TGA UModel exports when the cache is absent.
- **Observed:** all mip ranges are in their expected file bounds; inline mips are contained by the export serial range, while mip 0 is in the named TFC. The UModel presence/fallback logs agree with the resulting mip dimensions.
- **Unknown:** semantics of the 24-byte TFC prefix, whether/how the stored GUID participates in cache lookup, game-runtime behavior, and generality across other texture classes, TFC files, and compression variants.
- **Limit:** one Texture2D, one UPK, one TFC, pinned UModel and UELib. This is not a general TFC indexer or runtime rendering proof.

## Links

- [EXP-0090 cache-name corpus joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [EXP-0091 UModel TFC-present/missing behavior](EXP-0091-umodel-texture-tfc-presence-probe.md)
- [Mip census helper](../tools/uelib_texture_mip_census.ps1)
- [DXT1/TGA verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py)
