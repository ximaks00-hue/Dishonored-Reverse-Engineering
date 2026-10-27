---
id: EXP-0180
title: Task flag transition and task-added notification path
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Under which exact-build conditions does the SetTaskHidden handler candidate update task flag bit 3 and reach the task-added popup callback?"
---

# EXP-0180 — Task flag transition and task-added notification path

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build action handler `0x00B86820`, task bit updater `0x00AC63C0`, guarded event helper `0x00BBE6A0`, dispatcher `0x00AD4F60`, code-3 handler `0x00AD1080`, and task popup callback `0x00BB27C0`.
- Exclusions: no runtime occurrence, no proof of a particular serialized Kismet node, no target-binary field or enum symbols, and no claim that the queued record becomes visible.
- Exact-build cache records: [00B86820](../knowledge/cache/decompiles/00B86820.json), [00AC63C0](../knowledge/cache/decompiles/00AC63C0.json), [00BBE6A0](../knowledge/cache/decompiles/00BBE6A0.json), [00AD4F60](../knowledge/cache/decompiles/00AD4F60.json), [00AD1080](../knowledge/cache/decompiles/00AD1080.json), and [00BB27C0](../knowledge/cache/decompiles/00BB27C0.json). Each records build ID `10256413` and the registered EXE SHA above. These are local generated decompilation records.
- Cross-source leads: the candidate `SetTaskHidden` class/handler mapping is supported by the exact-build table and byte-match evidence in [EXP-0179](EXP-0179-task-action-vtable-family.md); event-code dispatch and the task popup callback map are separately documented in [EXP-0171](EXP-0171-task-state-event-dispatch.md) and [EXP-0176](EXP-0176-objective-task-popup-event-codes.md).
- Field-layout lead: [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md) records the pinned 2013 layout's task bitfield order, which places candidate `m_bHidden` as the fourth bit after `m_TaskState`; that aligns with exact-build DWORD `+0x60` bit 3 but has no per-bit static assertion and is not target-symbol evidence.

## Procedure

1. Verify the registered executable SHA-256 and resolve the six function starts/sizes in the exact-build index.
2. Read the action-handler body and the callee that receives its `+0xFC` bit value.
3. Follow the exact numeric helper argument into the dispatcher and its selected branch.
4. Inspect the handler's task-bit, parent-object, and HUD callback guards; keep all literals and offsets distinct from candidate symbol names.
5. Verify every cited cache record's `exe_sha256` and `build_id` fields; do not infer runtime execution from the static call graph.

## Observations

- The exact-build table candidate at RVA `0x00D58780` has slot `+0x190` pointing to `0x00B86820`. Donor evidence labels the table and handler `UDisSeqAct_SetTaskHidden` / `HandleTaskInstance`; the handler is a byte match with ratio 1.000 and equal 25-byte sizes. Class naming remains cross-source evidence, not target symbol metadata (EXP-0179).
- `FUN_00B86820` passes action DWORD `+0xFC & 1` to `FUN_00AC63C0`.
- Raw x86 in the registered executable confirms the action handoff: `0x00B86823` loads `[ecx+0xFC]`, `0x00B8682C` applies `and eax, 1`, and the call at `0x00B86830` targets `0x00AC63C0`.
- `FUN_00AC63C0` reads the task DWORD at `+0x60`, compares its bit 3 with the passed Boolean, and writes the DWORD with bit 3 changed only when the values differ. Raw x86 shows the compare at `0x00AC63D2`, conditional DWORD write at `0x00AC63E4`, test of bit 3 at `0x00AC63E7`, and compare of task byte `+0x5D` to `1` at `0x00AC63EB`. When the new bit is clear and the task byte equals `1`, it pushes numeric code `3` and calls `FUN_00BBE6A0` at `0x00AC63F2`. Thus the event call is transition-dependent and requires both the resulting-bit and task-byte conditions.
- `FUN_00BBE6A0` calls the dispatcher only when global pointer `DAT_0145F614` and its field `+0x6F8` are nonzero. `FUN_00AD4F60` routes numeric code `3` to `FUN_00AD1080` (EXP-0171).
- `FUN_00AD1080` first walks a listener array and can invoke listener virtual slot `+0x18C`. It then checks that task bit 3 is clear. When the optional parent/type test does not veto the path (including the observed parent `+0x48` bit-`0x10` condition), it calls `FUN_00BBF730` and then `FUN_00BB27C0(task)`.
- `FUN_00BB27C0` returns without queue work unless the HUD object's `+0x1FC` mask contains `0x4000`. On the enabled path it uses task `+0x24` as the queue key, checks existing records in the queue at `+0x514` (count `+0x518`), builds task-popup event byte `0`, and may build an objective-popup container with event byte `1` (EXP-0176). The candidate name `OnTaskAdded` is external symbol evidence, not an exact-build name.
- Function-index sizes are 25, 64, 37, 96, 398, and 287 bytes respectively for the six functions in the order listed in scope. All six decompilation caches bind to the registered build identity.

