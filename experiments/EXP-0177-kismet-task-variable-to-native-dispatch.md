---
id: EXP-0177
title: Kismet Task variable resolution and task-action dispatch
experiment_status: done
claim_status: mixed
build: "10256413"
question: "How does a generic Kismet task action resolve its Task variable link and dispatch a task instance in the registered retail build?"
---

# EXP-0177 — Kismet Task variable resolution and task-action dispatch

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build static decompilations of the generic task-action activation path, variable-link lookup, task-variable resolution, and objective/task lookup helpers; raw exact-build PE inspection of a donor-derived `UDisSeqAct_SetTaskState` vtable candidate; donor symbol crosswalk for candidate function names; editor-source declaration of the `Task` link.
- Exclusions: no selected Boyle Kismet export is joined to this call path; no runtime observation or package payload/link reconstruction. The vtable's class identity is cross-source inferred even though its raw slot contents are read from the exact-build executable.
- Exact-build cache records: [task action candidate 00BA8300](../knowledge/cache/decompiles/00BA8300.json), [variable-link resolver 00BDD150](../knowledge/cache/decompiles/00BDD150.json), [task pointer getter 00B92210](../knowledge/cache/decompiles/00B92210.json), [task variable accessor 00B9CDA0](../knowledge/cache/decompiles/00B9CDA0.json), [instance resolver 00AD0DC0](../knowledge/cache/decompiles/00AD0DC0.json), [objective lookup 00AD0BF0](../knowledge/cache/decompiles/00AD0BF0.json), and [task lookup 00ACBE40](../knowledge/cache/decompiles/00ACBE40.json). Cache records bind to the registered build SHA/ID and remain local generated evidence.
- Raw pointer evidence: [candidate vtable slot check](../research/executable/evidence/EXP-0177-settaskstate-vtable-slot.json) records the PE image base, donor-derived table RVA, exact-build file offsets/bytes, and source hashes.
- External symbol snapshot: `D:\Dishonored\01_REFERENCE\community\dishonoredrecompiled-main\resources\docs\symbols`; `functions_2013.csv` SHA-256 `C3B6821A018D30E2A317D95396B6584EB0C378BA5C0BD0075EC1E8C6C240CE88`, `match_2012_2013.csv` SHA-256 `06164572249FD3E2477F1C404B2AF6A27CACF83ACECB8C82DB08FCEDE037B330`. The source snapshot has no Git identity; labels remain donor candidates.

## Procedure

1. Confirm the registered build and resolve each target function in the exact-build function index.
2. Decompile the relevant indexed functions read-only and verify that returned cache records carry the registered EXE SHA and build ID.
3. Trace the literal `Task` passed to the variable-link resolver, then follow the resolved link objects through the task-variable getter and objective/task lookup helpers.
4. Inspect external editor metadata for the declared `Task` variable-link type and donor export/matcher rows for the associated function-name candidates.
5. Use the external 2012→2013 global-vtable match to locate the candidate table in the exact-build PE, translate its RVA through the PE section map, and read the slot pointer without executing the game.

## Observations

