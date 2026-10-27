---
id: EXP-0130
title: AKPK table census for localization-coded extensions
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do the CookedPC/DLC files with localization-like extensions use the AKPK table format already measured in PCK files, and what package-entry and same-stem variant coverage can be established?
---

# EXP-0130 — AKPK table census for localization-coded extensions

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: Do the CookedPC/DLC files with localization-like extensions use the AKPK table format already measured in PCK files, and what package-entry and same-stem variant coverage can be established?
- Scope and exclusions: All manifest paths ending in `.INT`, `.RUS`, `.DEU`, `.ESN`, `.FRA`, `.ITA`, or `.JPN` under `DishonoredGame/CookedPCConsole` or `DishonoredGame/DLC/PCConsole` (extension names are treated as labels, not proof of runtime locale); exact-build hashes, the EXP-0120 AKPK parser, payload-header checks, and same-stem byte identity. No full bank/WEM decoding, HIRC parsing for this cohort, independent QuickBMS listing, runtime load/locale behavior, or install provenance claim.
- Prerequisites / starting state: Re-read repository instructions, research status, Blink graph, roadmap, and build record; Steam build 10256413 executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Tools and versions: Python 3 standard library; [EXP-0120 Python AKPK table parser](../tools/wwise_pck_table_crosscheck.py), previously cross-checked against the QuickBMS entry census for 503 `.pck` files; exact-build manifest and local package bytes.
- Durable outputs: [4,059-file package table](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-packages.csv), [16,168-entry catalog](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-entries.csv), [same-stem variant comparison](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-variants.csv), [aggregate summary](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-summary.json), and [reproduction tool](../tools/wwise_localized_akpk_census.py).

## Procedure

1. Select all matching extensions under the two manifest path roots; retain empty files in the denominator.
2. Reconcile each local byte length and SHA-256 against the saved build manifest.
3. For each nonempty file, parse its AKPK sections using the EXP-0120 Python implementation; record languages, bank/sound entries, offsets, sizes, and payload four-byte markers.
4. Check table end against the first parsed payload and check parsed payload ranges for overlap.
5. Group same-parent, same-stem extension variants and compare full-file SHA-256 values.

## Observations

- The selected manifest cohort contains 4,059 files totaling 4,085,787,427 bytes: 1,061 `.INT`, 1,058 `.RUS`, and 388 each of `.DEU`, `.ESN`, `.FRA`, `.ITA`, and `.JPN`.
- Three `.INT` files named `DishonoredGame.int` in DLC05, DLC06, and DLC07 are zero bytes. All other 4,056 files begin with `AKPK` and parse successfully with the EXP-0120 table parser. There were zero manifest size mismatches and zero SHA-256 mismatches.
- The parser records one bank entry in each nonempty container (4,056 bank entries total) and 12,112 sound entries; it records no external entries. All parsed bank versions are `65`, all bank payloads begin with `BKHD`, and all sound payloads begin with `RIFF`.
- In all 4,056 parsed containers, the parsed tables end at or before the first payload range. The 16,168 parsed payload ranges contain no overlaps under the recorded offset/size table. These checks validate bounds and markers, not complete payload decodes.
- There are 1,058 same-parent, same-stem variant groups: 670 two-file groups in `CookedPCConsole` and 388 seven-file groups across DLC06/DLC07. Every CookedPCConsole `.INT`/`.RUS` pair has an identical full-file SHA-256.
- Each of the 388 seven-file DLC groups has exactly five distinct full-file hashes. The `.INT`, `.JPN`, and `.RUS` members are byte-identical within every group; `.DEU`, `.ESN`, `.FRA`, and `.ITA` each form a distinct hash class in every group.
- The embedded language tables report `german` for `.DEU`, `spanish(spain)` for `.ESN`, `french(france)` for `.FRA`, and `italian` for `.ITA`. The `.INT`, `.JPN`, and `.RUS` parsed tables report `english(us)` (plus `sfx` where present); 11 parsed `.INT` and 11 `.RUS` files report only `sfx`.
- The parser implementation was previously compared to QuickBMS for `.pck` sources. No QuickBMS listing or second parser output was available for this 4,059-file extension cohort; the current evidence is parser output plus full-file hash/size reconciliation and internal range/magic checks.

## Interpretation

- **Observed:** 4,056 nonempty files in this extension/path cohort satisfy the AKPK parser's section and entry constraints; three additional manifest rows are empty files. The parser reports the entry counts, version values, and payload markers above.
- **Observed:** the recorded same-stem groups and byte-identical extension classes match the exact full-file SHA-256 comparisons in the variant catalog.
- **Inferred, limited:** these files use the same observed AKPK container/table layout as the `.pck` cohort. This inference uses the EXP-0120 implementation; that implementation's QuickBMS comparison was performed on `.pck` files, not this extension cohort.
- **Inferred, limited:** several extension variants share exact package bytes, including `.INT/.RUS` base pairs and `.INT/.JPN/.RUS` DLC triplets. File suffixes and internal language strings do not establish actual game locale selection.
- **Unknown:** bank HIRC contents and completeness, WEM decode integrity, why some variants are duplicates, language-selection rules, references from AKMAP/config/package metadata, runtime loading, and provenance of every local file.
- Confidence: High for manifest reconciliation, byte identity, table parse success, and observed four-byte payload markers; medium for format-family classification; no runtime claims.
- Alternative explanations: The extension variants could be build-time packaging outputs or install copies whose names do not represent the runtime language policy; the parser could share an unrecognized layout assumption with its original QuickBMS-derived implementation.
- Evidence that would falsify this interpretation: A build-specific independent parser or QuickBMS listing that conflicts with the reported table offsets/entries, or a corrected manifest/hash comparison that changes the cohort.

## Reproduction

```powershell
python tools/wwise_localized_akpk_census.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --game-root "Dishonored RHCP" `
  --packages-output research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-packages.csv `
  --entries-output research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-entries.csv `
  --variants-output research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-variants.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-summary.json
```

The command reads source package files and writes only the analysis catalogs; it extracts no payloads.

## Links

- Build: `research/builds/BUILD-STEAM-10256413/build.md`
- Related experiments: EXP-0065, EXP-0077, EXP-0115, EXP-0120
- Open questions: HIRC/WEM coverage and package/reference/runtime joins for these additional containers.
