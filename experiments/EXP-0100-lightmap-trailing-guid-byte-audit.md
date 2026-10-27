---
id: EXP-0100
title: Audit the repeated trailing bytes after aliased LightMap mip chains
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do LightMap alias samples share a bounded post-mip region, and does that region contain the GUID reported by the mip census?"
---

# EXP-0100 — Audit the repeated trailing bytes after aliased LightMap mip chains

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: five prior explicit LightMap alias census summaries and their exact decompressed UPK copies. Their source-package/TFC identities are individually recorded in EXP-0096/0097/0099 and the corresponding census JSON files.
- Objects: five `LightMapTexture2D` objects from `Dishonored_MainMenu.upk`, `Dishonored_MainMenu_Env.upk`, `L_ArtDealer_Block.upk`, `L_ArtDealer_P.upk`, and `L_Boyle_Ext_Env.upk`.
- Tools: census summary CSV/JSON files, Python 3, and [trailing GUID audit helper](../tools/audit_lightmap_trailing_guid.py).
- Durable output: [five-object trailing-byte audit](../research/builds/BUILD-STEAM-10256413/lightmap-trailing-guid-audit.json).
- Limits: this is a byte-structure check on five objects already parsed through the LightMap-to-UShadowMap alias. It does not identify the meaning of the other words, validate a native class layout, or establish runtime behavior.

## Procedure

1. Read the object export serial end and all inline mip end offsets from each existing census summary/CSV.
2. Extract the bounded bytes between the last inline mip end and export serial end.
3. Parse the four little-endian 32-bit words at tail offset +8 and compare them to the four GUID components reported in that object's census summary.
4. Record the bytes and exact comparison results without assigning semantics to other words.

```powershell
python tools\audit_lightmap_trailing_guid.py `
  research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu-DirectionalMaxComponent0_289-lightmap.json `
  research\builds\BUILD-STEAM-10256413\tfc-mip-probe-Dishonored_MainMenu_Env-DirectionalMaxComponent0_3-lightmap.json `
  research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_Block-DirectionalMaxComponent0_1-lightmap.json `
  research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_ArtDealer_P-DirectionalMaxComponent0_12-lightmap.json `
  research\builds\BUILD-STEAM-10256413\tfc-mip-probe-L_Boyle_Ext_Env-DirectionalMaxComponent0_10-lightmap.json `
  --output-json research\builds\BUILD-STEAM-10256413\lightmap-trailing-guid-audit.json
```

## Observations

- In all five samples, the final inline mip end is exactly 32 bytes before the export serial end.
- In every 32-byte region, the first two little-endian 32-bit words are `(4, 4)`, and the last two are `(0, 1)`.
- The four little-endian words at byte offset +8 match the census `TextureFileCacheGuid` components `(A, B, C, D)` in all five cases.
- All five decompressed package hashes match their corresponding census summary hashes; the helper refuses to audit a mismatching copy.
- The repeated layout also occurs in the 32×32 inline-only control in `Dishonored_MainMenu.upk`; thus it is not limited to objects with external mip ranges.

## Interpretation and claim limits

- **Confirmed for these five serialized samples:** the post-mip region is 32 bytes; bytes +8 through +23 decode to four little-endian words equal to the census GUID components, with the same `(4,4)` prefix words and `(0,1)` suffix words.
- **Observed:** UELib reports trailing data on the LightMap alias parses; this audit locates and characterizes a repeated 32-byte region after the final inline mip.
- **Unknown:** the semantic types/roles of prefix and suffix words, whether this is the complete explanation for UELib's diagnostic, how other serialized class variants differ, and whether runtime uses these values as observed.
- **Claim status: mixed.** Byte offsets and GUID equality are directly checked. Interpretation of the remaining bytes and parser/runtime semantics remains unknown.

## Links

- [EXP-0096 first alias sample and control](EXP-0096-lightmap-alias-mip-range-pixel-validation.md)
- [EXP-0097 second-package LightMap sample](EXP-0097-lightmap-alias-second-package-validation.md)
- [EXP-0099 third-package non-square LightMap sample](EXP-0099-lightmap-third-package-mip-pixel-validation.md)
- [Audit helper](../tools/audit_lightmap_trailing_guid.py)
- [Audit output](../research/builds/BUILD-STEAM-10256413/lightmap-trailing-guid-audit.json)
