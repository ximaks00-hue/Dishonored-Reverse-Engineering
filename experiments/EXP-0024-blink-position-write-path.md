---
id: EXP-0024
title: "Blink movement path to owner-pawn position write"
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "Is there a static Blink path that writes the owner pawn position?"
---
# EXP-0024 — Blink movement path to owner-pawn position write

- Status: a Blink update path from the Blink component vtable to a location-writing helper on its owner pawn is confirmed statically. The initiating player-input/activation edge remains unresolved.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra project: `dishonored_exact_full`, x86, image base `0x00400000`; read-only decompilation, disassembly, and memory reads.
- Scope: static inspection only. No game files or Ghidra program data were changed. `_excluded_coop_project/` was not accessed.

## Recovered call/data path

1. The `DishonoredActivePowerComponent_Blink` constructor `FUN_00BF9A10` installs vtable `0x01168698`. Its slot `+0x13C` contains `FUN_00BFC5D0`.
2. `FUN_00BFC5D0` dispatches on the component byte at `this+0xC9`. In case `1`, it calls `FUN_00BFC160`. The package enum declares value `1` as `EBM_BlinkMove`; the field-to-name join is supported by the byte offset and class declaration, while the dispatch itself is directly visible in the binary.
3. `FUN_00BFC160` updates Blink step state and calls `FUN_00BECDF0` with a candidate position. The Ghidra database reports one direct code caller of `FUN_00BECDF0`: `FUN_00BFC160`.
4. `FUN_00BECDF0` repeatedly performs collision/trace work through `FUN_00BE1560` and evaluates candidate positions relative to the owner pawn. On its accepted path it calls `FUN_006539C0`. Raw instructions at the call site load the owner-pawn pointer from the Blink component's `+0x48` field and pass a candidate vector; the world/context object is placed in ECX.
5. Raw arguments at the call from `FUN_00BECDF0` are: ECX receives the world/context pointer; the first stack argument is the owner pawn; the second is the candidate vector; the next three are `0`, `1`, and a float global. This matches the decompiler's `FUN_006539C0(param_1, param_2, param_3, param_4, param_5, param_6)` with pawn in `param_2` and candidate vector in `param_3`.
6. `FUN_006539C0` does **not** write coordinates unconditionally. It checks actor flags and current location, and its `param_5 == 0` cases run additional validation. For the call observed from `FUN_00BECDF0`, `param_5` is `1`, so that validation branch is skipped; the helper still tests the result of `FUN_00643E40` when `param_4 == 0` and the actor flag at `pawn+0x128` lacks bit `0x10`. Its final movement branch also requires its internal validity value to remain nonzero. When that branch proceeds, it writes the vector components to `[pawn+0xC4]`, `[pawn+0xC8]`, and `[pawn+0xCC]` (`MOV` instructions at `0x00653DF4`, `0x00653DFA`, `0x00653E00`), then continues through actor virtual callbacks/state updates.

This gives a direct static path from a Blink-class update in move mode, through candidate tracing and a conditionally accepted generic helper, to writes of the owner pawn's position fields. The calls and stores are evidence of a movement path, but not proof that every candidate is accepted. The names `SetLocation` or `teleport` are not assigned to the helper because its engine-level contract has not been independently named.

## Move-mode entry candidate

Blink vtable slot `+0x1AC` points to `FUN_00BFC990`. In its successful branch this function sets the byte at `this+0xC9` to `1`, after setting up ability state and checking a target distance. Its other branch calls `FUN_00BFAB80(1)`. The package enum labels mode `1` `EBM_BlinkMove`, so `FUN_00BFC990` is a concrete move-mode entry candidate.

`FUN_00CF34E0` calls `FUN_00BFC990`, and its pointer appears in a data table at `0x011BD254`; the code/data owner and the gameplay event that dispatches this table entry are not established. Therefore this evidence does **not** prove that PlayerController shortcut `Use`, PowerWheel selection, or `Dis_SelectPower` activates Blink.

## Relation to Blink tweak values

EXP-0023 resolves the Blink tweak-interface getter to the component field at `+0x8C`, strongly mapped to base property `m_pPowerTweaks`, and shows that the Blink component default points to `Twk_Powers.Blink.Twk_Blink`. `FUN_00BF9AB0`, called from the Blink update path, indexes that returned object using a level value from `+0x88` and reads fields at offsets consistent with the beginning of `PowerAttributes_Blink` records. These values feed spatial candidate/distance checks. The exact record layout remains unresolved because native stride is `0x38`, while the full serialized struct declaration is `0x4C`.

## Evidence classification

**Confirmed by binary evidence:** Blink vtable slot `+0x13C` → `FUN_00BFC5D0`; mode value `1` dispatches to `FUN_00BFC160`; `FUN_00BFC160` calls `FUN_00BECDF0`; that helper has collision/trace work and calls `FUN_006539C0` with the owner-pawn pointer and candidate position; `FUN_006539C0` writes the candidate's three coordinates to the pawn's `+0xC4/+0xC8/+0xCC` fields only when its validation and movement conditions pass. Blink vtable slot `+0x1AC` → `FUN_00BFC990`, which sets mode value `1` on its successful branch.

**Strong inference:** the owner-pawn field at component `+0x48` is `m_pOwnerPawn`; the position fields at pawn `+0xC4/+0xC8/+0xCC` are its location; the step/trace path implements Blink's in-motion movement, with the tweak-driven distance checks described in EXP-0023.

**Unknown:** which input or active-power callback dispatches `FUN_00BFC990`; how the controller's `Use` state reaches that callback; whether the collision helper always accepts the proposed vector under all game states; the final destination-selection policy; and how the `0x38` native record maps to the serialized `PowerAttributes_Blink` properties.

## Next work

1. Establish whether the pointer sequence containing `FUN_00CF34E0` / `FUN_00CF3540` is used at all; EXP-0025 found no direct code caller or absolute address reference to the sequence or these entries. If its use cannot be established, deprioritize it and search for another activation edge.
2. Trace PlayerController shortcut `Use` and the active-power state manager through any indirect callbacks until they reach a Blink-specific entry, or document that the path remains unresolved.
3. Resolve the native level-record layout and separately inspect the final candidate/trace acceptance conditions in `FUN_00BECDF0`.