## Static path summary

```text
action +0xFC bit 0
  -> task +0x60 bit 3 transition
  -> if new bit 3 = 0 and task +0x5D = 1: helper code 3
  -> global event gate -> dispatcher case 3
  -> listener callbacks
  -> if task bit 3 remains clear and parent/type test does not veto:
       FUN_00BBF730 -> FUN_00BB27C0
  -> if HUD mask +0x1FC & 0x4000:
       queue/deduplicate task popup event byte 0; possible container event byte 1
```

The conditional edges are material: a bit transition alone does not establish that the helper, handler, or popup queue branch executes in a particular game state.

## Interpretation

- **Observed, exact-build static:** the action bit controls task DWORD `+0x60` bit 3; a transition to clear plus task byte `+0x5D == 1` can call numeric event helper code `3`. The dispatcher, handler, and callback contain the gates and data flow listed above.
- **Observed, raw-instruction cross-check:** the registered executable contains the described field loads, mask, conditional write, state-byte compare, and code-3 call at the listed addresses. Its SHA-256 was recomputed during this experiment and matches the build record.
- **Inferred, candidate labels:** external cross-source matching supports `SetTaskHidden`; the 2013 layout field order supports candidate task `m_bHidden` for DWORD `+0x60` bit 3, but no bitfield-specific target assertion is available. The dispatcher enum crosswalk supports reading event code `3` as a new-task category and the popup callback as `OnTaskAdded`. These labels do not prove visible hide/show behavior or callback execution.
- **Inferred, possible presentation path:** when all static guards pass, this path reaches code that queues a task popup record with event byte `0`; `FUN_00BB27C0`'s queue writes do not prove that a user sees a popup.
- **Unknown:** exact field/enum names in build `10256413`, which retail Kismet values select each branch, the parent/type guard's semantic role, whether the global and HUD gates pass at runtime, and whether the queue record reaches visible GFx output.
- **Limit:** decompiler output is a rendering of machine code, not original source. The call graph establishes possible static control flow, not runtime reachability.

## Reproduction

1. Confirm the target SHA in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Resolve all six function sizes in `research/executable/functions.csv` and verify each cache's SHA/build fields.
3. Recompute PE VA-to-file-offset mapping and decode the listed raw instruction addresses with a 32-bit x86 disassembler.
4. Recheck `FUN_00B86820`'s action `+0xFC` mask and `FUN_00AC63C0`'s `+0x60`/`+0x5D` conditions.
5. Follow numeric case `3` through `FUN_00BBE6A0`, `FUN_00AD4F60`, and `FUN_00AD1080`; verify the conditional call to `FUN_00BB27C0`.
6. Compare the queue branch and event byte against EXP-0176 without transferring donor names into the exact-build binary.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Task-action virtual slots: [EXP-0179](EXP-0179-task-action-vtable-family.md)
- Numeric dispatcher: [EXP-0171](EXP-0171-task-state-event-dispatch.md)
- Popup event-byte map: [EXP-0176](EXP-0176-objective-task-popup-event-codes.md)
- Task-target/field-layout crosswalk and bitfield caveat: [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md)
- Objective/task/HUD evidence graph: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
