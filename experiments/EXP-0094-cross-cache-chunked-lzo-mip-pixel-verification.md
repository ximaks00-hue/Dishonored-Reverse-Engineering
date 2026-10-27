---
id: EXP-0094
title: Verify a CharTextures chunked LZO mip against UModel pixels
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can a UELib mip in another TFC be reconstructed from its chunked LZO byte range and matched to UModel output?"
---

# EXP-0094 — Verify a CharTextures chunked LZO mip against UModel pixels

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `Dishonored_MainMenu_Env.upk`, manifest size 16,252,497 bytes and SHA-256 `C47769160A26F1986D2077D9C2F8F51A64A0AD695577D4546610EC0A1B79A788`; `CharTextures.tfc`, 301,325,850 bytes and SHA-256 `DC44903278ECFF2E3735DF828F550FAD5D9A5871370EEB5A5D4D1CEF040E9D7B`. Both source identities match the build manifest.
- Object: UELib package index 5819, `Texture2D'dead_wap_body_01_d'`; UModel `-list` uses zero-based export ordinals, corresponding ordinal 5818. UELib property is `TextureFileCacheName="CharTextures"`; serialized `Format` property is `PF_DXT1`.
- Tools: UELib 1.13.3 census helper; pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; updated [byte-to-pixel verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py), Python 3 and `lzokay==1.1.7`.
- Durable outputs: [mip range table](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu_Env-dead_wap_body_01_d.csv), [census summary](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-Dishonored_MainMenu_Env-dead_wap_body_01_d.json), and [pixel verification report](../research/builds/BUILD-STEAM-10256413/tfc-mip-pixel-verification-Dishonored_MainMenu_Env-dead_wap_body_01_d.json). Decompressed package, TGA outputs, and logs remain under ignored `assets/extracted/tfc-cross-cache-mainmenu/`.
- Limits: one Texture2D and one cache file, using the same UModel/UELib and DXT1 format as the prior sample but a different TFC and multi-chunk external mip. No game runtime or broad TFC parser is verified. Source game files were read-only; the game was not launched.

## Procedure

1. Re-read repository instructions, status, Blink graph, build record, and current EXE hash; verify source UPK/TFC identities against the build manifest.
2. Decompress a copy of the exact UPK to ignored storage. UModel reports 6,389 exports; UELib's positive package index 5819 refers to `dead_wap_body_01_d`, while UModel lists this same export at ordinal 5818.
3. Use UELib to load that object, record its cache name, format, export serial range, GUID and all mip ranges; check each range against its containing file and inline ranges against the export serial range.
4. Export the object with the full CookedPCConsole path containing `CharTextures.tfc`, then export it with an isolated directory containing only the identical UPK. UModel logs the external mip read in the first run and missing cache in the second.
5. The verifier reads mip 0's exact TFC range. It validates the observed little-endian tag, declared aggregate sizes, per-chunk size table, and exact stored-range boundary; it decompresses each chunk to its declared length and concatenates them. It does not assign meanings to header words beyond these checks. It DXT1-decodes mip 0 and the first inline mip and compares both images to UModel's with-cache and fallback TGAs.

Reproduce metadata extraction and byte-to-pixel verification from the repository root:

```powershell
tools\ue-package-decompressor\decompress.exe -game=dis `
  -path="Dishonored RHCP\DishonoredGame\CookedPCConsole" `
  -out="assets\extracted\tfc-cross-cache-mainmenu\decompressed" `
  Dishonored_MainMenu_Env.upk

New-Item -ItemType Directory -Force -Path `
  assets\extracted\tfc-cross-cache-mainmenu\with-cache, `
  assets\extracted\tfc-cross-cache-mainmenu\no-cache-input, `
  assets\extracted\tfc-cross-cache-mainmenu\no-cache | Out-Null
Copy-Item "Dishonored RHCP\DishonoredGame\CookedPCConsole\Dishonored_MainMenu_Env.upk" `
  assets\extracted\tfc-cross-cache-mainmenu\no-cache-input\Dishonored_MainMenu_Env.upk

