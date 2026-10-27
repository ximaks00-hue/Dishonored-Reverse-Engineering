---
id: EXP-0173
title: Task-state field offsets and enum cross-check
experiment_status: done
claim_status: inferred
build: "10256413"
question: "Do the exact-build task-state reads/writes align with independently recorded reflected layouts and the available task-state enum?"
---

# EXP-0173 — Task-state field offsets and enum cross-check

- Date: 2026-10-27 (Europe/Kiev).
- Build under investigation: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: the exact-build task-state action/setter/getter from EXP-0170, the state-change dispatcher from EXP-0171/0172, retail reflected member offsets from a local CodeRed SDK dump, and the editor SDK task-state enum declaration.
- Exclusions: the CodeRed dump does not contain the exact-build EXE hash, so its offsets are corroborating retail-build evidence, not by themselves proof of identical executable identity. The editor enum is not treated as runtime execution evidence. No runtime trace or Kismet node reachability is claimed.
- External sources: `Dishonored_DumpedSDK_Retail` CodeRed dump parsed by the local Dishonored Recompiled project; its `sdk_dump.md` says it was captured from a running 2013 retail EXE. The exported C++ layouts and enum script are derived artifacts. The local source snapshot has no recorded Git commit; export and matcher hashes are preserved in [EXP-0163 provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json).
- Exact-build cache records: [00B86840](../knowledge/cache/decompiles/00B86840.json), [00AC17B0](../knowledge/cache/decompiles/00AC17B0.json), [00AC17A0](../knowledge/cache/decompiles/00AC17A0.json), [00AD4F60](../knowledge/cache/decompiles/00AD4F60.json), and [00AD1320](../knowledge/cache/decompiles/00AD1320.json). These are generated local files, not public Git source of truth.

## Procedure

1. Verify the registered target EXE SHA-256 and read the exact-build decompile outputs for action handler, setter, getter, dispatcher, and task-state handler.
2. Inspect the external CodeRed-derived retail layout declarations and their documented source/method.
3. Compare the exact-build raw field offsets with reflected field offsets for `UDisSeqAct_SetTaskState` and `UDishonoredTask_Base`.
4. Read the editor SDK enum declaration and compare its ordinal order with state values handled by the exact-build code and notification codes mapped in EXP-0172.
5. Keep the task-state enum and objective-notification enum as separate numeric domains.

## Observations

- Exact-build `FUN_00B86840` reads one byte at action receiver `+0xFC` and passes it with the task pointer into `FUN_00AC17B0`.
- Exact-build `FUN_00AC17B0` compares/writes one byte at task receiver `+0x5D`; exact-build `FUN_00AC17A0` reads that same byte.
- The external CodeRed-derived reflected layout declares `UDisSeqAct_SetTaskState::m_TaskState` at decimal offset 252 (`0xFC`) and `UDishonoredTask_Base::m_TaskState` at decimal offset 93 (`0x5D`). The generated class header marks the action layout as retail size 256 and task layout as retail size 124; the parsed layout documentation states that member offsets are `UProperty::Offset` values read from a running 2013 retail executable.
- The DFSDK `DishonoredTask_Base.uc` declares `EDisTaskState` in this order: `DTS_Inactive`, `DTS_Active`, `DTS_Completed`, `DTS_Failed`, `DTS_MAX`. With standard UE enum ordinals, the four states are candidates for values 0, 1, 2, 3 respectively; the declaration itself does not annotate explicit numeric assignments.
- Exact-build setter code dispatches objective notification code 3 when the new task-state byte is 1, and notification code 5 for every changed value.
- Exact-build objective dispatcher codes 0–5 align ordinally with the separate `EDisObjectiveChangedNotifyType` enum in the editor SDK and candidate native export. Thus task state value `1` and notification code `3` are distinct values from different enums.
- Exact-build code in the state-changed handler has special branches for task-state bytes 2 and 3. The byte-2 branch can inspect related task bytes and dispatch objective notification code 1 if its guard succeeds.

## Interpretation

- **Observed:** the exact-build code reads and writes the exact offsets assigned to `m_TaskState` by the independent reflected-layout dump. This provides strong structural corroboration that both fields are the task-state member, rather than arbitrary bytes at nearby offsets.
- **Inferred, state labels:** the editor SDK enum order supports interpreting task-state bytes 0/1/2/3 as Inactive/Active/Completed/Failed. This is a useful mapping hypothesis supported by offset agreement and code branches, but the enum declaration is a separate editor artifact and does not itself prove the 10256413 runtime meaning.
- **Inferred, transition notifications:** on a changed state, value 1 dispatches notification code 3 (candidate `DOCNET_NewTask`); every changed value dispatches code 5 (candidate `DOCNET_TaskStateChanged`). In the separate task-state domain, values 2 and 3 enter distinct follow-on branches. Keep the domains explicit: task-state `1` is not objective-notification `1`, and task-state `3` is not objective-notification `3`.
- **Inferred, completion aggregation:** the exact-build byte-2 branch can test task-state bytes across an array and, when its conditions pass, dispatch objective event code 1 (candidate `DOCNET_CompletedObjective`). This is a static aggregate path, not evidence that a specific objective completes in a play session.
- **Unknown:** whether the exact-build SDK/runtime uses the same enum declaration without additions/reordering; concrete identity and ownership of the task/object pointers in a specific Kismet execution; which observer receives each callback; runtime occurrence; and whether the Boyle archive graph has the same retail properties/edges.
- **Limit:** the layout dump reflects a running 2013 retail executable but is not bound in the available source to the registered 10256413 SHA. It corroborates names/offsets from an independent retail data source while the exact-build decompilation remains the primary binary evidence.

## Reproduction

1. Confirm build identity in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Check each linked cache record's `exe_sha256` and `build_id` and inspect the raw pseudocode.
3. In the local external snapshot inspect `DishonoredGameLayouts.h` entries for offsets `m_TaskState == 252` on `UDisSeqAct_SetTaskState` and `m_TaskState == 93` on `UDishonoredTask_Base`.
4. Inspect `resources/docs/sdk_dump.md` for the dump capture provenance and the DFSDK `DishonoredTask_Base.uc` enum declaration.
5. Compare task-state values separately from notification codes in EXP-0172.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Native storage path: [EXP-0170](EXP-0170-task-state-native-storage-crosswalk.md)
- Objective notification switch: [EXP-0172](EXP-0172-objective-notify-enum-crosswalk.md)
- State event handlers: [EXP-0171](EXP-0171-task-state-event-dispatch.md)
- Boyle candidate graph: [EXP-0169](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
