---
id: EXP-0079
title: Exact-build Wwise cross-bank action target ID candidates
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Among Wwise action targets unresolved within their source bank, which IDs exactly match HIRC object IDs in another parsed bank, and how ambiguous are those matches?"
---

# EXP-0079 — Exact-build Wwise cross-bank action target ID candidates

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: use the EXP-0077/0078 parsed HIRC object-ID catalog to compare exact target IDs for action edges that do not resolve within their own bank. Preserve every cross-bank object row as a separate candidate.
- Exclusions: no promotion of numeric equality to a confirmed runtime reference; no joins across non-HIRC ID namespaces, HIRC objects without a parsed `ulID`, or unparsed assets; no Wwise runtime loading or invocation evidence.
- Inputs/tool: [EXP-0077/0078 HIRC edge and object catalogs](EXP-0077-wwise-bank-hirc-and-media-link-census.md), pinned parser workflow [generator](../tools/wwise_bank_hirc_census.py).
- Output: [wwise-action-target-global-id-candidates.csv](../research/builds/BUILD-STEAM-10256413/wwise-action-target-global-id-candidates.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256.
2. Select `action_target` rows marked unresolved in their source bank (`to_type=unknown_or_cross_bank`) from the EXP-0077 base edge set.
3. For each target ID, enumerate exact `object_id` rows from all 503 PCK BNKs plus standalone `Init.bnk`. Record source action/bank, candidate bank/object type, total ID occurrence count, and candidate bank count.
4. Compare candidate object types across all records for each numeric target ID. Preserve ambiguity rather than choosing an arbitrary bank.

## Observations

- The original corpus query reported 1,625 action-target edges without a same-bank HIRC object match. [EXP-0080](EXP-0080-wwise-action-target-zero-id-audit.md) found that this pre-partition count includes 1,007 literal-zero `ulTargetID` values; the corrected nonzero unresolved denominator is 618. The local join alone does not prove that an ID is absent or invalid.
- Of the 618 nonzero locally unresolved source edges, 526 have at least one exact numeric ID match in the other parsed bank-object records; the candidate table contains 4,090 edge-to-object rows. These edges comprise 263 `CAkActionStop`, 173 `CAkActionMute`, 86 `CAkActionSetAkProp`, two `CAkActionPause`, and two `CAkActionResume` records.
- The matches involve 90 distinct target-ID values. In all 90 cases, every corpus occurrence has the same HIRC object type for that numeric ID; no target ID is associated with multiple candidate object types in this parsed corpus.
- For 320/526 source edges, the target ID occurs exactly once in the full 504-bank object-ID corpus, and its candidate is in a different source PCK. For the remaining 206 source edges, the ID occurs in multiple bank records (up to 113); these repeated records retain one object type but can refer to duplicated bank content, so the owning bank remains ambiguous.
- Twenty-three source edges have an exact-ID candidate row in standalone `Init.bnk`. Example: `CAkActionSetAkProp` in `Bank_AI_Overseer_Music.pck` targets ID `686520729`; the unique catalog occurrence is a `CAkBus` record in `Init.bnk`. This is exact parser-ID equality, not independent proof that the action references that bus at runtime.
- The remaining 92 nonzero locally unresolved action-target edges have no exact `ulID` match in the 503 PCK BNKs plus `Init.bnk` catalog. Several unresolved action classes may target state, parameter, or other identifier domains not represented as HIRC `ulID`; this corpus check does not distinguish those semantics.

## Interpretation and claim limits

- **Observed:** the candidate table records exact numeric ID equality between 526 locally unresolved action target fields and one or more HIRC object ID records in a different PCK/Init bank. Candidate type is consistent per ID within this corpus.
- **Inferred, narrow:** the 320 single-occurrence matches are stronger cross-bank target candidates than repeated IDs, based on the `ulTargetID` field and unique matching HIRC object ID. They remain candidates because ID namespace/consumer semantics and runtime bank co-loading are unverified.
- **Unknown:** whether the 206 repeated-ID groups represent intentional shared objects, duplicated bank content, or another ID reuse pattern; whether the 92 remaining nonzero targets use a different object-ID namespace; runtime resolution/load order and invocation.
- **Correction:** EXP-0080 establishes that the candidate file excludes 1,007 zero-valued target fields and compares candidates against 618 nonzero locally unresolved edges; use its totals for the current cross-bank denominator.
- **Limit:** exact numeric equality and type consistency do not prove runtime cross-bank resolution. The index covers only parsed HIRC objects with `ulID` in the 503 PCK BNKs and `Init.bnk`.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0077 BNK HIRC/media census](EXP-0077-wwise-bank-hirc-and-media-link-census.md)
- [EXP-0078 container child paths](EXP-0078-wwise-hirc-container-child-paths.md)