third_party\ueviewer-gildor\umodel.exe -export -game=dis `
  -path="Dishonored RHCP\DishonoredGame\CookedPCConsole" `
  -out=assets\extracted\tfc-cross-cache-mainmenu\with-cache `
  Dishonored_MainMenu_Env.upk dead_wap_body_01_d
third_party\ueviewer-gildor\umodel.exe -export -game=dis `
  -path=assets\extracted\tfc-cross-cache-mainmenu\no-cache-input `
  -out=assets\extracted\tfc-cross-cache-mainmenu\no-cache `
  Dishonored_MainMenu_Env.upk dead_wap_body_01_d

& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-cross-cache-mainmenu\decompressed\Dishonored_MainMenu_Env.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\CharTextures.tfc" `
  -PackageIndex 5819 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-dead_wap_body_01_d.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-dead_wap_body_01_d.json

python tools\compare_uelib_mip_data_to_umodel_tga.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-dead_wap_body_01_d.csv `
  --package assets\extracted\tfc-cross-cache-mainmenu\decompressed\Dishonored_MainMenu_Env.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\CharTextures.tfc" `
  --mip0-tga assets\extracted\tfc-cross-cache-mainmenu\with-cache\Dishonored_MainMenu_Env\Texture2D\dead_wap_body_01_d.tga `
  --inline-fallback-tga assets\extracted\tfc-cross-cache-mainmenu\no-cache\Dishonored_MainMenu_Env\Texture2D\dead_wap_body_01_d.tga `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-pixel-verification-Dishonored_MainMenu_Env-dead_wap_body_01_d.json
```

## Observations

- UELib reports 11 DXT1 mips. Mip 0 is 512×1024, external, LZO-compressed; its TFC byte range starts at 264,164,359 and contains 226,462 bytes. Mip 1 is also external (256×512, 58,792 bytes at 264,105,567). Mips 2–10 are inline; all inline ranges are within export serial range `[20,530,719, 20,553,179)`.
- Mip 0 block begins with little-endian 32-bit value `0x9E2A83C1`. The following observed size fields are consistent with aggregate compressed and uncompressed lengths of 226,430 and 262,144 bytes. Two following compressed/uncompressed size pairs sum exactly to those totals: `(119,692, 131,072)` and `(106,738, 131,072)`. The table plus compressed payload is exactly the UELib-reported 226,462-byte range. Each LZO chunk independently decompresses to its declared size; concatenated bytes total 262,144. No undocumented meanings are assigned to other header fields.
- UModel with `CharTextures.tfc` logged mip 0 at 512×1024 and exported a 977,321-byte TGA. UModel without the named TFC logged it missing and exported 128×256, matching the first inline mip (mip 2), since mip 1 is also external.
- DXT1-decoded external mip 0 matches the TFC-present UModel TGA exactly: 524,288/524,288 RGB pixels, mean absolute channel error 0, max error 0.
- DXT1-decoded inline mip 2 matches the no-TFC UModel TGA exactly: 32,768/32,768 RGB pixels, mean absolute channel error 0, max error 0.

## Interpretation and claim limits

- **Confirmed for this object and pinned parser outputs:** the UELib-reported external range can be split by the validated chunk size table, decompressed to the declared aggregate byte count, and DXT1-decoded to the exact UModel TFC-present pixels. The first inline mip likewise reproduces the no-TFC fallback pixels.
- **Observed:** this second TFC path uses a two-chunk compressed external mip; another external mip follows it, and UModel falls back to inline mip 2 when the named cache is absent.
- **Unknown:** semantic interpretation of every fixed-header field, GUID participation in cache lookup, behavior in the game runtime, and generality to other resource classes/formats/compression arrangements.
- **Scope limit:** one object, one package, one alternate TFC, one DXT1 texture format, and one pinned UModel build. EXP-0092/0093 cover a different TFC with one-chunk external blocks. These are three object samples across two TFCs, not corpus-wide confirmation.

## Links

- [EXP-0092 first TFC pixel verification](EXP-0092-uelib-tfc-mip-byte-to-pixel-verification.md)
- [EXP-0093 second object in Textures.tfc](EXP-0093-second-texture-tfc-mip-pixel-verification.md)
- [EXP-0090 cache-name corpus joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [Updated DXT1/TGA verifier](../tools/compare_uelib_mip_data_to_umodel_tga.py)
