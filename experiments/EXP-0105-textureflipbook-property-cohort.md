---
id: EXP-0105
title: TextureFlipBook serialized-property cohort across installed packages
experiment_status: done
claim_status: observed
build: "10256413"
question: Do cache-bearing TextureFlipBook objects in the all-install UELib property corpus share the selected serialized texture and atlas properties?
---

# EXP-0105 — TextureFlipBook serialized-property cohort across installed packages

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: group `TextureFlipBook` owner rows from EXP-0088's all-install UELib formatted-property JSONL, compare selected serialized properties, and reconcile each source package SHA-256 to the build manifest. EXP-0090 supplies the independently generated denominator of 29 cache-bearing `TextureFlipBook` objects.
- Exclusions: no independent package property parser, TFC mip/pixel check, frame ordering/timing rule, or runtime playback was established here. CDO is reported separately from the 29 cache-bearing objects.
- Inputs: ignored EXP-0088 property JSONL (`assets/extracted/uelib-object-init-ondemand-full/default-properties.jsonl`), [build file manifest](../research/builds/BUILD-STEAM-10256413/files.csv), and [EXP-0090 TFC reference table](../research/builds/BUILD-STEAM-10256413/uelib-texture-tfc-references.csv). Outputs: [per-object cohort CSV](../research/builds/BUILD-STEAM-10256413/textureflipbook-property-cohort.csv) and [distribution summary](../research/builds/BUILD-STEAM-10256413/textureflipbook-property-cohort.json).
- Tool: [cohort audit script](../tools/audit_textureflipbook_property_cohort.py), Python 3 standard library.

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; verify the current executable SHA-256.
2. Stream the EXP-0088 JSONL, grouping rows whose owner object path begins with `TextureFlipBook` by source package and package index.
3. Extract selected atlas, rate, dimensions, pixel-format, cache-name, and mip-residency properties; count absent properties and `valueError` rows.
4. Compare every grouped source package SHA-256 with the exact-build manifest. Cross-check the cache-bearing object count against EXP-0090; keep the Engine default object distinct.

Reproduce from the repository root:

```powershell
python tools\audit_textureflipbook_property_cohort.py `
  --properties assets\extracted\uelib-object-init-ondemand-full\default-properties.jsonl `
  --manifest research\builds\BUILD-STEAM-10256413\files.csv `
  --output-csv research\builds\BUILD-STEAM-10256413\textureflipbook-property-cohort.csv `
  --output-json research\builds\BUILD-STEAM-10256413\textureflipbook-property-cohort.json
```

## Observations

- The property stream contained 414 rows grouped into 30 owners in 30 packages. All 30 source package hashes matched the build manifest; there were zero `valueError` rows.
- Twenty-nine owners are the cache-bearing objects cataloged by EXP-0090. All 29 reported `HorizontalImages=4`, `VerticalImages=4`, `FrameRate=32.0000000`, `FrameTime=0.0312500`, `SizeX=2048`, `SizeY=2048`, `OriginalSizeX=2048`, `OriginalSizeY=2048`, `Format=EPixelFormat.PF_DXT1`, `TextureFileCacheName="Textures"`, `MipTailBaseIdx=11`, and `FirstResourceMemMip=4`.
- The remaining owner is `TextureFlipBook'Engine.Default__TextureFlipBook'` in `Engine.upk`: `HorizontalImages=1`, `VerticalImages=1`, `FrameRate=4.0000000`, and `FrameTime=0.2500000`. The selected resource-specific dimensions, format, cache, and mip properties were not emitted for this CDO.
- The per-object CSV preserves package path/hash and owner package index so the distribution can be traced to each UELib row group.

## Interpretation and claim limits

- **Observed:** in this EXP-0088 property corpus, the 29 cache-bearing `TextureFlipBook` objects have identical values for the selected serialized properties, and their 29-object count agrees with EXP-0090. The distinct Engine CDO has different atlas/rate values and lacks the selected resource properties.
- **Unknown:** whether `FrameRate`, `FrameTime`, and atlas dimensions are consumed as expected by the engine, how frames are ordered, and what playback behavior occurs at runtime.
- **Limit:** formatted UELib rows are the evidence source; matching source hashes establish package identity against the local manifest, not correctness of UELib's property decoding. No frame-count or playback rule is inferred from the property values.

## Links

- [EXP-0088 all-install UELib on-demand object load](EXP-0088-uelib-all-install-on-demand-object-load.md)
- [EXP-0090 UELib texture TFC name joins](EXP-0090-uelib-texture-tfc-name-joins.md)
- [EXP-0104 TextureFlipBook mip structural audit](EXP-0104-textureflipbook-mip-structural-audit.md)
- [Cohort audit tool](../tools/audit_textureflipbook_property_cohort.py)
