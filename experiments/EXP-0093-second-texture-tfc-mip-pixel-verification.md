---
id: EXP-0093
title: Verify a second Texture2D TFC mip range against UModel pixels
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does a second Texture2D in the same package map its UELib external and inline mip ranges to exact UModel pixels?"
---

# EXP-0093 — Verify a second Texture2D TFC mip range against UModel pixels

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `Abbey_01_Keys_SF.upk`, 38,530 bytes, SHA-256 `D54098F22E7A72B03A9EF91B2B3892B521E065C23026BC101D5A0A5E11298C74`; `Textures.tfc`, 1,209,025,724 bytes, SHA-256 `111AEEF2932BC9679C3262A9D0077BED79784B919AFF04151CED5849BCE62C74`. Both match the build manifest.
- Object: UELib package index 14, `Texture2D'key_set_01_n'`; UModel `-list` numbers exports from zero, so the corresponding UModel list ordinal is 13. This differs from UELib's positive package object index. Cache name is `Textures`.
- Tools: UELib 1.13.3 mip census helper, pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, and the EXP-0092 byte-to-pixel verifier with `lzokay==1.1.7`.
- Durable outputs: [mip metadata and ranges](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_n.csv), [metadata summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_n.json), and [pixel verification](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-Abbey_01_Keys_SF-key_set_01_n.json). UModel outputs and logs remain under ignored `assets/extracted/tfc-reference-probe-abbey-keys/`.
- Limits: this is a second object in the same UPK, same TFC, same UModel build, and same decode formats as EXP-0092. It does not establish general TFC directory/GUID semantics or in-game runtime rendering. No game process was launched and no source game file was changed.

## Procedure

1. Re-read repository instructions, status, Blink graph, and build identity; confirm the executable and source hashes.
2. Use UModel `-list` to identify `key_set_01_n` and keep its zero-based display ordinal distinct from UELib's positive package index.
3. Copy the exact UPK to isolated ignored storage and export `key_set_01_n` once with the original `CookedPCConsole` path (which contains `Textures.tfc`) and once with only the UPK in the search path.
4. Run `uelib_texture_mip_census.ps1` on the decompressed package with package index 14; check every mip range against file bounds and inline ranges against the export serial bounds.
5. Run `compare_uelib_mip_data_to_umodel_tga.py`, which validates the observed LZO chunk table (or uses the bounded-prefix fallback for legacy payloads), then DXT1-decodes the UELib mip bytes and UModel RLE TGAs and compares RGB pixels. Its inline-fallback argument always means the first inline mip, which can be later than mip 1 when earlier mip levels are external.

Commands from the repository root (UModel captures are already generated under ignored extraction storage):

```powershell
& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-reference-probe-abbey-keys\decompressed-confirmed\Abbey_01_Keys_SF.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Textures.tfc" `
  -PackageIndex 14 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_n.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_n.json

python tools\compare_uelib_mip_data_to_umodel_tga.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Abbey_01_Keys_SF-key_set_01_n.csv `
  --package assets\extracted\tfc-reference-probe-abbey-keys\decompressed-confirmed\Abbey_01_Keys_SF.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Textures.tfc" `
  --mip0-tga assets\extracted\tfc-reference-probe-abbey-keys\second-with-tfc\Abbey_01_Keys_SF\Texture2D\key_set_01_n.tga `
  --inline-fallback-tga assets\extracted\tfc-reference-probe-abbey-keys\second-without-tfc\Abbey_01_Keys_SF\Texture2D\key_set_01_n.tga `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-pixel-verification-Abbey_01_Keys_SF-key_set_01_n.json
```

## Observations

- UELib reports nine DXT1 mips, cache name `Textures`, and cache GUID components `A=3554091322`, `B=1315413265`, `C=367512730`, `D=4065412231`. Export serial range is `[55518, 67151)` in the decompressed package.
- External mip 0 is 256×256, `StoreInSeparateFile, CompressedLZO`, 12,491 stored bytes at TFC offset 52,435,560. Its range is within `Textures.tfc`; stored-range SHA-256 is `926F9B194BE24AE487931BAFF3611359FF7B7EA47E046FB3945A280C6350DF56`. Skipping 24 leading bytes is the smallest tested prefix yielding exactly 32,768 decoded bytes. The skipped bytes' structure is unknown.
- Inline mip 1 is 128×128 and 8,192 bytes at package offset 56,019, within this export's serial range.
- With the TFC available, UModel logged that it read mip 0 from `Textures.tfc` and exported 256×256. With only the package available, it logged the TFC missing and exported 128×128.
- Decoded external mip 0 is pixel-identical to the TFC-present UModel TGA: 65,536/65,536 RGB pixels, zero mean and maximum channel error. Decoded inline mip 1 is pixel-identical to the no-TFC UModel TGA: 16,384/16,384 pixels, zero mean and maximum channel error.
- The package's other cache-bearing Texture2D, `key_set_01_d` (UELib package index 13), was verified in EXP-0092. It has a different cache GUID and TFC offset. Both samples use the same cache file and format path.

## Interpretation and claim limits

- **Confirmed for these two objects and pinned parser outputs:** the UELib-reported external byte ranges and inline mip ranges decode to the exact corresponding UModel output pixels.
- **Observed:** both objects' external ranges lie in the named TFC and their inline mip ranges lie within their package export serial bounds; UModel selects the expected dimensions with and without the TFC.
- **Unknown:** the meaning of the 24-byte prefixes, the role of GUID values in TFC lookup, whether this mapping generalizes to other TFC files/classes/formats, and game-runtime rendering behavior.
- **Scope limit:** two neighboring Texture2D exports in one package, one TFC, one UModel version, and DXT1/LZO only. This is stronger than a one-object probe, not corpus-wide coverage.

## Links

- [EXP-0092 first Texture2D pixel verification](EXP-0092-uelib-tfc-mip-byte-to-pixel-verification.md)
- [EXP-0090 cache-name corpus joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [Mip census helper](../tools/uelib_texture_mip_census.ps1)
- [Pixel verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py)
