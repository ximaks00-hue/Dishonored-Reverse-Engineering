---
id: EXP-0104
title: Audit TextureFlipBook mip ranges and record UModel support gap
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can UELib's TextureFlipBook implementation expose bounded, format-consistent mips, and does UModel export the same class?"
---

# EXP-0104 — Audit TextureFlipBook mip ranges and record UModel support gap

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `L_ArtDealer_Block.upk`, 7,459,099 bytes, SHA-256 `90485964E570B7E1E71B056585FF393DB8C464ED54A86A018B4738C65837049D`; `Textures.tfc`, 1,209,025,724 bytes, SHA-256 `111AEEF2932BC9679C3262A9D0077BED79784B919AFF04151CED5849BCE62C74`. Decompressed UPK hash appears in the census summary.
- Object: `TextureFlipBook'L_ArtDealer_Block.Txr_FireFlipBook'`, UELib package index 3779, UModel zero-based export ordinal 3778.
- Tools: UELib 1.13.3, mip census helper, all-mip DXT1 audit helper, and pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.
- Durable outputs: [mip census CSV](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-Txr_FireFlipBook.csv), [census JSON with serialized properties](../research/builds/BUILD-STEAM-10256413/tfc-mip-probe-L_ArtDealer_Block-Txr_FireFlipBook.json), and [all-mip audit](../research/builds/BUILD-STEAM-10256413/tfc-mip-audit-artdealer-fireflipbook.json). UModel logs are in ignored `assets/extracted/tfc-flipbook-artdealer/`.
- Limits: one object/package, one TFC, and structural UELib parsing. UModel rejects the class before reading the cache or writing an image; no byte-to-pixel comparison or flipbook playback/runtime behavior is established.

## Procedure

1. Verify package and TFC hashes against the build manifest.
2. Run UELib census on object index 3779 with the native class registry (no alias).
3. Validate all external/inline ranges and DXT1 mip sizes.
4. Attempt UModel export with the full cooked resource path and with an isolated package-only path; capture whether the class is supported.

```powershell
& tools\uelib_texture_mip_census.ps1 `
  -PackagePath assets\extracted\tfc-lightmap-artdealer\decompressed\L_ArtDealer_Block.upk `
  -TextureFileCachePath "Dishonored RHCP\DishonoredGame\CookedPCConsole\Textures.tfc" `
  -PackageIndex 3779 `
  -UelibAssemblyPath .nuget\packages\eliot.uelib\1.13.3\lib\netstandard2.0\Eliot.UELib.dll `
  -OutputCsv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-Txr_FireFlipBook.csv `
  -SummaryJson research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-Txr_FireFlipBook.json

python tools\audit_uelib_texture_mips.py `
  --mip-census-csv research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-Txr_FireFlipBook.csv `
  --package assets\extracted\tfc-lightmap-artdealer\decompressed\L_ArtDealer_Block.upk `
  --tfc "Dishonored RHCP\DishonoredGame\CookedPCConsole\Textures.tfc" `
  --output-json research\builds\BUILD-STEAM-10256413\tfc-mip-audit-artdealer-fireflipbook.json

third_party\ueviewer-gildor\umodel.exe -export -game=dis `
  -path="Dishonored RHCP\DishonoredGame\CookedPCConsole" `
  -out=assets\extracted\tfc-flipbook-artdealer\with-cache `
  L_ArtDealer_Block.upk Txr_FireFlipBook
```

The second UModel invocation used the isolated `no-cache-input` directory and is recorded with the corresponding log. Both executions report the same unsupported class.

## Observations

- UELib instantiates the export as `UELib.Engine.UTextureFlipBook`, reports serialized dimensions 2048×2048 and `EPixelFormat.PF_DXT1`, and exposes 12 mips: four external and eight inline.
- The serialized property list includes `HorizontalImages=4`, `VerticalImages=4`, `FrameRate=32.0000000`, `FrameTime=0.0312500`, `OriginalSizeX=2048`, `OriginalSizeY=2048`, `MipTailBaseIdx=11`, and `FirstResourceMemMip=4`. The frame-rate/time values are reciprocal numerically; this arithmetic does not identify the runtime frame-selection rule.
- Every external range lies within `Textures.tfc`; every inline range lies inside export serial interval `[12,901,164, 12,912,872)`. The all-mip audit decompresses the LZO ranges and DXT1-decodes all 12 payloads to the reported dimensions.
- With the full resource directory and with package-only input, UModel logs `Unknown class "TextureFlipBook" for object "Txr_FireFlipBook"` and reports no supported objects for the requested export. Neither run writes a TGA.

## Interpretation and claim limits

- **Observed:** UELib's native TextureFlipBook implementation exposes a 12-level PF_DXT1 mip chain whose ranges and decoded sizes pass the audit, together with the serialized properties listed above.
- **Observed:** the tested UModel build rejects this class before TFC selection/export in both search-path conditions.
- **Unknown:** independent correctness of the mip offsets/pixels, whether the horizontal/vertical and rate/time fields correspond directly to runtime frame layout/playback, and behavior of other TextureFlipBook assets.
- **Claim status: mixed.** Structural UELib evidence is positive; the planned independent export check is unavailable due to the observed UModel class gap.

## Links

- [Texture/TFC class census](../research/builds/BUILD-STEAM-10256413/uelib-texture-tfc-references.csv)
- [MIP census helper](../tools/uelib_texture_mip_census.ps1)
- [All-mip DXT1 audit helper](../tools/audit_uelib_texture_mips.py)
- [EXP-0101 DLC LightMap validation](EXP-0101-lightmap-dlc05-cross-cache-pixel-validation.md)
- [EXP-0103 second ShadowMap sample](EXP-0103-shadowmap-second-package-g8-replication.md)
