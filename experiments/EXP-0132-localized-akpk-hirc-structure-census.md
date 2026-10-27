---
id: EXP-0132
title: HIRC structure census for localized AKPK bank cohort
experiment_status: done
claim_status: observed
build: "10256413"
question: What parser-derived HIRC object and static relation rows are present in unique bank payloads from the EXP-0130 CookedPC/DLC AKPK cohort?
---

# EXP-0132 — HIRC structure census for localized AKPK bank cohort

- Experiment status: done
- Claim status: observed
- Build ID: 10256413
- Question: What HIRC object and static relation rows does pinned wwiser report for each unique bank payload from the EXP-0130 AKPK cohort?
- Scope and exclusions: 4,056 bank-entry occurrences across the nonempty CookedPC/DLC AKPK files in EXP-0130, deduplicated by exact payload SHA-256 and byte count. This parses HIRC structures, object labels, and the parser's static relation output. It does not independently validate EXP-0130 AKPK offsets, establish Wwise source semantics, or prove runtime bank loading, event execution, language selection, media resolution, or playback.
- Prerequisites / starting state: Build 10256413 executable SHA-256 matched the build record and manifest; all 4,056 source package paths were rehashed and verified against the manifest. Entry tables and ranges are those catalogued by EXP-0130.
- Tools and versions: Python 3.12.10; wwiser commit `08e937b649bc7007c234bbd59e34a41d5eef3b38`, script SHA-256 `6A12FB9BA8AE3DC0724BFDCBF1AB1657E39E9C60E6BEA091275CF044E3267323`; parser `tools/wwise_bank_hirc_census.py`, SHA-256 `293B4BDA601E8D714FDBAD25FB655FDB16E1E5B120B31FBEAE3221AA8BA301F9`.
- Durable outputs: [unique bank results](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-unique.csv), [HIRC objects](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-objects.csv), [static relation rows](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-edges.csv), [source occurrence mapping](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-occurrences.csv), [run summary](../research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-hirc-summary.json), and [reproduction tool](../tools/wwise_localized_akpk_hirc_census.py). The append-only resumable cache is kept under ignored `.tmp/` and is not a Git artifact.

## Procedure

1. Verify the executable and all AKPK source file hashes against the build manifest; use EXP-0130's bank-entry table.
2. Hash each exact bank byte range, retaining all source occurrence paths and resource IDs. Deduplicate parse jobs on `(SHA-256, byte size)`.
3. For each unique payload, call the pinned wwiser parser with XML output, under a 300-second timeout. Save a checkpoint keyed by build/EXE, wwiser and parser identities/options, source-table fingerprints, and payload identity. Four workers were used.
4. Produce one unique-payload result row, global HIRC object and static-edge rows, and a complete source occurrence mapping. Fail the run if any payload is missing or parsing fails.

## Observations

- All 4,056 bank-entry occurrences from 4,056 verified source files mapped to 2,570 unique bank payloads, totaling 1,144,722,681 bytes. All 2,570 payloads parsed without failures or timeouts; all reported bank version 65.
- The parser emitted 100,115 unique-payload HIRC object rows: 31,637 each `CAkActionPlay`, `CAkEvent`, and `CAkSound`; 2,645 `CAkActorMixer`; 2,559 `CAkAttenuation`; and 2 `CAkState`.
- The parser emitted 126,548 unique-payload static relation rows. Occurrence output preserves source paths and payload identity for all 4,056 entries.
- The run summary fingerprints the executable, wwiser commit/script, parser source, Python version, options, and input table CSVs. The 2,570 successful checkpoints are stored under ignored `.tmp/` for reuse on a matching rerun.

## Interpretation

- Finding and status (observed / inferred / unknown): Observed parser output covers every unique bank payload in this EXP-0130 cohort. HIRC labels and relation rows are parser-derived structural evidence only. Runtime loading, ownership/selection, event meaning, and playback are unknown.
- Confidence and rationale: High confidence in the measured run counts and byte-identical payload deduplication under the recorded inputs; independent AKPK table validation and independent HIRC parser comparison were not performed here.
- Alternative explanations: Parser labels or edge extraction may not represent original Wwise source semantics; table offsets or sizes may be wrong in EXP-0130 despite its internal bounds/hash checks.
- Evidence that would falsify this interpretation: A reproducible parser/output mismatch under the recorded tool and input fingerprints, an independently verified AKPK range mismatch, or a missing/incorrect source occurrence mapping.

## Reproduction

- Reset/cleanup steps: None. Cache is append-only under ignored `.tmp/`; remove it only to force a full recomputation.
- Repeat count and variation: One full cohort run with four workers; pilot runs are not included in the reported full-run counts.
- Known sources of variance: Parser/tool version, options, script hashes, and source table fingerprints are included in cache identity and summary. Temporary directory names in captured diagnostics vary.
- Command: `python tools/wwise_localized_akpk_hirc_census.py --jobs 4 --cache .tmp/wwise-localized-akpk-hirc-cache.jsonl`

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related experiments: [EXP-0130 AKPK table census](EXP-0130-localized-akpk-container-census.md), [EXP-0131 WEM decode census](EXP-0131-localized-akpk-wem-decode-census.md), EXP-0077–0081 PCK Wwise catalogs
- Open questions: Independent AKPK range validation for this extension cohort; compare bank HIRC IDs and media references to existing PCK/DIDC/WEM catalogs; determine runtime bank selection and playback with a separately recorded runtime experiment.
