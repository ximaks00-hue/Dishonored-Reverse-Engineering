# EXP-0027 — Input/use context to BlinkMove dispatch

Status: planned. Source: user narrative after REV-0006. This is NOT the user's primary local EXP-0025 or EXP-0026; those were not available in this GitHub branch.

## Objective

Establish actual event/caller that reaches native `FUN_00CF34E0 → FUN_00CF3360 → FUN_00BFC990` and causes Blink mode `1 (EBM_BlinkMove)`. Distinguish contextual `DisItemContext_UsePower` and animation `CastBlink` metadata from an executed native call chain.

## Prerequisites

- Verify exact 32-bit EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, base `0x400000`, Ghidra project hash and source-path caveat.
- Do not run unknown modified DLLs; do not edit game binaries; preserve current locked Ghidra project state.

## Static procedure

1. For `0x00CF34E0`, `0x00CF3360`, `0x00BFC990` collect function boundaries, direct and data xrefs, call/callind sites, address-taken uses, tail jumps and the exact arguments/state/guard conditions.
2. Examine bytes near `0x011BD230` as **an unidentified data region**. Check whether it has valid function pointers, relative offsets, vptr assignment or registration references; lack of direct absolute xrefs is a *negative search result*, not class evidence.
3. Trace construction and use of `DisItemContext_UsePower` and `CastBlink` from package metadata to native object ownership, handlers or asset callbacks, **only where supported by exact references**.
4. In `FUN_00AB7D30` and functions accessing controller `+0x238`, follow direct branches and *indirect consumers* of shortcut state (including `+0x228`). Separately trace keyboard/gamepad Use handlers and compare with Select: update-only vs ability activation.
5. Join to Blink method `FUN_00BFC990` using exact call/dispatch evidence. Then verify that move mode reaches prior conditional coordinate write path, not merely enum assignment.
6. Preserve alternatives (computed callbacks, thunk, event dispatcher, scripting or UI boundary) and explicit failures/coverage.

## Discriminating tests

- If `FUN_00CF34E0` appears solely in a function pointer record, identify who writes or indexes that record.
- If `0x011BD230` is not referenced, search context carefully: the data may be a false association. **Do not claim a callback table without constructor/registry and dispatch evidence.**
- If shortcut selection only updates UI state, isolate a separate use/cast dispatcher rather than invent a shortcut-to-Blink edge.

## Exit criteria

Verified class-context construction or listener, actual upstream event to `FUN_00CF34E0`, mode-transition branch and downstream movement chain with module-relative address and source evidence; otherwise leave the activation gap open. Store raw metadata-only evidence locally and commit only permissible notes.

## Namespace note

User local `EXP-0025-use-power-package-boundary.md` is distinct from the older GitHub `EXP-0025-blink-cast-and-position-proof.md` plan. Avoid accidentally replacing either with the other. IDs need reconciliation when originals can be synced.
