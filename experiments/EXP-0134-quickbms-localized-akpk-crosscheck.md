---
id: EXP-0134
title: QuickBMS cross-check of localized AKPK entry tables
experiment_status: done
claim_status: observed
build: "10256413"
question: Does the pinned QuickBMS Wwise AKPK listing reproduce the EXP-0130 Python catalog's bank and sound paths, offsets, and sizes across all nonempty localized extension containers?
---

# EXP-0134 — QuickBMS cross-check of localized AKPK entry tables

- Experiment status: done
- Claim status: observed
- Build ID: 10256413
- Question: Does list-only output from the pinned Wwise QuickBMS script match the EXP-0130 Python catalog on entry names, offsets, and byte sizes for the localized AKPK extension cohort?
- Scope and exclusions: The 4,056 nonempty AKPK package rows under the EXP-0130 CookedPC/DLC extension cohort, deduplicated by exact package SHA-256 plus byte size for QuickBMS invocations and mapped back to every source path. The three zero-byte files are counted but have no entries to list. No payload decoding, HIRC semantics, locale policy, runtime loading, or original vendor specification claim.
- Prerequisites / starting state: Steam build 10256413 EXE hash and all source package hashes/sizes match the build record/manifest and EXP-0130 package table. EXP-0130 table parser output is the comparison catalog.
- Tools and versions: QuickBMS 0.12.0 (`third_party/quickbms-0.12.0/quickbms.exe`, SHA-256 `FF812D38E22AEA0CC2CDC13C5C91CA34FAE4443AB12987002105BE6BAB3F4948`); pinned `wwise_pck_extractor.bms` SHA-256 `4459C0A4C354A92DCAD335599C389E8296908BD8B38FB128BD4C505AEAEE6B5D`; Python 3 standard library.
- Durable outputs: [per-source-content comparison](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-quickbms-unique.csv), [QuickBMS entry rows](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-quickbms-entries.csv), [all source-path outcomes](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-quickbms-packages.csv), [run summary](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-quickbms-summary.json), and [reproduction tool](../tools/wwise_localized_akpk_quickbms_crosscheck.py). The resumable QuickBMS result cache and per-invocation listings remain under ignored `.tmp/`.

## Procedure

1. Reconcile executable, package manifest, EXP-0130 package/entry counts, source hashes, and QuickBMS/BMS hashes.
2. For every distinct nonempty source package content `(SHA-256, byte size)`, run QuickBMS in list-only mode (`-0 -L`) and parse output listing rows; do not extract payloads.
3. Compare the QuickBMS `(entry path, offset, size)` multiset against the Python rows for one source path with those exact bytes. First verify that Python's per-path row multisets are identical for all source paths sharing a content hash; this avoids counting repeated catalog rows for byte-identical `.INT/.RUS` or localized variants as duplicate entries in one file. Preserve per-unique-content and every source-path outcome; cache by build/tool/script/source identity for safe resumption.
4. Report exact matches, mismatches, parse/list failures, and empty source count. Agreement is an independent implementation cross-check of the observed container entry catalog, not an independent vendor specification.

## Observations

- All 4,059 package paths (4,056 nonempty, three zero-byte files) matched their current manifest and EXP-0130 sizes/SHA-256 values. Those paths contain 2,570 distinct nonempty `(SHA-256, byte size)` payloads.
- QuickBMS 0.12.0 with the pinned Wwise extractor emitted 10,002 `(entry path, offset, size)` rows over those 2,570 unique source payloads. The EXP-0130 Python catalog contains 16,168 path-level rows; after grouping by exact source content, its canonical per-content entry rows total 10,002.
- Python per-path row multisets agreed across all manifest paths that shared a package content hash. The QuickBMS multiset then matched exactly for 2,570/2,570 unique payloads: zero missing rows, extra rows, list failures, or mismatched paths. Mapping the same result back covers 4,056/4,056 nonempty package paths; the remaining three paths are empty.
- One initial comparison attempt incorrectly compared one QuickBMS listing per unique byte payload against Python rows repeated for every identical source path. That produced apparent count mismatches for duplicate-content groups. After checking the repeated path catalogs and comparing one canonical per-path multiset per exact byte payload, all 2,570 unique payloads and 4,056 nonempty source paths matched. The retained QuickBMS listings were unchanged; only the comparison accounting was corrected.
- QuickBMS was invoked in `-0 -L` list-only mode. It wrote temporary catalog listings under ignored `.tmp/`; the tool removes each listing after caching parsed rows. No package payload extraction was requested.
- Summary records both run inputs by SHA-256 and reports 2,570 successful cached parser results. The final summary regeneration reused all 2,570 exact-key cache results after the full list-only run.

## Interpretation

- Finding and status (observed / inferred / unknown): Observed: pinned QuickBMS and the EXP-0130 Python table parser report identical entry paths, offsets, and sizes across all nonempty source paths in this cohort after accounting for byte-identical package variants.
- Confidence and rationale: High for the recorded build/source files and this exact list-only comparison: executable, all package paths, QuickBMS binary, BMS script, Python package/entry catalogs, and per-content outcome counts were checked and fingerprinted. The agreement is between two implementations, not an independent Wwise vendor specification.
- Alternative explanations: Both tools might share assumptions or defects about an undocumented AKPK variant; exact table agreement does not prove that a listed bank or WEM is loaded or played.
- Evidence that would falsify this interpretation: Reproducing either parser against current hash-matched inputs and obtaining a missing/extra/different `(path, offset, size)` row, or establishing that the pinned QuickBMS/BMS/source identity differs from the recorded fingerprints.

## Reproduction

- Reset/cleanup steps: None. For a forced QuickBMS rerun, remove the ignored `.tmp/wwise-localized-akpk-quickbms-cache.jsonl`; no input files are modified.
- Repeat count and variation: One list-only QuickBMS invocation per 2,570 unique package payloads. A later deterministic report regeneration reused all 2,570 successful cache records.
- Known sources of variance: Build, source content, QuickBMS binary, BMS script, options, and cache version form the cache identity. Empty source files have no entry rows and are preserved as a separate denominator.
- Command: `python tools/wwise_localized_akpk_quickbms_crosscheck.py --jobs 4`

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related experiments: [EXP-0065 QuickBMS PCK census](EXP-0065-wwise-pck-and-bink-media-census.md), [EXP-0120 Python AKPK parser cross-check](EXP-0120-wwise-pck-python-table-crosscheck.md), [EXP-0130 localized AKPK census](EXP-0130-localized-akpk-container-census.md)
- Open questions: Runtime package/locale selection; whether HIRC media links execute or play in-game.
