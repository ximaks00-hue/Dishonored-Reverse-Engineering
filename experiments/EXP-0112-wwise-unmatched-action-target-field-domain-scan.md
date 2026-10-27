---
id: EXP-0112
title: Wwise unresolved action target alternate field-domain scan
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do the 92 nonzero action target IDs without parsed HIRC ulID candidates occur as values in other fields in the parsed BNK XML corpus?
---

# EXP-0112 — Wwise unresolved action target alternate field-domain scan

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: search all XML field values in the pinned EXP-0077/0078 parser corpus for the 27 nonzero target IDs from the 92 action-target rows that have no HIRC `ulID` candidate, excluding the source `ulTargetID` field itself. Keep field name, nearest XML object type, and source bank.
- Exclusions: no interpretation of numeric equality as a reference, no runtime loading/execution, and no claim that the parser exposes every possible ID namespace or field.
- Durable outputs: [per-target summary](../research/builds/BUILD-STEAM-10256413/wwise-action-target-unmatched-domain-summary.csv), [field/package matches](../research/builds/BUILD-STEAM-10256413/wwise-action-target-other-field-id-matches.csv), [edge-level matches](../research/builds/BUILD-STEAM-10256413/wwise-action-target-unmatched-domain-edges.csv), and [count summary](../research/builds/BUILD-STEAM-10256413/wwise-action-target-unmatched-domain-summary.json).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, EXP-0080, EXP-0079, and build record; verify the build identity.
2. Select `action_target` rows from `wwise-hirc-edges.csv` with `to_type=unknown_or_cross_bank`, nonzero `to_id`, and zero `global_candidate_count`. Confirm the input is 92 rows / 27 target values.
3. Use the 503 numbered pinned wwiser XML files plus standalone `Init.bnk` XML from EXP-0077. Match each PCK XML's parsed bank ID to the saved bank-summary row; rely on EXP-0077 for the hash-checked PCK/toolchain provenance and confirm the executable identity against the build manifest.
4. Search all XML `field.value` strings for the target values; exclude `ulTargetID` occurrences, associate each match with its nearest enclosing object type and package, and preserve source action edges separately.
5. Run `python tools/wwise_unmatched_action_target_domains.py` to regenerate tables and assert the 92/27 denominators, field/domain groups, and matched/unmatched edge counts.

## Observations

- The input remains the corrected EXP-0080 set of 92 nonzero unresolved action-target edges across 27 distinct IDs; none has an exact HIRC object `ulID` candidate in the parsed corpus.
- Searching all field values in 503 PCK-bank XMLs plus `Init.bnk` found non-`ulTargetID` field-value matches for 10 of the 27 target IDs. Those 10 IDs account for 57 of the 92 source action edges. The remaining 17 IDs (35 edges) have no other matching field value in this XML corpus.
- Six target IDs match `RTPCID` fields in `RTPC` objects, accounting for all 21 `CAkActionSetGameParameter` edges in the unresolved set. Seventeen of those edges have an `RTPCID` value match in the same PCK; the other four match only in other parsed packages. The same six values also occur as `RTPC_ID` in `RTPCRamping` fields in `Init.bnk`. The parser output thus shows exact numeric matches across these fields; it does not establish that the action target semantically references an RTPC.
- Four other target IDs match `ulNodeID` fields in `AkSwitchNodeParams` objects, accounting for 36 edges: 18 `CAkActionMute` and 18 `CAkActionStop` rows. The 18 Stop edges have same-PCK matches; the 18 Mute edges match only field values in another parsed PCK. The XML field-owner/package catalog contains seven distinct `ulNodeID`/object-type/package tuples for these IDs. These values were not recorded as HIRC `ulID` matches in EXP-0080.
- A focused parent-chain inspection of the seven `ulNodeID` XML field occurrences found that each is under `AkSwitchNodeParams` → `rParams` → `SwitchCntrInitialValues` → `CAkSwitchCntr`. In `Bank_DLC06_Amb_Level_SlaughterInt.pck`, three IDs occur twice each in this nested structure; in `Bank_Amb_LVL_E3.pck`, the fourth occurs once. These are XML occurrences in a switch-container parameter subtree, not additional parsed HIRC `ulID` objects. The equality remains a candidate numeric association only; the inspection does not establish whether the representation is duplicated serialization or an intentional data relationship.
- The 35 edges without any other field-value match consist of 23 `CAkActionStop`, 10 `CAkActionSetAkProp`, one `CAkActionPause`, and one `CAkActionResume`.
- Field-owner-package tuple counts are: 15 `RTPCID`/`RTPC`, six `RTPC_ID`/`RTPCRamping`, and seven `ulNodeID`/`AkSwitchNodeParams`. These counts are deduplicated field/type/package tuples, not raw XML-field occurrence counts.

## Interpretation and claim limits

- **Observed:** 57 unresolved edges share exact numeric values with other parsed XML fields: 21 `CAkActionSetGameParameter` edges align numerically with six RTPC IDs; 36 Stop/Mute edges align with four switch-node IDs. Thirty-five have a same-PCK field match and 22 match only fields in another PCK/Init XML. The match is an alternate-field-domain candidate set, distinct from the earlier HIRC `ulID` candidate search.
- **Inferred, narrow:** the `CAkActionSetGameParameter`/`RTPCID` equalities are consistent with these target IDs using a game-parameter identifier domain rather than an HIRC object `ulID`. The parser XML alone does not prove the engine's target-resolution rule.
- **Unknown:** whether `ulNodeID` matches represent intended action targets or merely reused numeric values; why 17 IDs have no other field match; whether any of these records execute or resolve at runtime.
- **Limit:** the scan covers named scalar field values present in the retained pinned parser XML for 503 PCK banks and `Init.bnk`; it does not scan raw serialized payload bytes or other identifier domains that wwiser did not label.

## Reproduction

The corpus XML is generated and its tool/build provenance is recorded in EXP-0077. After confirming those XML files and the EXP-0077 edge/summary outputs exist, run:

```powershell
python tools/wwise_unmatched_action_target_domains.py
```

The script checks saved build identity, verifies all 503 PCK XML bank IDs against the parse summary, and regenerates the four output catalogs.

## Links

- [EXP-0080 corrected zero/nonzero target denominator](EXP-0080-wwise-action-target-zero-id-audit.md)
- [EXP-0079 cross-bank HIRC ID candidates](EXP-0079-wwise-cross-bank-action-target-id-candidates.md)
- [EXP-0077 HIRC parse corpus](EXP-0077-wwise-bank-hirc-and-media-link-census.md)
- [Domain scan tool](../tools/wwise_unmatched_action_target_domains.py)
