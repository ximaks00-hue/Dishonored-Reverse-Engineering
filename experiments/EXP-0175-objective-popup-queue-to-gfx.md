---
id: EXP-0175
title: Objective popup queue and GFx SetObjectives path
experiment_status: done
claim_status: inferred
build: "10256413"
question: "How does an objective completion popup candidate move through the exact-build HUD queue into the GFx SetObjectives call?"
---

# EXP-0175 — Objective popup queue and GFx SetObjectives path

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build code paths at `FUN_00BB2500`, `FUN_00BAFE70`, `FUN_00BAE770`, and `FUN_00B98A40`; external reflected layouts and candidate 2012→2013 symbols for popup structs and HUD methods.
- Exclusions: no runtime display confirmation; no claim about player-visible styling, text localization, popup timing in a playthrough, or exact semantic names for event byte values; no Boyle graph linkage.
- Exact-build cache records: [completion callback 00BB2500](../knowledge/cache/decompiles/00BB2500.json), [popup tick 00BAFE70](../knowledge/cache/decompiles/00BAFE70.json), [queue removal 00BAE770](../knowledge/cache/decompiles/00BAE770.json), and [GFx serializer 00B98A40](../knowledge/cache/decompiles/00B98A40.json). These local generated records include the registered EXE SHA and build ID; they are not public Git source of truth.
- External provenance and limitations: reflected layout and 2013 export/matcher rows come from the local Dishonored Recompiled snapshot without a recorded Git commit; hashes and donor limitations are documented in [EXP-0163 provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json) and [EXP-0173](EXP-0173-task-state-field-layout-crosscheck.md).

## Procedure

1. Confirm the registered exact-build SHA and inspect the local index sizes for the four addresses.
2. Read-only decompile the objective-completion callback, popup tick/queue consumer, queue-removal helper, and GFx serializer.
3. Compare offsets used in exact-build code against reflected retail SDK layout for `FDisObjectivePopupInfo`, `FDisTaskPopupInfo`, and the HUD's active popup, queue, and timer fields.
4. Match candidate names through 2012→2013 export rows while retaining each method, score, donor-size difference, and exact-build local-index size.
5. Trace the literal GFx method and data keys in the serializer; do not interpret them beyond the visible arguments and control flow.

## Observations

- The exact-build index records sizes: `FUN_00BB2500` 346 bytes, `FUN_00BAFE70` 591 bytes, `FUN_00BAE770` 227 bytes, and `FUN_00B98A40` 1,640 bytes.
- External 2013 native exports/matcher suggest the following candidate labels:

| Exact-build VA | Candidate label | Matcher method / ratio | Donor sizes (2012/2013) | Local exact-build index size |
| --- | --- | --- | ---: | ---: |
| `0x00BB2500` | `UDisGFxMoviePlayerHUD::OnObjectiveCompleted` | neighbours / 0.925 | 351/351 | 346 |
| `0x00BAFE70` | `UDisGFxMoviePlayerHUD::Tick_ObjectivePopup` | string / 0.814 | 564/591 | 591 |
| `0x00B98A40` | `UDisGFxMoviePlayerHUD::ShowObjectivePopup` | callee / 0.963 | 1652/1649 | 1640 |
| `0x00BAE900` | `TArray<FDisObjectivePopupInfo>::AddItem`-like helper | order / 0.689 | 184/129 | 129 |

