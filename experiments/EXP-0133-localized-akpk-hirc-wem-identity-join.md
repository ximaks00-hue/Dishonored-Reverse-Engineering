---
id: EXP-0133
title: Static HIRC media ID to localized AKPK WEM identity join
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do parser-reported HIRC media IDs have exact same-source AKPK sound-resource ID candidates, and can every decoded WEM occurrence be covered without ambiguous source/resource keys?
---

# EXP-0133 — Static HIRC media ID to localized AKPK WEM identity join

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: How completely do HIRC `CAkSound` `sourceID` values match the resource IDs and decoded payloads in the exact AKPK source container, and what remains unresolved?
- Scope and exclusions: All 31,637 `sound_media` rows in the 2,570 unique bank payloads from EXP-0132, all 4,056 bank source occurrences, all 12,112 sound-entry occurrences, and all 7,213 decoded unique WEM payloads from EXP-0131. A same-source path plus equal parser/catalog ID is a static identity candidate. This does not independently validate EXP-0130 offsets, establish Wwise source semantics, prove HIRC object ownership at runtime, select a locale/bank, or prove playback.
- Prerequisites / starting state: Exact Steam build 10256413 executable hash `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`. HIRC and WEM summaries both report the same AKPK source inventory counts; the current EXP-0130 entry table SHA-256 matches EXP-0132's recorded entry-table fingerprint. HIRC parse failures are zero; all WEM payload decode outcomes are successful.
- Tools and versions: Python 3 standard library. Inputs and SHA-256 fingerprints are recorded in the join summary. Parser-derived HIRC edges are from pinned wwiser/EXP-0132; WEM payload decode results are from vgmstream r2023/EXP-0131.
- Durable outputs: [HIRC-to-WEM occurrence join](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-media-join.csv), [join summary](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-media-join-summary.json), and [reproduction tool](../tools/wwise_localized_akpk_hirc_media_join.py).

## Procedure

1. Reconcile the HIRC and WEM run summaries, their exact-build EXE hashes, CSV row counts, and the current EXP-0130 AKPK entry-table hash.
2. Index HIRC bank occurrences by exact bank payload SHA-256, WEM sound occurrences by `resource_id`, and decoder outcomes by `(payload_sha256, byte size)`.
3. For every `CAkSound` media edge, compare `media_id` to WEM `resource_id`. Label a candidate same-source only when the ID and exact source path both match. Label any ID-only match in another source file separately; do not treat it as same-bank evidence. Preserve unmatched edges.
4. Require the candidate source/resource key set to match all WEM occurrence keys exactly, one-to-one, and require each joined payload to have a successful decode record.
5. Independently check whether an otherwise unmatched `file_id` matches any WEM resource ID; report this separately from the `media_id` join.

## Observations

- HIRC source: 31,637 `sound_media` edges from 2,559 unique bank payload hashes. WEM source: 12,112 sound-entry occurrences, 7,368 distinct resource IDs, and 7,213 distinct successfully decoded payload hashes.
- 7,432 unique `(bank payload SHA-256, sound ID, media ID)` edge keys have a same-source `media_id == resource_id` candidate. Expanding across package occurrences yields 12,112 candidate rows: exactly one for every WEM `(source_path, resource_id)` key, with no missing, duplicate, or extra keys. All 12,112 candidates have `file_id == media_id`, map to a decoded payload, and remain in the exact same source path.
- These occurrence candidates cover all 7,213 unique WEM payload SHA-256/size identities. This is a catalog identity join, not perceptual or playback validation.
- The remaining 24,205 unique edge keys have no WEM `resource_id` candidate. No unmatched edge has a `file_id` that matches any resource ID in the localized AKPK WEM catalog. The 24,205 do not establish missing audio or a broken reference; their IDs may be outside this catalog or the parser fields may have different meanings.
- No cross-source-only ID candidates occurred. Source paths, media/resource IDs, file IDs, payload SHA-256 values, and decode statuses are retained per output row.
- All inputs are fingerprinted in the summary; the join tool refuses changed input counts, table hashes, mismatched build hashes, incomplete WEM occurrence coverage, or missing decode success.

## Interpretation

- Finding and status (observed / inferred / unknown): Observed, complete static candidate mapping for all 12,112 AKPK WEM occurrences to HIRC media-ID rows in the exact same source containers; 24,205 unique HIRC edge keys remain unmatched by this WEM catalog. The parser/catalog ID equality strongly supports a same-container media identity candidate, but original Wwise semantics and runtime consumption remain unknown.
- Confidence and rationale: High confidence in the one-to-one CSV-key reconciliation and recorded input hashes/counts. The conclusion is limited by shared dependence on EXP-0130's AKPK ranges and parser-derived wwiser fields; the WEM decoder proves format acceptance only.
- Alternative explanations: A matching numeric field could carry a different semantic role; media IDs in unmatched HIRC edges could resolve from other banks, packages, built-in media, or runtime data not represented in this cohort.
- Evidence that would falsify this interpretation: An independently verified AKPK table that changes any range or resource ID; a mismatch between exact source bytes and the recorded hashes; or an independent parser/runtime trace showing the matching fields do not identify these WEM payloads.

## Reproduction

- Reset/cleanup steps: None; no payloads are extracted by this join.
- Repeat count and variation: One full deterministic CSV join.
- Known sources of variance: Inputs are checked by SHA-256 and summary counts; CSV row ordering follows the stored HIRC edge and occurrence catalogs.
- Command: `python tools/wwise_localized_akpk_hirc_media_join.py`

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related experiments: [EXP-0130 AKPK table census](EXP-0130-localized-akpk-container-census.md), [EXP-0131 WEM decode census](EXP-0131-localized-akpk-wem-decode-census.md), [EXP-0132 HIRC census](EXP-0132-localized-akpk-hirc-structure-census.md)
- Open questions: Independently validate AKPK entry offsets/resource IDs for this extension cohort; investigate 24,205 unmatched HIRC media edge keys against other bank/media domains; establish runtime bank/locale selection and actual playback behavior.
