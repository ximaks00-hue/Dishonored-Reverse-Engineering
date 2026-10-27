---
id: EXP-0174
title: Task aggregation to objective completion notification and HUD
experiment_status: done
claim_status: inferred
build: "10256413"
question: "Does the exact-build task-state path statically connect all-completed task checks to objective-state mutation and the objective-completed HUD handler?"
---

# EXP-0174 — Task aggregation to objective completion notification and HUD path

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build static path from task state byte `2` through related-task aggregation, objective state byte `+0x45`, notification code `1`, objective-notification dispatcher, and one HUD candidate callee.
- Exclusions: no runtime execution, user-visible display confirmation, exact observer ownership, or Boyle Kismet reachability claim. External symbol/layout data is retained as corroborating cross-source evidence, not treated as source code.
- Related exact-build caches: [00AD1320](../knowledge/cache/decompiles/00AD1320.json), [00ACBC70](../knowledge/cache/decompiles/00ACBC70.json), [00BBE6A0](../knowledge/cache/decompiles/00BBE6A0.json), [00AD4F60](../knowledge/cache/decompiles/00AD4F60.json), [00AD0E00](../knowledge/cache/decompiles/00AD0E00.json), and [00BB2500](../knowledge/cache/decompiles/00BB2500.json). All cache records are local generated evidence bound to build ID and EXE SHA; they are not public Git source of truth.
- External corroboration: CodeRed-derived retail SDK layout captured from a running retail 2013 executable; DFSDK enum declarations; local 2013 native-function export and 2012→2013 matcher. Snapshot and hash caveats are detailed in EXP-0163/0173.

## Procedure

1. Read exact-build cached decompilations for the state-change handler, aggregate check, notification helper/dispatcher, code-1 handler, and downstream candidate HUD function.
2. Trace only explicit direct calls and field reads/writes; keep the three enum/value domains separate.
3. Cross-check `UDishonoredObjective::m_ObjectiveState` offset and enum order against external retail SDK artifacts.
4. Preserve the matcher quality for the candidate HUD name and distinguish that from the exact-build call edge.

## Observations

- Exact-build task state-change handler `FUN_00AD1320` has a branch when task byte at `+0x5D` equals `2`. It iterates entries in an array and calls a virtual slot `+0x24` on each attached object. If the preceding owner lookup returns non-null, it calls `FUN_00ACBC70(task)`.
- `FUN_00ACBC70` requires task flag bit `+0x48 & 0x04` and objective byte `+0x45 != 1`. It checks every task pointer in an array (`count +0x5C`, pointer array `+0x58`) and returns unless every task's byte `+0x5D` equals `2`. If the check passes, it writes `1` to objective byte `+0x45` and calls `FUN_00BBE6A0(1, objective)`.
- The CodeRed-derived retail layout records `UDishonoredObjective::m_ObjectiveState` at decimal offset 69 (`0x45`). The editor SDK enum order is `DOS_Active`, `DOS_Completed`, `DOS_Failed`, `DOS_MAX`; standard UE ordinal interpretation makes byte `1` the candidate Completed value.
- `FUN_00BBE6A0` globally gates and forwards event code `1` to `FUN_00AD4F60`; dispatcher branch 1 calls `FUN_00AD0E00` with the event object.
- In exact-build `FUN_00AD0E00`, under an object flag guard (`object +0x48 & 0x10 == 0`), the function calls `FUN_00BBF730()` and then `FUN_00BB2500(object)`. It subsequently iterates an attached-object array and invokes virtual slot `+0x14` on its entries.
- External 2013 native export maps VA `0x00BB2500` to `UDisGFxMoviePlayerHUD::OnObjectiveCompleted(UDishonoredObjective *)`. The 2012→2013 matcher row uses method `neighbours`, ratio `0.925`, equal donor sizes `351/351`; the exact-build local function index records 346 bytes, a 5-byte size difference from the donor export. This remains a candidate function name, not a semantic proof by itself.
- The same objective field offset is recorded in the external generated `DishonoredGameLayouts.h` as `m_ObjectiveState == 69`; the CodeRed dump provenance and limitations are documented in EXP-0173.

## Interpretation

- **Observed, exact-build static path:** a task value-2 branch can check all task bytes in an associated task array. On success it writes objective byte `+0x45 = 1`, dispatches notification code `1`, and that code reaches a handler which calls `FUN_00BB2500` under a flag guard.
- **Inferred, objective field/state:** the external reflected offset aligns objective byte `+0x45` with `m_ObjectiveState`; the editor enum order supports interpreting value `1` as `DOS_Completed`. This cross-build SDK corroboration is strong for field identity but is not bound to the registered 10256413 executable hash.
- **Inferred, named notification/HUD association:** EXP-0172 maps notification code `1` to candidate `DOCNET_CompletedObjective`; the export/matcher labels `FUN_00BB2500` as candidate `UDisGFxMoviePlayerHUD::OnObjectiveCompleted`. The exact-build call edge is observed, but the transferred donor name and user-visible effect remain inferred.
- **Important distinction:** task state value `2` (candidate `DTS_Completed`), objective state value `1` (candidate `DOS_Completed`), and objective notification code `1` (candidate `DOCNET_CompletedObjective`) are separate fields/domains.
- **Unknown:** whether the global notification gate is enabled during a given session; which exact Kismet task array/object reaches this path; observer and attached-object identities; whether the HUD candidate updates a visible widget, queues a popup, or only updates internal state; and runtime occurrence.
- **Limit:** static calls establish a possible execution chain, not that a specific playthrough invokes it. Candidate names are transferred from external symbols with varying match quality; no Ghidra names were changed.

## Reproduction

1. Confirm the registered build SHA-256 in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Check `exe_sha256`/`build_id` in the linked cache records.
3. Verify task-state handler → `FUN_00ACBC70` → `FUN_00BBE6A0(1, objective)` → dispatcher case 1 → `FUN_00AD0E00` → guarded call `FUN_00BB2500(object)`.
4. Recheck external layout offset, enum order, and name-match ratio; keep the three value domains distinct.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Task-state field and values: [EXP-0173](EXP-0173-task-state-field-layout-crosscheck.md)
- Notification code map: [EXP-0172](EXP-0172-objective-notify-enum-crosswalk.md)
- Event handler structure: [EXP-0171](EXP-0171-task-state-event-dispatch.md)
- Setter and action-field path: [EXP-0170](EXP-0170-task-state-native-storage-crosswalk.md)
- Boyle archive graph (not joined to this runtime path): [EXP-0169](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
