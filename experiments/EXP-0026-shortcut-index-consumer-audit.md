---
id: EXP-0026
title: "Controller shortcut-index consumer audit"
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do consumers of the controller shortcut index reach power activation?"
---
# EXP-0026 — Controller shortcut-index consumer audit

- Status: inspected consumers update or navigate shortcut-selection state; no direct power-use/activation edge was found in this path.
- Date: 2026-10-26.
- Binary/Ghidra: exact-build `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; database `dishonored_exact_full`, x86, image base `0x00400000`.
- Scope: read-only Ghidra decompilation, call-graph lookup, and disassembly-text searches for accesses to controller fields `+0x228` and `+0x238`. No game files or Ghidra program data were changed; `_excluded_coop_project/` was not accessed.

## Relevant observed functions

1. `FUN_00BBD090(controller, index)` selects the 4-entry or 10-entry byte array at controller `+0x208` or `+0x20C`, depending on a mode bit at `+0x218`. If the index is in range and the relevant flags are enabled, it copies that array byte to `controller+0x228` and saves the index at `controller+0x238`.
2. `FUN_00BBD0F0(controller, direction)` starts from `controller+0x238`, wraps through the same 4- or 10-entry array, skips zero-valued entries, and returns the next nonzero index. It does not call the power-selection target.
3. `FUN_00BB9DF0(controller, value)` scans the shortcut byte array for a matching value and stores its index in `controller+0x238`; if there is no match, it stores zero.
4. `FUN_00BBD180(controller, value)` calls the matching-index helper and, when found, copies the byte from the shortcut array to `+0x228` and the matching index to `+0x238`.
5. `FUN_00BC3400(controller, index)` handles assignment: it changes a shortcut-array byte, invokes Scaleform `AssignShortcut`, clears duplicates, and adjusts the saved index if a duplicate slot was cleared.
6. Controller state handler `FUN_00AB7D30`, called by `FUN_00ABA900`, calls `FUN_00BBD090`, `FUN_00BBD180`, `FUN_00BC3400`, and Scaleform shortcut-selection helpers. Its direct call graph does not include `FUN_00AB4680` (`Dis_SelectPower`) or `FUN_00BFC990` (Blink move-mode entry).
7. Another read of `controller+0x238` occurs in `FUN_00AAFEB0`; the shown body uses the value to choose an argument for a helper and stores helper results at `+0x230`/`+0x1C4`. It does not directly call `Dis_SelectPower` or Blink code. The full semantic contract of this routine is not identified.

## Conclusion

The indexed consumers examined here implement shortcut-array navigation, lookup, assignment, and UI/state refresh. The mapped byte at `+0x228` and index at `+0x238` therefore remain shortcut state; their conversion into `_iPower` or an active-power use request is not established. No direct call from this controller state path to `FUN_00AB4680` or `FUN_00BFC990` was found, but this does not rule out engine dispatch, unexamined consumers, or callback indirection.

## Evidence classification

- **Confirmed:** the described reads/writes and array navigation in the cited functions; the direct call-graph edge `FUN_00ABA900` → `FUN_00AB7D30`; absence of `FUN_00AB4680` and `FUN_00BFC990` from `FUN_00AB7D30`'s direct callees.
- **Unknown:** the semantic domain of values stored in `+0x208/+0x20C` and `+0x228`; whether an indirect event path uses `+0x238` to activate a power; how keyboard/gamepad `Use` eventually starts `DisItemContext_UsePower`.

## Next work

1. Trace all call sites/indirect dispatch for the item-use context and `DisItemPowers` item object, rather than treating shortcut selection as activation.
2. Identify the native callback or animation event that enters Blink vtable slot `+0x1AC` / `FUN_00BFC990`.
3. Keep UI wheel ID, selection branch code, controller shortcut bytes/index, `_iPower`, and active-power array index separate until a concrete value-flow edge connects them.
