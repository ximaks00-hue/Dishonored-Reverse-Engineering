---
id: EXP-0135
title: Cross-domain audit of localized AKPK HIRC media IDs against PCK audio
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do unmatched localized AKPK HIRC media IDs resolve by exact numeric ID or exact bank bytes in the existing PCK WEM/BNK catalogs?
---

# EXP-0135 — Cross-domain audit of localized AKPK HIRC media IDs against PCK audio

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: Among the EXP-0133 unmatched AKPK HIRC media edges, are there exact numeric-ID candidates in the 503-PCK WEM catalog or byte-identical bank payloads in the 503-PCK BNK corpus?
- Scope and exclusions: All 24,205 unique AKPK HIRC `(bank payload SHA-256, sound ID, media ID)` edge keys without a same-source AKPK WEM candidate, all 23,549 distinct media IDs in those keys, the 1,908 PCK WEM entries from EXP-0065/0119, and all 503 PCK embedded BNK payloads from EXP-0077. Exact numeric ID and exact payload SHA are candidate-identity checks only. This does not establish event meaning, package ownership, runtime loading, locale policy, playback, or exhaust other media domains.
- Prerequisites / starting state: Build 10256413 executable SHA-256 matches build record/manifest. AKPK source paths and hashes were revalidated across the cohort by EXP-0134; HIRC/WEM catalogs come from EXP-0132/0133. PCK WEM/BNK catalogs come from EXP-0065/0077/0119; PCK sources, WEM ranges/payload hashes, and BNK range hashes are revalidated in this experiment.
- Tools and versions: Python 3 standard library; saved QuickBMS PCK entry catalog, PCK WEM decode audit, pinned wwiser HIRC catalogs, localized AKPK HIRC/WEM catalogs.
- Durable outputs: [unmatched media ID audit](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-pck-domain-unmatched-media-ids.csv), [PCK bank hash crosswalk](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-pck-domain-pck-bank-hashes.csv), [run summary](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-pck-domain-summary.json), and [reproduction tool](../tools/wwise_localized_akpk_pck_audio_domain_audit.py).

## Procedure

1. Verify the exact build identity and rehash all 503 PCK source files against the manifest and saved entry catalog.
2. Re-read each PCK BNK range, verify its hash/size against EXP-0077's extracted-bank catalog, and compare its exact hash to the 2,570 unique localized AKPK bank payload hashes.
3. Reconcile all 1,908 PCK WEM catalog rows to their successful EXP-0119 decode rows; re-read each source range and verify its byte hash; extract numeric terminal `.wem` IDs from the stored embedded names.
4. Deduplicate EXP-0133 rows into 24,205 AKPK HIRC edge keys classified as having no same-source localized WEM match. Compare each `media_id` and `file_id` exactly against the PCK WEM ID set; retain per-ID counts and candidate rows.
5. Record candidate counts and input fingerprints. Exact identifiers or byte hashes remain static candidates and do not prove semantic ownership or runtime use.

## Observations

- All 503 PCK source files matched the manifest by size/SHA-256. All 503 BNK entry ranges matched EXP-0077's extracted-bank hashes and sizes; they represent 480 distinct bank payload hashes. None of those 480 hashes occurs among the 2,570 unique localized AKPK bank payloads.
- All 1,908 PCK WEM rows reconciled one-to-one with EXP-0119 successful decode rows. Re-reading each range reproduced its recorded SHA-256; the entries contain 1,314 distinct numeric terminal filename IDs, of which 315 IDs occur in multiple PCK entries.
- The EXP-0133 no-same-source-WEM set contains 24,205 unique `(bank payload SHA-256, sound ID, media ID, file ID)` keys and 23,549 distinct `media_id` values. None of these media IDs, or their associated `file_id` values, matches a numeric WEM ID in the 503-PCK catalog.
- The 503 PCK BNK exact-content crosswalk has zero SHA-256 intersections with the localized AKPK HIRC bank payload cohort. These are negative results within the tested catalogs; they do not show that the IDs or banks are absent from other installed media domains or runtime-loaded content.

## Interpretation

- Finding and status (observed / inferred / unknown): Observed: no exact PCK WEM numeric-ID candidates or exact PCK/AKPK bank-payload hash matches were found for this tested cross-domain comparison. It remains unknown where the 24,205 unmatched HIRC edge keys resolve, whether they require another media catalog, or whether the fields have the assumed roles.
- Confidence and rationale: High for the bounded negative comparison: all PCK files were rehashed; bank byte ranges matched EXP-0077; WEM ranges rehashed to all successful EXP-0119 payload identities; AKPK HIRC candidates came from the exact-source EXP-0133 join.
- Alternative explanations: Candidate media may live in other banks or resource families, be constructed/resolved dynamically, or use parser fields with different semantics. Lack of numeric equality or byte-identical bank payloads does not imply a broken reference.
- Evidence that would falsify this interpretation: A missing/incorrect source range or payload hash, an omitted PCK WEM catalog entry, or a reproducible exact numeric-ID/hash match under the recorded complete source catalogs.

## Reproduction

- Reset/cleanup steps: None; all source ranges were read-only and no payloads were retained.
- Repeat count and variation: One deterministic full-catalog comparison.
- Known sources of variance: Exact-build manifests and source/catalog SHA-256 values are checked on every run; input parser domain remains limited to saved PCK and localized AKPK catalogs.
- Command: `python tools/wwise_localized_akpk_pck_audio_domain_audit.py`

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related experiments: [EXP-0065 PCK entry census](EXP-0065-wwise-pck-and-bink-media-census.md), [EXP-0077 PCK HIRC census](EXP-0077-wwise-bank-hirc-and-media-link-census.md), [EXP-0119 PCK WEM decode](EXP-0119-wwise-wem-full-decode-census.md), [EXP-0132 localized AKPK HIRC](EXP-0132-localized-akpk-hirc-structure-census.md), [EXP-0133 localized AKPK media identity join](EXP-0133-localized-akpk-hirc-wem-identity-join.md)
- Open questions: Other installed media domains; runtime bank/locale selection, event resolution, and playback.
