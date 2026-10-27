---
id: EXP-0139
title: Native class-table targets joined to UELib NativeFlag token-zero exports
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do the 332 raw class-table name/target pairs from EXP-0138 match exact UELib native function exports with NativeToken zero, and how do their executable targets relate to the indexed function set?"
---

# EXP-0139 — Native class-table targets joined to UELib NativeFlag token-zero exports

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: join all 332 EXP-0138 decoded `.rdata` exec names to UELib `Function` exports from the eight EXP-0057 function-bearing base packages; check package hashes against the 13,623-row build manifest; relate the 329 indexed target starts to the EXP-0072 subsystem baseline and EXP-0128 manual body-review overlay.
- Exclusions: no function-body review, subsystem assignment, full table enumeration, runtime observation, proof of runtime ownership, or NativeToken dispatch claim. The three `.text` targets not indexed as functions or inside indexed ranges remain unresolved.
- Inputs: EXP-0138 raw pointer CSV; UELib census JSONL files generated from the EXP-0057 package set; exact-build manifest and function index; EXP-0072 triage and EXP-0128 additive overlay.
- Durable outputs: [332-row UELib join](../research/executable/evidence/EXP-0139-native-class-table-uelib-zero-token-join.csv), [summary](../research/executable/evidence/EXP-0139-native-class-table-uelib-zero-token-join-summary.json), and [254-address candidate overlay](../research/executable/evidence/function-triage/native-class-table-handler-candidates-EXP-0139.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record. Require the recorded build ID and executable SHA-256.
2. Read all eight UELib `*.functions.jsonl` files. Rehash each distinct source UPK against the manifest, verify the source hash recorded in every row, and record each JSONL file hash.
3. Require the expected 4,772-row function corpus, including 2,572 `NativeFlag` rows and 2,383 `NativeFlag` plus zero-token rows.
4. For every EXP-0138 name, derive the owner spelling from its class key (bare, `A`-prefixed, or `U`-prefixed), match one exact owner/exec export, and require an exact UELib `Function'<package>.<class>.<method>'` object path.
5. Require each of the 332 joined exports to have `NativeFlag=true` and `NativeToken=0`; preserve package, export, declaration, JSONL source/hash/line, and raw target evidence.
6. Group the 329 exact function-index target starts by address. Require all 254 unique addresses to remain in EXP-0072's `unknown` subsystem bucket and absent from the EXP-0128 manual body-review overlay. Keep this candidate layer separate; do not modify the baseline or manual overlay counts.

## Observations

- All 332 raw class-table name/target records have a unique exact owner/name join to a UELib Function object path. Every matched record is `NativeFlag=true`, `NativeToken=0`; none has a nonzero token.
- These 332 exports are a subset of 2,383 NativeFlag/token-zero records among 4,772 UELib function rows (13.93% of the zero-token subset). The eight JSONL outputs cover seven packages represented by these matches; every distinct package source hash matches the manifest.
- 329 target edges match exact starts in the 72,437-row function index, collapsing to 254 unique indexed addresses. Thirty-one target addresses are associated with more than one class/method edge; the maximum observed multiplicity is ten. These shared associations are candidate cluster links, not proof of common behavior or ownership.
- Three joined name/target records point into `.text` but match neither a function-index start nor any indexed function range.
- All 254 indexed target addresses are in the EXP-0072 `unknown` bucket, do not overlap its 439 symbol-name candidate addresses, and do not overlap the 28 EXP-0124–0128 manually reviewed bodies.
- This is a separate additive evidence overlay: it adds 254 static role-candidate rows (461 + 254 = 715 if counted across these distinct overlays), but the EXP-0128 unresolved-unknown count remains 71,976. This pass adds zero body-reviewed or runtime-verified functions.

## Interpretation and claim limits

- **Confirmed static label/export join:** all 332 raw class/method names match one exact UELib Function object path, and the matched exports carry `NativeFlag=true`, token zero.
- **Confirmed static address join:** 329 raw `.text` targets equal exact indexed function starts. The other three are not covered by indexed function starts or ranges.
- **Observed candidate relation:** 254 distinct indexed functions are associated with these class/method records and remain unreviewed by body. Repeated target addresses connect multiple class/method labels and provide a prioritization cluster.
- **Unknown:** whether these pointers are consumed as a native dispatch table, why three targets are unindexed, which class owns each implementation at runtime, what any function does, and whether any path is reachable in the selected game session.
- Function indexing, NativeFlag metadata, and matching strings do not establish runtime dispatch or semantic understanding. Do not move these records into a reviewed-function count or assign a subsystem from this join alone.

## Reproduction and limitations

From the repository root, using the ignored EXP-0057 UELib census output:

```powershell
python tools\native_class_table_zero_token_join.py --jsonl-root assets\extracted\uelib-census\20261026-230210-253-c7ad73d8
```

The script gates on build/manifest identity, rehashes all matched package sources, verifies corpus and join denominators, and regenerates all three outputs. The census JSONL is a generated/ignored input; its file hashes and package source hashes are recorded in the summary. The overlay is a static candidate list only; function bodies and runtime behavior remain unknown.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Raw pointer validation: [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- Parent class/key extraction: [EXP-0137](EXP-0137-native-class-registration-group-uelib-join.md)
- UELib function census and NativeToken analysis: [EXP-0057](EXP-0057-engine-upk-function-decompile-census.md), [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- Existing additive body review: [EXP-0128](EXP-0128-audio-request-queue-submission.md)