- `FUN_00BA8300` passes the wide string `Task` to `FUN_00BDD150`, receives an array of linked objects, passes each non-null link object through `FUN_00AD0DC0`, applies additional guards, then performs an indirect virtual call through the action object's vtable at byte offset `+0x190` with the resolved pointer as an argument.
- `FUN_00BDD150` scans the action's variable-link records, compares each link name with the supplied string, and gathers object values from that link's linked-variable array. This is the exact-build path by which the literal `Task` link is selected.
- `FUN_00AD0DC0` checks a link object's field at `+0x24`, calls `FUN_00AD0BF0` on that referenced object, and, if that lookup succeeds, calls `FUN_00ACBE40` using the original link object.
- `FUN_00AD0BF0` scans an array whose pointer/count fields are at `+0x54/+0x58`, comparing two-word names from the searched object with each entry's name. On a match it returns the corresponding array entry.
- `FUN_00ACBE40` scans an object's pointer/count array at `+0x58/+0x5C`, compares each contained object's name with the supplied object's name, and returns the matching pointer. The external layout places `UDishonoredObjective::m_Tasks` at `+0x58` with its count at `+0x5C`, which is consistent with this use but does not independently prove the exact runtime argument types.
- `FUN_00B92210` reads a variable object's candidate `m_pObjective` pointer at `+0xB0`, then scans that objective's task array at `+0x58/+0x5C` for an entry matching the variable's two-word task name at `+0xB4/+0xB8`. It returns the matching task pointer or null.
- `FUN_00B9CDA0` stores the return from `FUN_00B92210` at object offset `+0xBC`. The 2013 donor export names `FUN_00B92210` as `UDisSeqVar_Task::GetTaskPtr`; its exact local indexed size is 121 bytes and equals the donor export size.
- Exact-build function sizes: `00BA8300` 454 bytes; `00BDD150` 486; `00AD0DC0` 54; `00AD0BF0` 196; `00ACBE40` 254; `00B92210` 121; `00B9CDA0` 16. The relevant decompile caches include the target EXE SHA/build ID.
- The donor matcher maps `UDisSeqAct_TaskAction::Activated` to `00BA8300` with method `vtable`, ratio `0.788`, donor size 433 versus exact index size 454. The low-quality transfer and size delta make the class/method label a candidate, not an established target name.
- Donor rows map `UDisSeqAct_SetTaskState::HandleTaskInstance` to `00B86840` with method `bytes`, ratio `1.000`, sizes 23/23. The exact-build `00B86840` body is already described in [EXP-0170](EXP-0170-task-state-native-storage-crosswalk.md). This byte-perfect name crosswalk does not alone prove that the virtual slot called by `00BA8300` points to this override.
- The external global matcher maps the 2012 `UDisSeqAct_SetTaskState` vtable RVA `0x00D49238` to 2013 RVA `0x00D58918`, method `global-table`, ratio `1.000`. Treating that 2013 RVA as an exact-build table candidate (image base `0x00400000`) gives VA `0x01158918`, in `.rdata`.
- The registered exact-build EXE (SHA-256 above) contains the little-endian pointer `0x00B86840` at candidate table VA `0x01158AA8` (`0x01158918 + 0x190`; raw file offset `0x00D574A8`). The entry at candidate offset `+0x174` is `0x00BA8300`, consistent with the separately mapped `Activated` candidate. Thus the raw slot value agrees with the exact-build indexed `HandleTaskInstance` candidate address; identity of the containing table as the SetTaskState vtable rests on the external global-table crosswalk and table contents.
- External editor source `DisSeqAct_TaskAction.uc` declares a variable link named `Task`, with expected type `DisSeqVar_Task`, `MinVars=1`, and `MaxVars=255`. This is editor metadata and does not establish the properties or wiring of a particular retail sequence export.
- The external 2013 reflected layout places `UDisSeqVar_Task::m_pObjective` at `+0xB0`, `m_TaskName` at `+0xB4`, `m_pDummyTask` at `+0xBC`, and `m_pTask` at `+0xC0`. These offsets align with the exact-build getter/accessor offsets above, but the layout dump is not bound to the target EXE hash.

## Interpretation

- **Observed, exact-build static:** the generic action code selects a variable link by the literal name `Task`, iterates its linked objects, resolves task-related objects through a helper chain, and invokes a virtual method at vtable byte offset `+0x190` with the resolved task pointer.
- **Observed, exact-build PE bytes at a donor-derived table candidate:** slot `+0x190` contains pointer `0x00B86840`; the preceding candidate slot `+0x174` contains `0x00BA8300`.
- **Observed, exact-build static:** the candidate task-variable getter uses its objective pointer and task name to find a same-named entry in the objective's task array. A nearby accessor stores that result at `+0xBC`.
- **Inferred, table/name association:** external global-table matching identifies the candidate table as `UDisSeqAct_SetTaskState`'s vtable. Its exact-build `+0x190` slot points to `00B86840`, whose donor row is a byte-perfect match for `UDisSeqAct_SetTaskState::HandleTaskInstance`. `00BA8300` is likely `UDisSeqAct_TaskAction::Activated`, but its donor matcher is a 0.788 vtable match with a 21-byte size difference. `00B92210` has a strong `GetTaskPtr` association (0.978 callee match and equal size).
- **Inferred, layout association:** `+0xB0/+0xB4/+0xBC` in the object handled by `FUN_00B92210`/`FUN_00B9CDA0` align with the external 2013 reflected fields `m_pObjective` / `m_TaskName` / `m_pDummyTask`. The accessor's exact field identity at `+0xBC` is not proved by local target metadata.
- **Unknown:** whether a specific Boyle retail Kismet node supplies this link; the retail serialized variable-link identity and runtime execution. The table's class label still relies on the donor global-table mapping, not an exact-build symbol.
- **Limit:** decompiler pseudocode renders machine code and is not original source. Editor and donor references are external cross-source evidence. No compressed UPK payload was decompiled, and no runtime process was launched.

## Reproduction

1. Verify the build SHA in `research/builds/BUILD-STEAM-10256413/build.md`.
2. Re-run read-only decompilation for the listed addresses with the configured exact-build static gateway; verify `exe_sha256` and `build_id` in each returned cache record.
3. Resolve the exact function sizes in `research/executable/functions.csv` and donor function/matcher rows in the symbol snapshot identified above.
4. Read the cited external editor declaration and reflected layout; retain their separate provenance and build-scope limitations.
5. Reproduce the donor global-table row for the vtable candidate, then read exact-build PE bytes at VA `0x01158918` and verify the pointer at offset `+0x190`; do not treat the class label as an exact-build symbol.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Task-state handler and storage: [EXP-0170](EXP-0170-task-state-native-storage-crosswalk.md)
- Boyle archive-to-retail node candidates: [EXP-0169](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
- Evidence graph: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
