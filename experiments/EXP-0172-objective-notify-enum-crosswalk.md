---
id: EXP-0172
title: Objective notification dispatcher and enum crosswalk
experiment_status: done
claim_status: inferred
build: "10256413"
question: "Can the exact-build objective notification switch be mapped to named event handlers and enum values using the retail export and editor SDK?"
---

# EXP-0172 — Objective notification dispatcher and enum crosswalk

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build static dispatcher `FUN_00AD4F60`, its six direct numeric branches, `FUN_00BBE6A0` helper, and candidate name/value cross-checks from a local 2013 native-function export, a 2012→2013 matcher, and the DFSDK/editor class declaration.
- Exclusions: no Ghidra renaming; no original implementation source; no runtime execution or event occurrence; no claim that editor SDK enum provenance alone proves retail serialized/runtime meaning.
- External provenance: the local third-party snapshot has no recorded Git commit. The CSV hashes for its exports/matcher are preserved in [EXP-0163 provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json). The enum declaration was read from `DishonoredObjectivesComponent.uc` and independently appears in generated `DishonoredGameEngineShims.h` in that snapshot.
- Durable exact-build decompile outputs: [dispatcher 00AD4F60](../knowledge/cache/decompiles/00AD4F60.json), [gate/helper 00BBE6A0](../knowledge/cache/decompiles/00BBE6A0.json), [code 0 00ACC050](../knowledge/cache/decompiles/00ACC050.json), [code 1 00AD0E00](../knowledge/cache/decompiles/00AD0E00.json), [code 2 00ACC0E0](../knowledge/cache/decompiles/00ACC0E0.json), [code 3 00AD1080](../knowledge/cache/decompiles/00AD1080.json), [code 4 00AD1220](../knowledge/cache/decompiles/00AD1220.json), [code 5 00AD1320](../knowledge/cache/decompiles/00AD1320.json), and [task-completion callback 00ACBC70](../knowledge/cache/decompiles/00ACBC70.json). These are generated local files, not public Git source of truth.

## Procedure

1. Read the registered exact-build identity and resolve each VA in `research/executable/functions.csv`.
2. Read-only decompile `FUN_00AD4F60` and each of its six direct branch destinations; confirm the switch constants in exact-build pseudocode.
3. Join each 2013 export row to `match_2012_2013.csv` by RVA and preserve method, ratio, and both function sizes.
4. Compare branch order with the `EDisObjectiveChangedNotifyType` enum declaration in the editor SDK and generated shim. Treat this as a cross-reference, not retail execution evidence.
5. Review helper gating and one task completion follow-on to constrain what a numeric code means structurally.

## Observations

The exact-build dispatcher at `0x00AD4F60` has six explicit branches:

| Code | Exact-build target | Target size | 2013 export / candidate name | Matcher method | Ratio | 2012/2013 sizes |
| ---: | --- | ---: | --- | --- | ---: | ---: |
| 0 | `0x00ACC050` | 140 | `UDishonoredObjectivesComponent::OnGotObjectiveNotify` | callee | 0.982 | 140/140 |
| 1 | `0x00AD0E00` | 377 | `UDishonoredObjectivesComponent::OnCompletedObjectiveNotify` | callee | 0.714 | 401/377 |
| 2 | `0x00ACC0E0` | 124 | `UDishonoredObjectivesComponent::OnFailedObjectiveNotify` | callee | 0.980 | 124/124 |
| 3 | `0x00AD1080` | 401 | `UDishonoredObjectivesComponent::OnNewTaskNotify` | callee | 0.684 | 625/401 |
| 4 | `0x00AD1220` | 254 | `UDishonoredObjectivesComponent::OnTaskUpdatedNotify` | callee | 0.990 | 254/254 |
| 5 | `0x00AD1320` | 520 | `UDishonoredObjectivesComponent::OnTaskStateChangedNotify` | callee | 0.642 | 718/520 |

- The exact-build dispatcher takes an integer-like first argument and object pointer second, switching only on values 0–5; each case calls one distinct handler with the object and returns.
- The local editor SDK enum lists, in ordinal order: `DOCNET_GotObjective=0`, `DOCNET_CompletedObjective=1`, `DOCNET_FailedObjective=2`, `DOCNET_NewTask=3`, `DOCNET_TaskUpdated=4`, `DOCNET_TaskStateChanged=5`, followed by `DOCNET_MAX=6`. The generated shim repeats the same assignments.
- The external 2013 function export reports `OnObjectiveChangedNotify(enum EDisObjectiveChangedNotifyType, UObject*)` at VA `0x00AD4F60` and `DisSendObjectiveChangedNotify(enum EDisObjectiveChangedNotifyType, UObject*)` at VA `0x00BBE6A0`. The dispatcher matcher row is `bytes`, ratio `1.000`, sizes `120/96`; the helper row is `callee`, ratio `0.933`, sizes `37/37`.
- The exact-build helper at `0x00BBE6A0` gates dispatch on global pointer `DAT_0145F614` and nonzero field `+0x6F8`, then calls the dispatcher with the numeric code and object.
- Exact-build handlers 3 and 5 are structurally consistent with the prior EXP-0171 observations. Handler 1 also iterates the global listener array and calls virtual slot `+0x18C` for filtered listeners; the name-to-handler crosswalk quality differs by row, as shown above.

## Interpretation

- **Observed:** the exact-build dispatcher has six numeric routes (0–5). The editor SDK's enum contains six named values with matching ordinals, and local 2013 export rows assign the dispatcher/helper signatures to the corresponding named enum type.
- **Inferred, high-quality candidates:** code 0, 2, and 4 handler names have matcher ratios at or above 0.980 and equal 2012/2013 sizes. Code 1 has ratio 0.714 and a 24-byte size difference; code 3 has ratio 0.684 and a 224-byte difference; code 5 has ratio 0.642 and a 198-byte difference. These three labels are weaker candidates and must not be treated as independently proven function identities.
- **Inferred, enum crosswalk:** the combined dispatcher order, 2013 function declarations, and SDK enum order support mapping the six exact-build numeric routes to the six `DOCNET_*` labels. This increases confidence in the interpretation of codes 3/5 in EXP-0171, but does not establish runtime reachability or prove every candidate handler body is identical to its named donor.
- **Unknown:** why the helper requires `DAT_0145F614+0x6F8`; what concrete observer/listener objects receive events; whether any specific Boyle retail Kismet node reaches these functions; and whether the SDK's enum declaration is byte-for-byte current for all retail runtime paths.
- **Limit:** external native exports are a local snapshot without a known commit. Matcher quality is preserved instead of collapsed into one confidence value. Ghidra output is decompilation of machine code, not source.

## Reproduction

1. Confirm EXE SHA-256 in the registered build record.
2. Resolve the six target VAs/sizes in `research/executable/functions.csv`.
3. Read-only decompile `0x00AD4F60` and verify each case's target.
4. Reproduce the external joins with `functions_2013.csv` and `match_2012_2013.csv`; preserve the stated source hashes from EXP-0163.
5. Compare the enum values in `DishonoredObjectivesComponent.uc` and `DishonoredGameEngineShims.h`; retain editor provenance as a separate evidence source.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Task-state dispatcher implementation: [EXP-0171](EXP-0171-task-state-event-dispatch.md)
- Task-state field/setter: [EXP-0170](EXP-0170-task-state-native-storage-crosswalk.md)
- Donor/source provenance limits: [EXP-0163 crosswalk provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json)
- Boyle static candidate graph: [EXP-0169](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
