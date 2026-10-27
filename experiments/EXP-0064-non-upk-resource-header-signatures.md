---
id: EXP-0064
title: Non-UPK audio, movie, and texture-cache header signatures
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do the selected non-UPK audio, movie, and texture-cache extensions share stable leading-byte signatures in the current manifest tree?"
---

# EXP-0064 — Non-UPK audio, movie, and texture-cache header signatures

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: read the first 16 bytes from every manifest-listed `.pck`, `.bnk`, `.akmap`, `.bik`, and `.tfc` file; compare current presence and file sizes with the saved manifest.
- Exclusions: no full payload parsing, decompression, playback, or cryptographic content verification; no game launch or modification; `_excluded_coop_project/` was not accessed.
- Tools: [resource_header_census.py](../tools/resource_header_census.py); Python 3; saved build file manifest.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the local executable hash against build `10256413`.
2. Select manifest rows with extensions `.pck`, `.bnk`, `.akmap`, `.bik`, and `.tfc`.
3. For each path, check that it exists and current file size matches the manifest; read only the first 16 bytes.
4. Group observations by extension and first four bytes; write one output row per file to [resource-header-census.csv](../research/builds/BUILD-STEAM-10256413/resource-header-census.csv).

Reproduce from the repository root:

```powershell
python tools/resource_header_census.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --game-root "Dishonored RHCP" `
  --output research/builds/BUILD-STEAM-10256413/resource-header-census.csv
```

## Observations

- The manifest contains 596 selected files: 503 `.pck`, one `.bnk`, four `.akmap`, 76 `.bik`, and 12 `.tfc`.
- All 596 paths currently exist and have file sizes matching the saved manifest.
- All 503 `.pck` files begin `41 4B 50 4B` (`AKPK`). The single `.bnk` begins `42 4B 48 44` (`BKHD`). All 76 `.bik` files begin `42 49 4B 69` (`BIKi`).
- All 12 `.tfc` files begin `C1 83 2A 9E`. All four `.akmap` files begin `01 00 00 00`; this is recorded as a repeated leading DWORD, not a recognized magic value.
- The census records the first 16 bytes for all paths. It does not calculate hashes or parse payload blocks.

## Interpretation / claims

- **Observed:** each selected extension has a consistent four-byte prefix within this exact local snapshot.
- **Inferred, limited:** the `.pck`, `.bnk`, and `.bik` prefixes are useful format-family triage signatures. This experiment does not verify standards compliance or extraction support.
- **Unknown:** `.tfc` and `.akmap` header field semantics, internal block layouts, compression, references between resources, and whether the files are loaded at runtime.
- **Not established:** complete audio/video/texture-cache parsing, successful decoding, or resource-to-UPK dependency relations.

## Reproduction and limitations

- Re-run the command above. The tool reads at most 16 bytes per file and reports file size alongside the manifest size.
- Full per-file observations: [resource-header-census.csv](../research/builds/BUILD-STEAM-10256413/resource-header-census.csv).
- Family denominator and text/config profile: [EXP-0063](EXP-0063-install-file-family-and-text-resource-profile.md).
- Same leading bytes do not establish that files share all versions/options or that a particular parser can decode them.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- File-family inventory: [EXP-0063](EXP-0063-install-file-family-and-text-resource-profile.md)
- Header census helper: [resource_header_census.py](../tools/resource_header_census.py)
- Project completion contract: [roadmap](../docs/roadmap.md)
