---
id: EXP-0090
title: UELib Texture2D cache-name joins to installed TFC files
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do parsed Texture2D TextureFileCacheName fields map to installed TFC file basenames across the package corpus?"
---

# EXP-0090 — UELib Texture2D cache-name joins to installed TFC files

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: stream UELib property rows from the EXP-0088 all-install run, select `TextureFileCacheName` `NameProperty` values, group unique owner indices by source package/owner class/cache name, and join case-insensitively against `.tfc` basenames in the exact-build file manifest.
- Exclusions: this is a name-to-basename catalog join. It does not parse TFC internal indexes, match `TextureFileCacheGuid` to cache entries, recover byte offsets, validate texture payloads, or prove runtime loading. `_excluded_coop_project/` was not accessed.
- Inputs: the hash-reconciled EXP-0088 property JSONL (ignored; 9,073,077,390 bytes) and [build file manifest](../research/builds/BUILD-STEAM-10256413/files.csv). Durable outputs: [join table](../research/builds/BUILD-STEAM-10256413/uelib-texture-tfc-references.csv) and [summary](../research/builds/BUILD-STEAM-10256413/tfc-reference-summary.json).
- Tool: [TFC reference indexer](../tools/index_uelib_tfc_references.py), Python 3 standard library.

## Procedure

1. Re-read repository instructions, research status, Blink activation graph, and build record; verify the current EXE hash.
2. Load all `.tfc` manifest rows keyed by basename without extension.
3. Recheck current size and SHA-256 of all 12 TFC files against the manifest.
4. Stream the EXP-0088 `default-properties.jsonl`, select rows whose `propertyName` is `TextureFileCacheName` and `propertyType` is `NameProperty`, and count unique owner package indices by source package/value.
5. Join each observed value to the manifest TFC basename, preserving source package hashes, target path, bytes, and target SHA-256.

Reproduce from the repository root:

```powershell
python tools\index_uelib_tfc_references.py `
  --properties assets\extracted\uelib-object-init-ondemand-full\default-properties.jsonl `
  --manifest research\builds\BUILD-STEAM-10256413\files.csv `
  --game-root "Dishonored RHCP" `
  --output research\builds\BUILD-STEAM-10256413\uelib-texture-tfc-references.csv
```

## Observations

- The join table contains 1,548 source-package/class/cache-name groups, representing 1,263 distinct source-package/cache-name pairs from 482 distinct source packages and 126,006 unique cache-bearing object indices.
- Owner classes are `Texture2D` (84,478 objects; 938 class-specific groups), `LightMapTexture2D` (31,436; 325), `ShadowMapTexture2D` (10,063; 256), and `TextureFlipBook` (29; 29). The property is not limited to the `Texture2D` class.
- The property corpus contains 12 distinct cache names; the manifest contains 12 TFC basenames. All 1,263 observed pairs match an installed TFC basename; there are zero unmatched pairs.
- All 12 current TFC files matched manifest size and SHA-256 during this run.
- Per-cache object counts and source package counts:

| Cache name | Source packages | Cache-bearing objects | TFC manifest bytes |
|---|---:|---:|---:|
| `CharTextures` | 205 | 8,525 | 301,325,850 |
| `CharTextures_DLC05` | 30 | 189 | 2,923,062 |
| `CharTextures_DLC06` | 25 | 382 | 49,798,975 |
| `CharTextures_DLC07` | 31 | 621 | 106,762,042 |
| `Lighting` | 207 | 25,288 | 548,298,402 |
| `Lighting_DLC05` | 42 | 5,149 | 73,883,321 |
| `Lighting_DLC06` | 28 | 4,657 | 82,637,946 |
| `Lighting_DLC07` | 48 | 6,405 | 106,124,066 |
| `Textures` | 481 | 68,945 | 1,209,025,724 |
| `Textures_DLC05` | 55 | 1,381 | 32,295,353 |
| `Textures_DLC06` | 46 | 1,859 | 153,944,404 |
| `Textures_DLC07` | 65 | 2,605 | 237,967,555 |

- Some DLC packages name base caches such as `Textures` and `Lighting`; the table preserves those observed values and maps them to the base CookedPCConsole TFC files. This is a static name match only.

## Interpretation and claim limits

- **Observed:** UELib's formatted `TextureFileCacheName` values form a complete basename match to the 12 TFC files listed in this build manifest for 126,006 emitted cache-bearing objects across four owner classes and 482 packages.
- **Inferred, limited:** the property is useful as a static package-to-cache-name relation for further resource analysis. It does not identify a particular byte range or prove that the game loads the named cache for an object.
- **Unknown:** TFC internal directory/index layout, GUID-to-entry resolution, serialized payload identity, and runtime cache selection/streaming behavior.
- **Limit:** coverage is limited to objects for which UELib emitted this property row; 482 is not all 904 packages, and name equality is not payload validation.

## Links

- [EXP-0063 install file-family/config/localization profile](EXP-0063-install-file-family-and-text-resource-profile.md)
- [EXP-0064 non-UPK resource header census](EXP-0064-non-upk-resource-header-signatures.md)
- [EXP-0088 UELib on-demand object load](EXP-0088-uelib-all-install-on-demand-object-load.md)
- [TFC reference indexer](../tools/index_uelib_tfc_references.py)
