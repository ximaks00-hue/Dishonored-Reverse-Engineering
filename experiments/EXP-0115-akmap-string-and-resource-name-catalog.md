---
id: EXP-0115
title: AKMAP string catalog and exact package-basename joins
experiment_status: done
claim_status: observed
build: "10256413"
question: Can all four installed AKMAP files be partitioned into a reproducible candidate string region and joined by exact string equality to installed PCK/UPK basenames?
---

# EXP-0115 — AKMAP string catalog and exact package-basename joins

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect all four manifest-listed `.akmap` files; record the observed version/offset/tag fields; extract the NUL-separated printable ASCII sequence from byte 8 through the terminating NUL after the `EGLOBAL` bytes; and perform case-insensitive exact basename equality against manifest-listed `.pck` and `.upk` paths.
- Exclusions: no interpretation of the post-string binary tables, no semantics assigned to `EGLOBAL` or integer fields, no claim that exact name equality is an actual dependency edge, and no runtime loading evidence.
- Durable outputs: [string and basename-match catalog](../research/builds/BUILD-STEAM-10256413/akmap-string-catalog.csv), [four-file summary](../research/builds/BUILD-STEAM-10256413/akmap-name-match-summary.json), and [reproduction tool](../tools/akmap_name_catalog.py).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify build 10256413 and the recorded executable SHA-256.
2. Select all `.akmap` rows from the saved manifest. Check each current file's size/hash and verify the executable against both the build record and manifest.
3. Read the first two little-endian DWORDs. Confirm the second value points to bytes `EGLOBAL\0`. Extract NUL-separated printable ASCII tokens from byte 8 to the byte immediately after that terminator; reject malformed bounds, empty tokens, or non-printable values.
4. Compare each token case-insensitively with `.pck` and `.upk` file stems in the saved install manifest. Record matching paths as textual candidates, preserving duplicate-basename fanout.
5. Run `python tools/akmap_name_catalog.py` to regenerate both outputs and check the four-file / 2,871-string denominators.

## Observations

- All four current AKMAP files match their saved manifest sizes and SHA-256 values. Each begins with little-endian version value `1`; the second DWORD points at the ASCII byte sequence `EGLOBAL\0`. The candidate NUL-separated printable string region is `[8, field_04 + 8)` in all four files.
- The four candidate string regions contain 2,871 rows total: 982 in the base install AKMAP, 311 in DLC05, 596 in DLC06, and 982 in DLC07. The base and DLC07 files have identical size and SHA-256.
- Case-insensitive exact basename comparisons found these `.pck` matches: base/DLC07 each 399 distinct string values mapping to 422 manifest paths; DLC05 205 values / 218 paths; DLC06 277 values / 300 paths.
- Exact `.upk` basename comparisons found: base/DLC07 each 160 distinct string values mapping to 161 manifest paths; DLC05 61 values / 61 paths; DLC06 100 values / 101 paths. Where path counts exceed string counts, the manifest contains repeated basenames in different package paths; the CSV preserves all matches.
- Immediately after the candidate string region, the first four raw DWORDs are `12, 160, 0, 0` for base/DLC07, `12, 61, 0, 0` for DLC05, and `12, 100, 0, 0` for DLC06. The remaining binary regions are 31,124, 10,732, and 18,712 bytes respectively; their layouts are not decoded here.

## Interpretation and claim limits

- **Observed:** every AKMAP contains a bounded printable NUL-separated string sequence with hundreds of exact textual matches to installed PCK/UPK basenames. These joins provide candidate cross-file name associations that were not present in the prior AKMAP header-only census.
- **Unknown:** the string sequence's role in the AKMAP format, the meaning of `EGLOBAL` and trailing DWORDs, whether matched package names are selected/loaded by the game, and whether the trailing records encode additional links or indices.
- **Limit:** the basename join establishes equality of text only. Duplicate package basenames create multiple candidate paths, and no runtime or payload-level relationship was tested.

## Reproduction

From the repository root:

```powershell
python tools/akmap_name_catalog.py `
  --game-root "Dishonored RHCP" `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --strings-output research/builds/BUILD-STEAM-10256413/akmap-string-catalog.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/akmap-name-match-summary.json
```

## Links

- [EXP-0064 non-UPK header census](EXP-0064-non-upk-resource-header-signatures.md)
- [EXP-0065 PCK entry and Bink census](EXP-0065-wwise-pck-and-bink-media-census.md)
- [Build inventory](../research/builds/BUILD-STEAM-10256413/files.csv)
- [Project completion contract](../docs/roadmap.md)
