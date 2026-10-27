---
id: EXP-0176
title: Objective and task popup event-byte crosswalk
experiment_status: done
claim_status: inferred
build: "10256413"
question: "What event-byte values are written and reconciled in exact-build objective/task popup records?"
---

# EXP-0176 — Objective and task popup event-byte crosswalk

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build decompilations of seven HUD callbacks and popup serializer; observed constants written to `FDisObjectivePopupInfo.m_Event` and `FDisTaskPopupInfo.m_Event`; external candidate native names and retail reflected record layout.
- Exclusions: no runtime observation; no claim that a popup is visible, that an event byte has a particular localized/UI meaning, or that the PDB donor names are exact-build symbols. The two `m_Event` fields belong to different struct types and are analyzed separately.
- Exact-build cache records: [objective added 00BB2480](../knowledge/cache/decompiles/00BB2480.json), [objective completed 00BB2500](../knowledge/cache/decompiles/00BB2500.json), [objective failed 00BB2660](../knowledge/cache/decompiles/00BB2660.json), [task added 00BB27C0](../knowledge/cache/decompiles/00BB27C0.json), [task updated 00BB28E0](../knowledge/cache/decompiles/00BB28E0.json), [unnamed task-event 2 callback 00BB2A00](../knowledge/cache/decompiles/00BB2A00.json), [unnamed task-event 3 callback 00BB2B20](../knowledge/cache/decompiles/00BB2B20.json), and [serializer 00B98A40](../knowledge/cache/decompiles/00B98A40.json). Cache records bind to the registered build SHA/ID and are generated local evidence.
- External provenance: candidate names are joined from a local third-party 2013 export and 2012→2013 matcher; record layout comes from a CodeRed dump documented as captured from a running retail 2013 executable. Snapshot/hash limits are described in [EXP-0163 provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json) and [EXP-0173](EXP-0173-task-state-field-layout-crosscheck.md).

## Procedure

1. Confirm exact-build function-index rows and SHA-bound decompile caches for the seven HUD callbacks.
2. Read the byte constants placed in callback-built popup structs and the task-event filters applied to queued records.
3. Cross-check the separate struct fields and offsets against `FDisObjectivePopupInfo` and `FDisTaskPopupInfo` in the external retail layout.
4. Join each candidate function address to 2013 export/matcher rows and retain matching method, ratio, and size deltas.
5. Compare serializer branches with these values without assigning UI text or animation meanings.

## Observations

The external reflected layout describes `FDisObjectivePopupInfo` with `m_Event` at offset 4, a task array at offset 8, and target-notification pointer at offset 20. `FDisTaskPopupInfo` is a separate 8-byte record with its own `m_Event` at offset 4. The exact-build callbacks write and filter these bytes as follows:

| Record field | Byte | Exact-build evidence | Candidate donor label | Matcher evidence | Exact-build index size vs donor 2013 size |
| --- | ---: | --- | --- | --- | ---: |
| Objective popup `m_Event` | 0 | `FUN_00BB2480` queues objective pointer with byte 0 | `OnObjectiveAdded` | neighbours, 0.935; donor 122 bytes | 122 vs 122 |
| Objective popup `m_Event` | 1 | Task-added and task-updated handlers create/update objective popup records with byte 1 | implicit task-notification container | See task rows below | — |
| Objective popup `m_Event` | 2 | `FUN_00BB2500` creates byte 2 after removing a matching queued byte-1 record and selected task events | `OnObjectiveCompleted` | neighbours, 0.925; donor 351 bytes | 346 vs 351 |
| Objective popup `m_Event` | 3 | `FUN_00BB2660` creates byte 3 after removing a matching queued byte-1 record and selected task events | `OnObjectiveFailed` | neighbours, 0.933; donor 351 bytes | 346 vs 351 |
| Task popup `m_Event` | 0 | `FUN_00BB27C0` creates a task record with byte 0 | `OnTaskAdded` | neighbours, 0.924; donor 287 bytes | 287 vs 287 |
| Task popup `m_Event` | 1 | `FUN_00BB28E0` creates a task record with byte 1 | `OnTaskUpdated` | neighbours, 0.930; donor 280 bytes | 280 vs 280 |
| Task popup `m_Event` | 2 | `FUN_00BB2A00` constructs/updates a task record with byte 2; `FUN_00BB2500` removes queued byte-2 records while completing the containing objective | candidate task-completed event; exact handler name unavailable | 2013 export row is `new`; no donor name | 287 |
| Task popup `m_Event` | 3 | `FUN_00BB2B20` constructs/updates a task record with byte 3; `FUN_00BB2660` removes queued byte-3 records while failing the containing objective | candidate task-failed event; exact handler name unavailable | 2013 export row is `new`; no donor name | 291 |

