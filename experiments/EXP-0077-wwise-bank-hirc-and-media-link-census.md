---
id: EXP-0077
title: Exact-build Wwise BNK HIRC and media-link census
experiment_status: done
claim_status: observed
build: "10256413"
question: "What bank, HIRC, event/action/sound, and media-index relations can be parsed from all Wwise BNKs embedded in the exact-build PCK set and the standalone Init.bnk?"
---

# EXP-0077 — Exact-build Wwise BNK HIRC and media-link census

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: extract the one BNK listed for each of 503 PCKs, parse each BNK and the separate installed `Init.bnk`, derive HIRC event/action/target and sound/media ID relations, and compare Sound media IDs to same-bank DIDX entries and PCK WEM paths.
- Exclusions: no WEM payload extraction/decoding, game launch, proof of runtime bank loading or event invocation, complete cross-bank object resolution, complete traversal through nested containers, or TFC/AKMAP parsing. `_excluded_coop_project/` was not accessed.
- Tools: QuickBMS 0.12.0 executable SHA-256 `FF812D38E22AEA0CC2CDC13C5C91CA34FAE4443AB12987002105BE6BAB3F4948`; Wwise PCK BMS SHA-256 `4459C0A4C354A92DCAD335599C389E8296908BD8B38FB128BD4C505AEAEE6B5D` (the script previously recorded in EXP-0065); [wwiser at pinned commit `08e937b649bc7007c234bbd59e34a41d5eef3b38`](https://github.com/bnnm/wwiser/tree/08e937b649bc7007c234bbd59e34a41d5eef3b38), version `v20260808`; Python 3.12.10; generator [`wwise_bank_hirc_census.py`](../tools/wwise_bank_hirc_census.py).
- Outputs: [bank parse summary](../research/builds/BUILD-STEAM-10256413/wwise-bank-hirc-summary.csv), [HIRC object IDs/types](../research/builds/BUILD-STEAM-10256413/wwise-hirc-objects.csv), [HIRC relation edges](../research/builds/BUILD-STEAM-10256413/wwise-hirc-edges.csv), [Sound/media joins](../research/builds/BUILD-STEAM-10256413/wwise-sound-media-joins.csv), and [direct event-to-sound-to-media paths](../research/builds/BUILD-STEAM-10256413/wwise-event-direct-sound-paths.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the local executable SHA-256.
2. Use the EXP-0065 PCK entry catalog (503 BNKs, one per PCK) and extract only `.bnk` entries with QuickBMS. The generator verifies every PCK's current size and SHA-256 against `files.csv`, verifies extracted BNK byte counts against the entry catalog, and verifies standalone `Init.bnk` size/SHA-256 against the same manifest.
3. Parse each extracted bank and `Init.bnk` to wwiser XML, then generate the five CSV outputs. No WEM media payload is extracted.
4. Re-run `python tools/wwise_bank_hirc_census.py` to extract and parse the corpus. `--reuse-xml` reproduces the CSV derivation from retained ignored XML dumps without rerunning wwiser.

## Observations

- All 503 PCK source paths are unique and match the current build manifest size/SHA-256. All 503 embedded BNKs match the catalog byte size and parsed without error. Standalone `Init.bnk` also matches the manifest size/hash and parses successfully. The 504 parsed banks (503 PCK + Init) report Wwise bank generator version 65.
- The 503 PCK banks contain 20,946 HIRC objects, 2,497 `CAkEvent` records, 4,805 `CAkAction*` records, 5,508 `CAkSound` records, and 3,265 DIDX media-index rows. `Init.bnk` adds 95 HIRC objects (27 `CAkBus`, 55 `CAkFxShareSet`, 13 `CAkState`) and no events/actions/sounds/DIDX rows. The object-ID CSV contains 19,401 HIRC object rows with a parsed `ulID`; it is not the total HIRC-object count.
- The extracted static relation catalog contains 4,805 event→action rows, 4,805 action→target rows, and 5,508 Sound→media-source rows (15,118 total). All 4,805 event action IDs match an action-object ID in the same bank. The original partition counted 3,180 same-bank target matches and 1,625 rows without a local match; EXP-0080 separates 1,007 literal-zero `ulTargetID` values from 618 nonzero locally unresolved targets.
- EXP-0080 corrects the nonzero unresolved partition: 526 of 618 edges have exact-ID object candidates in the 503-bank-plus-Init object catalog, including 23 source edges with a candidate in `Init.bnk`; 92 edges (27 distinct target IDs) have no exact object-ID candidate. Cross-bank candidates may be ambiguous or accidental ID collisions; they are not promoted to confirmed links.
- Of 5,508 Sound media-source IDs, 4,297 occur in a DIDX row of the same bank and 1,172 match a numeric `.wem` name in the same PCK (one ID occurs in both groups). Thus 5,468/5,508 have an exact same-bank index or same-PCK WEM name match. The other 40 have no exact DIDX ID in the full 504-bank corpus and no exact WEM name in the full 1,908-entry WEM catalog; all 40 have `fileID=0`, `StreamType=0`, `bExternallySupplied=0` in the parser output and occur across 16 PCKs.
- A strict same-bank ID join produced 1,696 direct paths of `CAkEvent → Action → CAkSound → media source`. Of these paths, 1,161 media IDs occur in the bank's DIDX and 535 match a WEM entry in the same PCK. This is a direct-reference subset; actions targeting containers and deeper child traversal are not represented in that path file.
- The five output tables record per-source PCK/build identity, parse statuses, IDs and types, extracted-bank hashes, local/global ID candidate counts, and the exact WEM path matches. All 504 bank parse records have status `parsed`.

## Interpretation and claim limits

- **Observed:** the pinned parser produces structured HIRC rows for all 503 PCK banks and `Init.bnk`; explicit event/action/sound/media IDs form the recorded static relations above.
- **Inferred, narrow:** same-bank DIDX IDs and same-PCK WEM numeric names are likely resource references represented by the corresponding parsed fields. The inference follows parser field labels and exact IDs/paths, not runtime observation.
- **Unknown:** whether these banks load in any particular gameplay state, event IDs/names and invocation conditions, whether nonzero unresolved global target IDs are valid external references, semantics of zero target fields, 40 unmatched source IDs, nested container traversal coverage, WEM decoding/content, and runtime bank/language selection.
- **Correction:** use [EXP-0080](EXP-0080-wwise-action-target-zero-id-audit.md) for the current zero/nonzero action-target partition and cross-bank candidate denominator; the original 1,625 value is retained as the pre-partition local-unresolved count.
- **Limit:** wwiser output is third-party parser/reverse-engineering output, not original Wwise source or independent validation of every field. HIRC IDs and call-like relations are not runtime execution proof. No audio is played or interpreted perceptually.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0065 PCK/Bink parser census](EXP-0065-wwise-pck-and-bink-media-census.md)
- [EXP-0073 exact-build audio API probes](EXP-0073-exact-build-audio-api-function-probes.md)
- [EXP-0074 audio API helper trace](EXP-0074-exact-build-audio-helper-trace.md)
