---
id: EXP-0171
title: Task-state helper and observer dispatch
experiment_status: done
claim_status: inferred
build: "10256413"
question: "What exact-build work follows task-state changes through helper codes 3 and 5?"
---

# EXP-0171 — Task-state helper and observer dispatch

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build static call graph and read-only decompilations for `FUN_00BBE6A0`, `FUN_00AD4F60`, state handlers `FUN_00AD1080` / `FUN_00AD1320`, representative additional event handlers, and state-specific helpers `FUN_00BB2A00`, `FUN_00BB2B20`, `FUN_00ACBC70`.
- Exclusions: no symbol renaming; no original-source claims; no identification of observer classes or virtual methods by name; no runtime occurrence, Kismet reachability, UI notification, or gameplay meaning claim.
- Durable decompile outputs: SHA/build-bound local cache records [00BBE6A0](../knowledge/cache/decompiles/00BBE6A0.json), [00AD4F60](../knowledge/cache/decompiles/00AD4F60.json), [00AD1080](../knowledge/cache/decompiles/00AD1080.json), [00AD1320](../knowledge/cache/decompiles/00AD1320.json), [00BB2A00](../knowledge/cache/decompiles/00BB2A00.json), [00BB2B20](../knowledge/cache/decompiles/00BB2B20.json), and [00ACBC70](../knowledge/cache/decompiles/00ACBC70.json). These generated local records are not public Git source of truth.

## Procedure

1. Resolve `FUN_00BBE6A0`'s callers/callee using the local knowledge call graph and confirm its indexed address/size.
2. Read-only decompile the helper, its dispatcher, and handlers selected by dispatcher codes 3 and 5.
3. Decompile state-specific callees reached from handler 5 for values 2/3 and follow one additional direct helper call.
4. Compare handler structures and preserve literal offsets, codes, flags, and virtual slot offsets without assigning names to unknown objects.

## Observations

- The indexed call graph reports 16 direct static call sites to `FUN_00BBE6A0` from eight functions, including two sites in `FUN_00AC17B0`; `FUN_00BBE6A0` has one direct callee, `FUN_00AD4F60`.
- `FUN_00BBE6A0(code, object)` calls the dispatcher only if global pointer `DAT_0145F614` is nonzero and its field at `+0x6F8` is nonzero.
- `FUN_00AD4F60` switches codes 0–5 to six distinct handlers. Code 3 selects `FUN_00AD1080`; code 5 selects `FUN_00AD1320`.
- Handler 3 iterates a global listener array. For each non-null listener that passes `FUN_00AD0F80(listener, object)`, it calls virtual slot `+0x18C` with five arguments including the global manager, manager field `+0x26C`, and two zero values. It then conditionally invokes `FUN_00BBF730` and `FUN_00BB27C0(object)` based on object flag `+0x60` bit 3 and an owner/outer flag check, and iterates the dispatcher's attached-object array calling virtual slot `+0x1C` on each entry.
- Handler 5 resolves an object from the task's field `+0x24`, iterates the same global listener array and applies the same listener filter. For each accepted listener, it builds an argument container holding the task byte at `+0x5D` and calls virtual slot `+0x18C` with the manager, manager field `+0x26C`, the container, and zero-valued arguments.
- Handler 5 also conditionally calls `FUN_00BBF730`; if the task byte is `2`, it calls `FUN_00BB2A00`; if it is `3`, it calls `FUN_00BB2B20`. It iterates attached objects calling virtual slot `+0x24` only when the task byte is `2`.
- `FUN_00BB2A00` and `FUN_00BB2B20` both check owner flag `+0x1FC` bit `0x4000`, consult a task/object pair array at `+0x514` (count at `+0x518`) to suppress duplicate handling for selected pair states, then call `FUN_00B9EE60`, `FUN_00BAE900`, and `FUN_00C4F0B0` on the non-duplicate path. The pair-state byte used by the duplicate check is `2` in the first helper and `1`/`3`/`2` in the second helper's distinct branches.
- `FUN_00ACBC70`, called later in handler 5 when task byte is `2`, checks task flag `+0x48` bit 2, task byte `+0x45`, and whether all task pointers in the array at `+0x58` have byte `+0x5D == 2`; when its conditions pass it sets `+0x45` to `1` and dispatches code 1 through `FUN_00BBE6A0`.
- Other direct callers of `FUN_00BBE6A0` include `FUN_00AC6300` (codes 3 and 5) and `FUN_00AC63C0` (code 3 after a bit update and a task-state check), showing the event helper is shared beyond the setter path.

## Interpretation

- **Observed:** codes 3 and 5 are not interchangeable notifications. They route through separate handlers; code 5 packages the current task-state byte into a callback argument and has additional branches for byte values 2 and 3. Code 3 has a distinct callback/attached-object dispatch pattern.
- **Inferred:** `FUN_00BBE6A0` is a guarded event/observer dispatcher in the structural sense: a global gate, numeric event-code switch, filtered listener iteration, virtual callbacks, and attached-object callbacks are visible in the exact-build decompilation. This does not establish source-level class or event names.
- **Inferred, state-specific follow-on:** byte values 2 and 3 reach different helper paths. Byte value 2 can also trigger an aggregate check over related task bytes, which then dispatches code 1. The user-facing meaning of these values is still unknown; do not label them Completed/Failed/etc. from archive data.
- **Unknown:** identities of `DAT_0145F614`, `DAT_0145F628`, listener and attached-object classes, virtual slots `+0x18C/+0x1C/+0x24`, and the semantics of downstream `FUN_00B9EE60`, `FUN_00BAE900`, and `FUN_00C4F0B0`; runtime execution and linkage to the Boyle candidate graph also remain unknown.
- **Limit:** the output is Ghidra pseudocode for this exact executable, not source code. Static call-graph edges and pseudocode do not prove a particular event occurs in a playthrough.

## Reproduction

1. Verify the registered EXE SHA-256 in the build record.
2. Query the local function dossier for `0x00BBE6A0` to reproduce the indexed direct call graph.
3. Read-only decompile the addresses listed above; check each cache record's `exe_sha256` and `build_id`.
4. Compare the dispatcher switch, listener loops, offsets, virtual calls, and state branches against the observations above. Keep object identities and enum names unknown until independently proven.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Previous setter path: [EXP-0170](EXP-0170-task-state-native-storage-crosswalk.md)
- Boyle static candidate graph: [EXP-0169](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