- For a matching queued objective, the completion callback scans its task records and deletes event-2 task records; the failure callback deletes event-3 task records. Both then remove the matching objective popup entry and append a separate objective popup record (event 2 for completion; event 3 for failure).
- The task-added/task-updated callbacks build a task record (event 0/1) and associate it with an objective popup record (event 1), coalescing into an already queued record for the same objective when the code's matching conditions pass.
- `FUN_00BB2A00` and `FUN_00BB2B20` are direct exact-build producers for task event bytes 2 and 3. Each checks HUD mask `+0x1FC & 0x4000`, reads a task's `+0x24` key, scans the popup queue, and passes a task record initialized with event 2 or 3 to `FUN_00B9EE60`. On a queue miss, each also creates an objective popup container with event byte 1 and appends it through `FUN_00BAE900`; the two callbacks differ in how they reconcile existing objective-event states.
- The exact-build serializer `FUN_00B98A40` reads the objective popup event byte. For value 3, the code skips task-record serialization; for values 0–2, it enters the task array processing branch. This describes code flow only.
- Local exact-build index sizes are: `00BB2480` 122, `00BB2500` 346, `00BB2660` 346, `00BB27C0` 287, `00BB28E0` 280, `00BB2A00` 287, and `00BB2B20` 291 bytes.
- Candidate donor names are from 2012→2013 matching; for objective complete/fail functions, the local exact-build index is 5 bytes shorter than the 2013 donor function size despite donor 2012/2013 rows agreeing at 351 bytes.

## Interpretation

- **Observed:** objective popup and task popup records have separate event-byte fields; exact-build code writes values 0–3 to each according to the table. Task event values 2/3 have direct producer callbacks and are also removed while a matching task-update popup is replaced with an objective complete/fail popup.
- **Inferred, candidate labels:** external exports support naming the callbacks `OnObjectiveAdded`, `OnObjectiveCompleted`, `OnObjectiveFailed`, `OnTaskAdded`, and `OnTaskUpdated`; name confidence varies and function-size differences are retained. The event-byte values themselves are direct exact-build observations.
- **Inferred, semantics:** the callback structure and donor labels support reading the numeric values as add/update/complete/fail event categories. Their exact UI text, ordering, animation, and localization semantics are unknown.
- **Unknown:** whether additional event values exist, the exact enum names/semantics for task events 2/3, whether `FUN_00B98A40` renders each event differently, and runtime popup visibility. The direct producers for task event bytes 2/3 are now established as `FUN_00BB2A00` and `FUN_00BB2B20`; their native names remain unavailable.
- **Limit:** event names come from a donor-symbol crosswalk; no source names were applied to Ghidra. The two `m_Event` fields are distinct domains even where their byte values coincide.

## Reproduction

1. Verify the registered EXE SHA-256 in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Resolve the seven callback sizes in `research/executable/functions.csv` and verify linked decompile caches' `exe_sha256`/`build_id`.
3. Confirm struct offsets in the external generated `DishonoredGameUIClasses.h` / `DishonoredGameLayouts.h` and the documented CodeRed dump source.
4. Reproduce the 2013 matcher rows and keep candidate labels separate from exact-build numeric observations.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Popup queue and GFx call: [EXP-0175](EXP-0175-objective-popup-queue-to-gfx.md)
- Completion path: [EXP-0174](EXP-0174-task-to-objective-completion-hud-path.md)
- Cluster summary: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
