# EXP-0047 — User Use event to UsePower/Blink activation

**Status: proposed, separate from EXP-0046; not executed here.** Build SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (verify against local EXE and Ghidra program).

## Goal

Establish an authentic event/call edge from keyboard/gamepad Use to a runtime `DisItemContext_UsePower` instance or proven Blink activation receiver. Existing static bridge `DisItemContext_UsePower +0x134 → FUN_00C44D30 → Blink +0x174/FUN_00BE7580 → Blink +0x1AC/FUN_00BFC990` is conditional and lacks upstream provenance.

## Procedure

1. Start from actual input bindings and engine event dispatch, not UI-only `SetShortcutSelection`. Preserve raw mapping from input action to receiver and event.
2. Verify UsePower context constructor/vtable, instantiation via `DisTweaks_ItemPowers/DisTweaks_UsePower`, pointer insertion and retrieval from runtime Pawn/Controller managers.
3. Confirm the runtime class at virtual `+0x134` call and the ABI/stack for that specific callsite. Earlier `FUN_00C04C30` mismatched the `RET 4`/float contract of known UsePower implementation; do not restore it as identified dispatch on slot similarity alone.
4. Distinguish path via `FUN_00C0CA70` and independent Blink `+0x340` entry; prove real receiver or leave alternative.
5. Trace flags/state through Blink `+0x174 → +0x1AC`; distinguish mode 1 success and mode 3 failure branch.
6. Join state transition to movement only after demonstrating actual input path and intended Pawn position update.

## Exit

Full, reproducible event → concrete context object → exact virtual callsite → Blink receiver → mode transition with static primary evidence; then independently runtime test on trusted clean installation. Until then E7 remains OPEN.
