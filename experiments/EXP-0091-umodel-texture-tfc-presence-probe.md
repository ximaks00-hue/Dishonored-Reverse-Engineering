---
id: EXP-0091
title: UModel texture export with and without the named TFC
experiment_status: done
claim_status: observed
build: "10256413"
question: "For one exact-build streamed texture, does UModel's export output change when the matching TFC is absent from its package search path?"
---

# EXP-0091 — UModel texture export with and without the named TFC

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Inputs: `DishonoredGame/CookedPCConsole/Abbey_01_Keys_SF.upk`, 38,530 bytes, SHA-256 `D54098F22E7A72B03A9EF91B2B3892B521E065C23026BC101D5A0A5E11298C74`; `Textures.tfc`, 1,209,025,724 bytes, SHA-256 `111AEEF2932BC9679C3262A9D0077BED79784B919AFF04151CED5849BCE62C74`. Both match the build manifest. Selected export: `Texture2D'Keys.key_set_01_d'`, export index 13; the EXP-0088 UELib row reports `TextureFileCacheName="Textures"`.
- Tools: pinned UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; PowerShell; Python 3 standard library for TGA RLE structural validation.
- Scope and limits: compare UModel parser/export behavior in two filesystem search-path conditions. This is not a game runtime test, does not prove UModel's pixels match the original game renderer, and does not resolve TFC GUIDs or offsets independently. Original game files were read-only; a single hash-verified UPK copy and outputs/logs are under ignored `assets/extracted/tfc-reference-probe-abbey-keys/`. `_excluded_coop_project/` was not accessed.
- General tool context: the [UE Viewer FAQ](https://github.com/gildor2/UEViewer/blob/master/Docs/FAQ.md) describes UE3 TFC data as automatically used for streamed textures; this experiment records the behavior of the pinned local UModel build on the selected package.

## Procedure

1. Re-read repository instructions, research status, Blink graph, and build record; verify the EXE hash and both source file identities.
2. Run UModel `-dump` for `key_set_01_d`; confirm its reported cache name. The initial dump reported `TextureFileCacheName = Textures`.
3. Run UModel `-export` with the original CookedPCConsole directory as its package path, where `Textures.tfc` is present. Capture the console log and output TGA.
4. Copy only the exact-hash UPK into an isolated one-file directory. Run UModel `-export` against that directory, with no TFC file available in its search path; capture the warning and output TGA.
5. Compare output file size/hash and parse both TGA headers/RLE streams, requiring packet pixel counts to equal the declared dimensions and the stream to end exactly at file end.

Reproduce from the repository root using fresh output directories under ignored `assets/extracted/` storage:

```powershell
$probeRoot = "assets/extracted/tfc-reference-probe-abbey-keys-repro"
New-Item -ItemType Directory -Path "$probeRoot/no-tfc-input", "$probeRoot/with-tfc", "$probeRoot/without-tfc" | Out-Null
Copy-Item "Dishonored RHCP/DishonoredGame/CookedPCConsole/Abbey_01_Keys_SF.upk" "$probeRoot/no-tfc-input/Abbey_01_Keys_SF.upk"

third_party/ueviewer-gildor/umodel.exe -export -game=dis `
  -path="Dishonored RHCP/DishonoredGame/CookedPCConsole" `
  -out="$probeRoot/with-tfc" Abbey_01_Keys_SF.upk key_set_01_d *> "$probeRoot/with-tfc.log"

third_party/ueviewer-gildor/umodel.exe -export -game=dis `
  -path="$probeRoot/no-tfc-input" -out="$probeRoot/without-tfc" `
  Abbey_01_Keys_SF.upk key_set_01_d *> "$probeRoot/without-tfc.log"
```

## Observations

- With the original package path, UModel logged `Reading key_set_01_d mip level 0 (256x256) from Textures.tfc` and wrote a 89,208-byte TGA, SHA-256 `548B1384B1FC5DF91BBD1F79E689FFFDCEA47C9F83EFD0F10D9A338A5502BAB7`.
- With only the identical UPK in the search path, UModel logged `TFC file "Textures" is missing` and wrote a 24,698-byte TGA, SHA-256 `C238184EE76C3080A7372D18A17F74ACADDFF453F9816E7814938EC243C75887`.
- The first TGA is RLE true-color type 10, 256×256, 24-bit; the second is type 10, 128×128, 24-bit. Each RLE stream accounts for exactly its declared pixel count and consumes the full payload with no trailing data.
- Both export commands completed and emitted files. The missing-TFC condition produced a lower-resolution export for this object; the files are not byte-identical.
- Captured logs and generated outputs live under ignored `assets/extracted/tfc-reference-probe-abbey-keys/`.

## Interpretation and claim limits

- **Observed:** for this exact package/object and pinned UModel build, the parser reads mip 0 from `Textures.tfc` when available; without the named TFC it logs a missing-cache warning and exports at a lower reported resolution.
- **Inferred, limited:** the cache-name join in EXP-0090 identifies a functional UModel TFC lookup path for this sample. This is parser behavior, not proof of the game's runtime lookup or rendered output.
- **Unknown:** whether the exported mip pixels match in-game output, why exactly four package bytes are dropped, how the serialized GUID and per-mip offsets map to TFC records, and whether every cache-bearing object follows this same path.
- **Limit:** one package, one texture, one UModel build; the outcome does not generalize to every texture format/cache or Dishonored runtime behavior.

## Links

- [EXP-0090 TextureFileCacheName corpus joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [EXP-0083 real Texture2D export](EXP-0083-umodel-single-texture-real-export.md)
- [UModel sample and captured logs](../assets/extracted/tfc-reference-probe-abbey-keys/)
