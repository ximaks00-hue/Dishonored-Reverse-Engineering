---
id: EXP-0030
title: "Blink move-mode transition conditions"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What conditions gate the static transition into Blink move mode, and who calls that setter?"
---
# EXP-0030 — Blink move-mode transition conditions

- Status: the conditions on the static transition into Blink move mode and the adjacent exit-state helper are now documented from the exact-build Ghidra decompilation. The event caller and runtime execution are still unknown.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; MCP reports 72,925 functions and this workspace executable path.
- Method: read-only decompilation and call-graph inspection. No game files or Ghidra program bytes were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. Blink vtable slot `+0x1AC` resolves to `FUN_00BFC990` (EXP-0024/0028). It first copies an owner-associated byte from `[this+0x48]+0x104` into `this+0xC8`, then calls `FUN_00BE8D60`. If that helper returns zero, or if the Euclidean distance from the stored target `[this+0x60/+0x64/+0x68]` to owner-pawn coordinates `[owner+0xC4/+0xC8/+0xCC]` is less than or equal to the float at `*[this+0x80]+0xE4`, it calls `FUN_00BFAB80(1)`. `FUN_00BE8D60` returns a truthy `local_8` only when the owner pointer at `this+0x48` is non-null, owner flag byte at `owner+0x120` bit 0 is clear, `this+0x80` is non-null, `FUN_00B49000()` returns zero, and owner byte `[owner+0x104]` is one of `{0,1,2,3,9,12,14}`. For owner byte value 2 it additionally sets a local flag and performs a trace-like call to `FUN_0064E7A0`; that local flag affects the computed `this+0xF4` value but not the boolean `local_8` returned by this helper. These are observed raw conditions; semantic names for the owner byte and trace remain unknown. This branch does not set the component byte at `+0xC9` to move-mode value 1.
2. On the other branch, `FUN_00BFC990` performs additional ability/UI/camera/state setup, calls the object's vtable slot `+0x178`, calls `FUN_00BF9FB0(2)` and other helpers, then stores `1` at `this+0xC9` and clears the timer-like field at `this+0x134`. Package metadata labels movement mode value 1 `EBM_BlinkMove`; the identity of the threshold object/field at `this+0x80` and the helper return contract remain unresolved.
3. `FUN_00BFAB80(modeArg)` is a separate state/cleanup helper. Unless current byte `this+0xC9` is already 2 or 3, it clears `this+0x134`, runs cleanup/state helpers, and branches on `modeArg`. For `modeArg==0`, it restores three saved vector DWORDs to owner-associated fields at `+0x1B4/+0x1B8/+0x1BC`. If current mode is 1 it first changes it to 2 and performs further state work; at the end it assigns `this+0xC9 = (modeArg != 0)+2`, i.e. 2 for zero and 3 for nonzero. The labels for values 2 and 3 were not recovered, so this report calls them numeric modes only.
4. The call graph contains `FUN_00CF34E0` as the only direct code caller of `FUN_00BFC990`; that caller executes `FUN_00CF3360` immediately before it. `FUN_00CF34E0` has no direct caller in the saved call graph. `FUN_00CF3540` shares a call to `FUN_00CF3360` and performs state/coordinate handling but does not call `FUN_00BFC990`. No evidence currently establishes that `FUN_00CF34E0` is invoked by the suspected data table, animation event, item context, or user input.
5. The downstream move path documented in EXP-0024 remains conditional: `FUN_00BFC5D0` dispatches mode 1 to `FUN_00BFC160`; that path reaches trace/candidate processing in `FUN_00BECDF0`, whose accepted branch calls `FUN_006539C0` with the owner pawn and candidate vector. `FUN_006539C0` has further actor/position checks before its stores at pawn `+0xC4/+0xC8/+0xCC`. This is static reachability, not a guarantee that the entry condition succeeds or that every candidate is accepted.

## Evidence classification

**Confirmed in the analyzed binary:** target-distance comparison and branch structure in `FUN_00BFC990`; the successful branch stores mode byte 1; the alternative calls `FUN_00BFAB80(1)`; `FUN_00BFAB80` finishes by assigning numeric mode 3 for a nonzero argument; direct call-graph edge `FUN_00CF34E0` → `FUN_00BFC990`; `FUN_00CF3540` does not directly call the mode setter.

**Package-backed label:** enum value 1 is `EBM_BlinkMove` (EXP-0024).

**Unknown:** meaning of the threshold value and `FUN_00BE8D60` result, semantic names of mode values 2/3, actual owner/caller that invokes `FUN_00CF34E0`, whether a UsePower activation reaches it, and runtime success conditions for reaching the location-writing path.

## Next analysis

1. Recover the registration/owner of `FUN_00CF34E0` and establish an actual indirect-call site before treating it as an activation callback.
2. Continue tracing the `FUN_00C44D30` → Blink `+0x174` → `FUN_00BE7580` → `+0x1AC` bridge, but keep it separate from `FUN_00CF34E0` until a concrete edge joins them.
3. Recover type/source for the threshold object at `this+0x80` and the return contract of `FUN_00BE8D60`.
4. Preserve EXP-0024's distinction between a reachable, validated location write and successful runtime Blink.
