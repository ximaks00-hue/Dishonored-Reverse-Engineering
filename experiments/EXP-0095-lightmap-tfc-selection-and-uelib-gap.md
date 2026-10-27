---
id: EXP-0095
title: Probe LightMapTexture2D cache selection and UELib native payload gap
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does UModel select Lighting.tfc for LightMapTexture2D objects, and can UELib expose the mip ranges needed for byte-level validation?"
---

# EXP-0095 — Probe LightMapTexture2D cache selection and UELib native payload gap

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `Dishonored_MainMenu.upk`, 3,518,959 bytes, SHA-256 `452BD81AC649F611331B312A222557BEF446430C24C30D08A144E015E3769297`; `Dishonored_MainMenu_Env.upk`, 16,252,497 bytes, SHA-256 `C47769160A26F1986D2077D9C2F8F51A64A0AD695577D4546610EC0A1B79A788`; `Lighting.tfc`, 548,298,402 bytes, SHA-256 `A30146AE7EDB1AF9973CDE5D70368D2AB23A811A2B737CDCD7A3B0637A0D70C1`. Identities match the build manifest.
- Tools: pinned UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, UELib 1.13.3 package load, and the local RLE-TGA structural decoder. All outputs/logs are under ignored `assets/extracted/tfc-lightmap-probe/` and `assets/extracted/tfc-lightmap-probe-large/`.
- Scope: inspect two `LightMapTexture2D` objects in two packages under with-cache and package-only search paths. The large object's mip ranges were not recovered, so this does not validate external cache bytes or pixels against UELib offsets.
- Exclusions: no game process was launched and no source package/TFC was modified. `_excluded_coop_project/` was not accessed.

## Procedure

1. Re-read AGENTS.md, research status, Blink activation graph, and the exact build record; verify the executable hash and match all input file identities to the manifest.
2. Use UELib's all-install property output to locate `LightMapTexture2D` objects with `TextureFileCacheName="Lighting"`. Load each sample with UELib 1.13.3 and record class, dimensions, format, package index, export serial range, parser type, and trailing-data diagnostics.
3. Run UModel `-dump` on the small control and confirm its public properties. Export the identical small object with the full cooked directory and an isolated one-package directory; compare logs, TGA dimensions, and hashes.
4. For the large sample, export with `Lighting.tfc` available and then absent from the isolated package search path. Record any explicit mip-read/missing-cache lines and validate both TGA RLE streams against their declared dimensions.
5. Keep UModel's resource-selection observation separate from byte-offset/pixel validation. UELib returns `UnknownObject` for this native subclass and does not expose its mip array; do not reconstruct offsets from the UModel log.

Reproduce UModel export conditions from the repository root:

```powershell
$probe = "assets/extracted/tfc-lightmap-probe-large"
New-Item -ItemType Directory -Force -Path "$probe/with-cache", "$probe/no-cache-input", "$probe/no-cache" | Out-Null
Copy-Item "Dishonored RHCP/DishonoredGame/CookedPCConsole/Dishonored_MainMenu_Env.upk" `
  "$probe/no-cache-input/Dishonored_MainMenu_Env.upk"

third_party/ueviewer-gildor/umodel.exe -export -game=dis `
  -path="Dishonored RHCP/DishonoredGame/CookedPCConsole" `
  -out="$probe/with-cache" Dishonored_MainMenu_Env.upk DirectionalMaxComponent0_3
third_party/ueviewer-gildor/umodel.exe -export -game=dis `
  -path="$probe/no-cache-input" -out="$probe/no-cache" `
  Dishonored_MainMenu_Env.upk DirectionalMaxComponent0_3
```

## Observations

- Small control: `LightMapTexture2D'Dishonored_MainMenu.DirectionalMaxComponent0_289'`, UELib package index 209; UModel lists exports with zero-based ordinal 208. UModel `-dump` reports 32×32, `PF_DXT1`, `TextureFileCacheName=Lighting`, and `MipTailBaseIdx=5`. In both the normal cooked path and package-only path, UModel exported a 32×32, 2,024-byte TGA with SHA-256 `39D43D97FCB5F2BC15413542C24AD818A23AA2EEB1EBF5DAD4F2B66F11A08ABC`. Neither log reported reading a mip from `Lighting.tfc` or a missing-cache warning.
- Large object: `LightMapTexture2D'Dishonored_MainMenu_Env.DirectionalMaxComponent0_3'`, UELib package index 228; UModel zero-based ordinal 227. UELib property rows report `SizeX=1024`, `SizeY=1024`, `Format=PF_DXT1`, `TextureFileCacheName="Lighting"`, `MipTailBaseIdx=10`, and `FirstResourceMemMip=3`. Its UELib export serial range is `[3,047,493, 3,058,933)` in the decompressed package.
- UELib instantiates the large object as `UELib.Core.UnknownObject`, reports trailing data for that export, and exposes no `Mips` collection or TFC storage offset through the current census API.
- With the TFC available, UModel logged `Reading DirectionalMaxComponent0_3 mip level 0 (1024x1024) from Lighting.tfc` and wrote a 600,671-byte TGA, SHA-256 `F6673332A19B76C0B36B7024966A01B2224A71FCF2F4EFB2620FB8BE1B31026A`.
- With only the identical package available, UModel logged `TFC file "Lighting" is missing` and wrote a 16,354-byte TGA at 128×128, SHA-256 `818C4EDC47DF45EDF6B28BE49C9AF46A81E5FE145A7AD2F7E18C986EEE7B8D57`. Both RLE streams account for the declared pixels and consume their complete payloads.
- The two LightMap objects show that a cache-name property alone does not establish that a particular export reads the cache: the small control produced identical 32×32 output and no cache-read line, while the large object produced an explicit external mip read and lower-resolution missing-cache fallback.

## Interpretation and claim limits

- **Observed for the selected UModel build:** it reads a mip from `Lighting.tfc` for the 1024×1024 LightMap sample and falls back to a 128×128 export when that cache is missing. This extends cache-selection evidence to `LightMapTexture2D`.
- **Observed for the small control:** although it has the same cache-name property, its output remains identical with and without the cache file and UModel reports no cache lookup. The property is therefore not sufficient evidence that a given object requires external cache data.
- **Unknown:** the large LightMap's UELib-readable mip index/offset, byte-to-pixel identity, exact reason the small object does not access the TFC, `Lighting.tfc` internal indexing, and in-game renderer behavior.
- **Limit:** two objects in two packages, one UModel build and one TFC. No claim is made that UELib parsed the LightMap native payload or that UModel output equals runtime pixels.

## Links

- [EXP-0090 all-install cache-name joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [EXP-0094 chunked LZO byte-to-pixel verification](EXP-0094-cross-cache-chunked-lzo-mip-pixel-verification.md)
- [EXP-0096 follow-up with explicit UELib parser alias](EXP-0096-lightmap-alias-mip-range-pixel-validation.md)

## Follow-up

The UELib native mip gap recorded above was the state of this initial probe. EXP-0096 registers an explicit in-memory alias from `LightMapTexture2D` to the existing `UShadowMapTexture2D` parser; its mip ranges pass file-bound checks and selected external/inline mip data match UModel pixels. EXP-0097 repeats that check for a second large LightMap in another package. The default parser still returns `UnknownObject`, and both alias runs leave trailing-data diagnostics, so compatibility claims remain sample-scoped.
- [Build file manifest](../research/builds/BUILD-STEAM-10256413/files.csv)
