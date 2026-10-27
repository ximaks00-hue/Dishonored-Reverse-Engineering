---
id: EXP-0080
title: Wwise action target zero-ID audit and corrected cross-bank denominator
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do zero-valued HIRC ulTargetID fields belong in the unresolved local/cross-bank object-reference denominator?"
---

# EXP-0080 — Wwise action target zero-ID audit and corrected cross-bank denominator

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: audit parser-derived `ulTargetID` values for all 4,805 action-target rows from EXP-0077/0078, isolate numeric zero values, and recompute the nonzero unresolved/cross-bank candidate denominator.
- Exclusions: no claim that zero means a runtime null operation in every Wwise action class; no runtime playback or invocation; no identification of non-HIRC ID namespaces absent from the object catalog.
- Tools/data: pinned wwiser XML dumps for 503 PCK BNKs plus `Init.bnk`; exact-build/hash-checked [`wwise_bank_hirc_census.py`](../tools/wwise_bank_hirc_census.py); outputs [base edge catalog](../research/builds/BUILD-STEAM-10256413/wwise-hirc-edges.csv) and [cross-bank candidate catalog](../research/builds/BUILD-STEAM-10256413/wwise-action-target-global-id-candidates.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify executable SHA-256.
2. In the current generated action-target edge rows, partition by raw `to_id == "0"`, same-bank HIRC object match, and nonzero local-unresolved value.
3. Reopen the pinned wwiser XML for each zero-valued action-target row and count action types and any separate `ulStateGroupID`/`ulTargetStateID` fields.
4. Regenerate the output catalogs with `python tools/wwise_bank_hirc_census.py --reuse-xml`; verify candidate rows exclude `zero_id_value` edges and all PCK hashes remain manifest-matched.

## Observations

- The corpus contains 4,805 parsed action `ulTargetID` fields: 1,007 are the literal numeric value `0`; 3,180 nonzero targets resolve to a same-bank HIRC object ID; 618 nonzero targets do not resolve in their own bank's parsed HIRC `ulID` map. These categories sum to the 4,805 total.
- The 1,007 zero-valued fields comprise 995 `CAkActionSetState`, nine `CAkActionSetAkProp`, one `CAkActionPause`, one `CAkActionResume`, and one `CAkActionStop` record. The current edge catalog labels these as `zero_id_value`, not `unknown_or_cross_bank`.
- All 995 `CAkActionSetState` records also expose a nonzero `ulStateGroupID`; 719 have a nonzero `ulTargetStateID`, while 276 have `ulTargetStateID=0`. These are distinct parsed fields from `ulTargetID`. This supports separating a zero `ulTargetID` value from an unresolved HIRC object ID; it does not define engine runtime behavior.
- After removing zero-valued target IDs from the nonzero unresolved denominator, 526/618 edges have exact same-ID candidates elsewhere in the 504-bank HIRC object catalog, and 92 edges have none. The 526 candidate edges contain 90 distinct target-ID values; the 92 no-candidate edges contain 27 distinct values. Candidate rows total 4,090 because repeated IDs in multiple banks remain separate rows. Of the 526 edges, 320 IDs occur exactly once and 206 repeat across multiple banks; all observed occurrences for each ID retain one HIRC object type in this corpus.
- The candidate CSV contains 526 distinct source-edge keys and excludes all 1,007 zero-valued target fields. The base HIRC edge catalog remains 15,118 rows; zero-valued edges remain available with explicit `zero_id_value` classification.

## Interpretation and claim limits

- **Observed:** the previous 1,625 count of locally unresolved action-target rows included 1,007 numeric-zero target values. The corrected nonzero unresolved count is 618 edges; 526 edges have candidates and 92 edges (27 distinct target IDs) lack a parsed HIRC object-ID match.
- **Inferred, narrow:** the `CAkActionSetState` entries likely encode state changes through the separate state-group/state fields while their generic target ID is zero. The parser output alone does not prove how the engine handles this case.
- **Unknown:** semantics of zero for other action classes; meaning of the 92 nonzero IDs with no HIRC object match; whether cross-bank candidates are actually loaded and consumed; runtime order/conditions.
- **Correction trail:** this audit refines the denominator in EXP-0077 and EXP-0079. Their earlier raw count remains reproducible as the pre-partition count; use this experiment for current zero/nonzero classification.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0077 BNK HIRC/media census](EXP-0077-wwise-bank-hirc-and-media-link-census.md)
- [EXP-0079 cross-bank target candidates](EXP-0079-wwise-cross-bank-action-target-id-candidates.md)
