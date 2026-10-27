---
id: EXP-0078
title: Exact-build Wwise HIRC container child and event-to-sound paths
experiment_status: done
claim_status: observed
build: "10256413"
question: "Can explicit ulChildID relations in parsed Wwise container HIRC objects extend same-bank event/action references to Sound media records?"
---

# EXP-0078 — Exact-build Wwise HIRC container child and event-to-sound paths

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: extend [EXP-0077](EXP-0077-wwise-bank-hirc-and-media-link-census.md) by extracting `ulChildID` values from parsed HIRC container objects, joining those IDs only within the same bank, and traversing event/action target IDs through those child relations to `CAkSound` media rows.
- Exclusions: no joins across banks, indirect/native event invocation, runtime playback, every Wwise object relationship, or WEM payload extraction/decoding. The result covers only `ulChildID` edges emitted by the pinned wwiser parser in the seven observed HIRC object types.
- Tooling: the same pinned toolchain and hash/build checks as EXP-0077, with the expanded [`wwise_bank_hirc_census.py`](../tools/wwise_bank_hirc_census.py) generator.
- Outputs: [extended HIRC edges](../research/builds/BUILD-STEAM-10256413/wwise-hirc-edges-with-container-children.csv), [container-inclusive event/HIRC/Sound paths](../research/builds/BUILD-STEAM-10256413/wwise-event-hirc-sound-paths.csv). The EXP-0077 [base edge catalog](../research/builds/BUILD-STEAM-10256413/wwise-hirc-edges.csv) continues to exclude `container_child` rows.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256.
2. Reuse the 504 exact-build bank XML dumps generated under EXP-0077. Extract every `ulChildID` field under each top-level HIRC object that has a parsed `ulID`; retain the owning object type and ID.
3. Add edges only when parent and child IDs resolve in the same bank's HIRC object-ID map. Separately keep unknown/cross-bank target candidates in the extended edge catalog.
4. For each same-bank event→action→target chain, recursively follow same-bank `ulChildID` edges until reaching `CAkSound`. Guard cycles per path and append media source IDs and the EXP-0077 DIDX/PCK-WEM matches.
5. Regenerate catalogs with `python tools/wwise_bank_hirc_census.py --reuse-xml` after the original 503-bank parser run; verify EXP-0077 base edge row count remains unchanged.

## Observations

- The 503 PCK banks contain 9,786 parsed nonzero `ulChildID` edges across seven HIRC object types: `CAkRanSeqCntr` 3,823; `CAkActorMixer` 1,877; `CAkMusicRanSeqCntr` 1,499; `CAkMusicSegment` 1,125; `CAkLayerCntr` 738; `CAkSwitchCntr` 589; `CAkMusicSwitchCntr` 135.
- All 9,786 child IDs resolve to a HIRC object ID within their owning bank. No cross-bank resolution was needed for these child edges.
- The expanded static edge catalog has 24,904 rows: the 15,118 base EXP-0077 event/action/target/sound-media edges plus 9,786 container-child edges. The separate EXP-0077 base catalog remains 15,118 rows.
- Recursive same-bank traversal yields 8,800 distinct event/action/child-chain/Sound/media-source rows across 445 PCKs (264 base-game and 181 DLC) and 1,832 `(source PCK, event ID)` pairs. The direct-target EXP-0077 subset remains 1,696 rows. HIRC object-ID chain lengths range from one to six; the maximum observed nesting is five container links before the Sound node.
- Of the 8,800 paths, 6,588 refer to a media ID in the same bank's DIDX index, 2,136 match a WEM filename in the same PCK, with three rows matching both; 79 path rows have neither same-bank DIDX nor same-PCK WEM match. These are path-row counts, so the 79 rows can refer to repeated Sound/media IDs reached from different events.
- EXP-0077's pre-partition count of 1,625 locally unresolved action target values includes 1,007 zeros. EXP-0080 separates those values: 618 nonzero targets remain locally unresolved, with 526 corpus ID candidates and 92 without; this traversal does not assume candidates are valid joins.

## Interpretation and claim limits

- **Observed:** parsed `ulChildID` field values form exact same-bank HIRC object-ID relations for all 9,786 recorded edges. Following these IDs extends the event/action graph to 8,800 parser-derived Sound/media paths.
- **Inferred, narrow:** the observed child edges are likely Wwise container membership relations because of their parser field names, owning HIRC object types, and exact local ID matches. This is not proof that those objects are active or selected during gameplay.
- **Unknown:** runtime loading/selection, conditions such as switch/state values and probability/sequence choices, cross-bank target semantics, missing media cases, and payload audio content.
- **Limit:** this covers explicit `ulChildID` relations from seven parsed types. It does not traverse every Wwise graph/reference field and is not a playback simulation or runtime reachability result.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0077 BNK HIRC/media census](EXP-0077-wwise-bank-hirc-and-media-link-census.md)
- [Pinned wwiser source](https://github.com/bnnm/wwiser/tree/08e937b649bc7007c234bbd59e34a41d5eef3b38)
