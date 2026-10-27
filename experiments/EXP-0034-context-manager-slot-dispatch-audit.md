---
id: EXP-0034
title: "Context-manager slot-dispatch audit"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Is there a concrete context-manager slot dispatch path, and does it reach Blink?"
---
# EXP-0034 — Context-manager slot-dispatch audit

- Status: identified a concrete two-stage virtual dispatch path through a context-array manager; the selected object's dynamic class and connection to Blink remain unproven.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`.
- Method: read-only Ghidra decompilation/disassembly/xrefs and raw vtable bytes. No game or Ghidra program bytes were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. `FUN_00AA2590` receives an object in ECX. Raw instructions at `0x00AA25B2` load `ECX=[this+0x59C]`, then push four values (context index and three further arguments) and call `FUN_00C04C30`. Before that call, it stores the result of `FUN_00AA2120(index)` at `this+0x8B7+index`.
2. `FUN_00C04C30` passes its first stack argument as an index to `FUN_00C04BD0`, preserving the manager object in ECX. It tests the returned pointer, calls the returned object's virtual slot `+0x134` with no explicit stack argument, and if EAX is nonzero calls slot `+0x188` with the other three stack arguments. It returns a small status derived from the second virtual call.
3. `FUN_00C04BD0` treats its ECX receiver as a manager: it tests flag bit 0 at `+0xE0`, reads the requested channel's selected array index from `+0x44 + 0x28*index`, bounds-checks it against count `+0x3C`, and returns the first DWORD of the corresponding 0x0C-byte entry in data array `+0x38`. `FUN_00C17D10` writes the same per-channel selected index and performs related operations on the selected object. This confirms a context-like selected-object lookup mechanism; the manager's reflected class name and entry schema are not yet identified.
4. `FUN_00C04C30` has one direct caller, `FUN_00AA2590`. `FUN_00AA2590` has multiple callers, including `FUN_00AB3210`, `FUN_00A74030`, `FUN_00C215B0`, `FUN_00C28CF0`, and `FUN_00B9E710`. These are separate call paths; their presence does not by itself identify the input event or selected object's class.
5. The exact `DisItemContext_UsePower` primary vtable has `+0x134 -> FUN_00C44D30` and `+0x188 -> FUN_009EA9D0`. Raw `FUN_00C44D30` instructions read a float from `[EBP+8]` and return with `RET 4`; `FUN_009EA9D0` returns 1 and also uses `RET 4`. `FUN_00C04C30` does not explicitly push a parameter for slot `+0x134`, so the static call site is not ABI/prototype-matched to this UsePower implementation on current evidence. The matching slot number is insufficient to attribute the dynamic receiver to UsePower.
6. The `FUN_00C04C30` route is therefore a concrete context-manager dispatch candidate, but not yet the missing Blink activation edge. If its selected object were `DisItemContext_UsePower`, the direct call to slot `+0x134` would be relevant; however the receiver vptr and effective argument contract have not been proven, and the ABI discrepancy weighs against assuming that identity.
7. No direct `FUN_00C04C30` caller is `Dis_SelectPower`, `FUN_00AB4680`, `FUN_00CF34E0`, or a known Blink function. The candidate route must remain separate from the already established selection and Blink move-mode branches.
8. `FUN_00C0B2A0`, called by the same manager-selection helpers, scans the `+0x38/+0x3C` array at 0x0C-byte stride. For each record it requires a nonzero DWORD at `+4`, accepts the byte at `+8` when it is zero or equals the requested qualifier, and checks whether the supplied object's `+0x44` link chain contains the pointer at record `+4`. On a match it can return the record address through an output parameter and returns the array index. This narrows the record's observed fields to a first-DWORD selected object, a second-DWORD chain anchor, and a qualifier byte; semantic names and any identity with `DisItemContext_UsePower` remain unproved.
9. Raw instructions in `FUN_00AB3210` confirm it uses the same receiver field: at `0x00AB325A` it loads `ECX=[ESI+0x59C]`, then calls `FUN_00C04BD0` with the requested index; later at `0x00AB32A1` it reloads the same manager and calls `FUN_00C11B50`. On its accepted branch it calls `FUN_00AA2590` with ECX still holding the outer `ESI` object. This ties the selected-context lookup and `AA2590 → C04C30` dispatch to one controller-like operation path. The class owner of `FUN_00AB3210` and whether this branch is the player's power-use input remain unproved.

## Evidence classification

- **Confirmed:** the `FUN_00AB3210`/`FUN_00AA2590` machine-level use of the same `this+0x59C` manager field; the context index lookup through `FUN_00C04BD0`; selected-index/data/count offsets and 0x0C entry stride; the record reads and object-chain comparison in `FUN_00C0B2A0`; the two virtual calls and their conditions in `FUN_00C04C30`; UsePower's actual slot targets and callee-cleanup sizes.
- **Supported interpretation:** `this+0x59C` at the `FUN_00AA2590` call site is a context-manager-like object, and its selected objects receive a virtual status/use-style callback.
- **Unknown:** the manager's native/reflected class, source/meaning of its selected objects and channel indices, runtime vptr in the array, effective ABI compatibility with UsePower, which caller corresponds to the player's Use action, and whether this route reaches Blink.

## Next analysis

1. Identify constructors/initializers that populate the manager at the call site's `this+0x59C` and the 0x0C-stride entries at manager `+0x38`.
2. Trace `FUN_00C17D10` callers back to the object insertion path; test whether a configured `DisItemContext_UsePower` pointer can reach that array.
3. Recover raw caller/callee stack behavior for the selected `+0x134` and `+0x188` implementations before assigning them UsePower semantics.
4. Join this path to Blink only if the selected receiver's vptr resolves to `DisItemContext_UsePower` and its arguments match the implementation contract.