- In `FUN_00BB2500`, if a HUD flag at `+0x1FC` has bit `0x4000`, the code scans the popup queue at `+0x514`. It compares queued entry objective pointers with the callback's objective argument. For a matching entry with event byte `1`, it scans that entry's task popup array and removes task entries whose event byte is `2`, then removes the matched popup entry. It creates a new 24-byte popup record with the objective pointer and event byte `2`, then calls `FUN_00BAE900` to append it to the queue.
- `FUN_00BAFE70` decrements HUD timer `+0x520` when its pause/time gate permits. Once the timer expires, it checks the relevant GFx movie `_opened` state, clears the active popup fields at `+0x4FC`, and, when the HUD flag at `+0x1C0` permits, takes the first queued record at `+0x514` into the active-popup area and removes that queue entry via `FUN_00BAE770(0,1)`. For a non-target-notification event it calls `FUN_00B98A40(active_popup)`; event byte `4` branches to `FUN_00B990D0` instead.
- `FUN_00B98A40` reads popup record fields as an objective pointer, event byte, and task array. It obtains strings/state from the objective and, for event values other than `3`, iterates task-popup entries to obtain task strings/states. It constructs GFx object properties including the literal keys `objState` and `objDescription`; inside the task loop it also constructs task state/description properties. It then calls the GFx method named by the literal `SetObjectives` on a movie-player object.
- The external reflected layout records `FDisObjectivePopupInfo` as 24 bytes with `m_pObjective` at offset 0, `m_Event` at 4, `m_Tasks` at 8, and `m_pTargetNotifSeq` at 20; `FDisTaskPopupInfo` is 8 bytes with `m_pTask` at 0 and `m_Event` at 4.
- The same layout records HUD `m_ActivePopup` at offset 1276 (`0x4FC`), `m_PopupQueue` at 1300 (`0x514`), and `m_fPopupTimer` at 1312 (`0x520`), matching the exact-build code's offsets.
- The external CodeRed dump documents reflected offsets from a running retail 2013 executable; its available provenance does not bind it to the registered 10256413 EXE SHA.
- Matcher donor sizes are not the same as all exact-build index sizes. In particular, `OnObjectiveCompleted`'s 2013 export is 351 bytes while the local exact-build index records 346; `ShowObjectivePopup` is 1649 vs local 1640. Similar labels remain candidates even where matcher ratios are high.

## Interpretation

- **Observed, exact-build static path:** the completion callback can remove/coalesce matching queued objective/task records, append a new objective popup record, and the HUD tick can later promote the queue head to active state and call the GFx serializer, subject to timer, movie-open, and HUD-flag conditions.
- **Observed, exact-build UI boundary:** the serializer constructs GFx data fields and invokes a method named by the binary string `SetObjectives`; task/objective description and state data are read before that call. This proves a static call boundary and named GFx method invocation in the code path, not what is rendered on screen.
- **Inferred, record layout mapping:** the external retail reflected layout agrees with the code offsets for active popup, queue, timer, and popup record fields; it supports interpreting the local fields as the named HUD structures.
- **Inferred, function names:** 2013 export/matcher rows support the HUD callback/tick/serializer labels with differing quality. The exact-build code is the primary evidence; donor names are not treated as proof, and size deltas are explicit above.
- **Unknown:** exact enum names for popup-event bytes (candidate callback mapping is in EXP-0176), the special target-notification event value `4`, whether `FUN_00BB2500` is invoked for every objective completion, how GFx `SetObjectives` renders or animates the record, localization/template behavior, runtime gate values, and relation to Boyle's archived Kismet nodes.
- **Limit:** this reconstructs queue mechanics and a native-to-GFx call boundary from static code. It does not confirm a visible popup or a complete end-to-end game scenario.

## Reproduction

1. Confirm the EXE identity in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Resolve local index rows for the four addresses and verify linked cache records' `exe_sha256`/`build_id`.
3. Inspect the call/control flow in `00BB2500`, `00BAFE70`, `00BAE770`, and `00B98A40`.
4. Recheck exact reflected offsets and matcher rows in the recorded external snapshot; do not treat the 2013 dump as SHA-bound to the target EXE.
5. Confirm the `SetObjectives` literal and the GFx data keys in the exact-build pseudocode.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Completion trigger path: [EXP-0174](EXP-0174-task-to-objective-completion-hud-path.md)
- Objective notification map: [EXP-0172](EXP-0172-objective-notify-enum-crosswalk.md)
- Task and objective state fields: [EXP-0173](EXP-0173-task-state-field-layout-crosscheck.md)
- Boyle candidate graph: [EXP-0169](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
