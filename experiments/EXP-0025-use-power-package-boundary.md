---
id: EXP-0025
title: UsePower package boundary and Blink activation lead
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What package UsePower/CastBlink configuration exists, and is there a script edge to Blink move-mode?"
---
# EXP-0025 — UsePower package boundary and Blink activation lead

- Status: package metadata inspected; no package-script activation edge to Blink was found. Native dispatch remains unresolved.
- Date: 2026-10-26.
- Package: decompressed analysis copy `assets/extracted/dishonored-blink/DishonoredGame.upk`; SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`.
- Method: local UELib probe against the decompressed package. The UE Explorer MCP can search the compressed package's object index, but direct decompilation of the compressed package remains unavailable in the configured service.
- Scope: read-only package analysis. No game files were modified; `_excluded_coop_project/` was not accessed.

## Observations

1. UELib emits `DisItemContext_UsePower` as a native class extending `DisItemContext_AimAssistAttack`; the class body contains only `m_bLoopIsOver` and no script function body that calls a Blink method.
2. `DisTweaks_UsePower` is a native tweak class extending `DisTweaks_ItemContext`. Its `m_pSpawnedObjectClass` default is `Class'DishonoredGame.DisItemContext_UsePower'`.
3. The nested player-specific `DisTweaks_UsePower` object named `pPlayerUsePower` appears under `Default__DisTweaks_ItemPowers`. It inherits the `DisTweaks_ActivePowerBase` default `m_UsePowerAction`; in the Blink tweak object that action is configured with animation state `CastBlink`, `m_bCanMove=true`, `m_bCanLook=true`, and `m_bAllowSelfInterrupt=true`.
4. The Blink component CDO separately binds `m_PowerName="Blink"`, `m_eUISelection=eDisUISelectionType_Blink`, `m_bSustainedCast=true`, and `m_pPowerTweaks=Twk_Powers.Blink.Twk_Blink`.
5. Searches for `UsePower`, `ActivatePower`, `BeginUse`, and `UseActivePower` in the compressed package's object index exposed the related class/object names, but the local script decompilation did not expose a script call path from `DisItemContext_UsePower` or `pPlayerUsePower` to `FUN_00BFC990`.
6. Binary inspection reconfirmed that `FUN_00CF34E0` calls `FUN_00CF3360` and then `FUN_00BFC990`. Its address is stored at `0x011BD254`; the following entry at `0x011BD258` stores `FUN_00CF3540`. No direct code caller for `FUN_00CF34E0` was found. A raw byte search over the mapped program found no absolute occurrences of the little-endian addresses for the table base (`0x011BD230`) or these two entries (`0x011BD254`/`0x011BD258`). Thus the region is a sequence of function pointers, but its use as an active dispatch table is unproved and currently weakened by the missing absolute reference.

## Interpretation and limits

The package confirms that Blink's configured use action is associated with the `CastBlink` animation state and a player-specific use-power context. This is metadata/configuration evidence only. It does not prove that the context dispatches `FUN_00BFC990`, nor that `CastBlink` is the callback-table owner or entry at `0x011BD254`.

The native path remains stronger downstream: Blink vtable slot `+0x1AC` reaches `FUN_00BFC990`, which conditionally enters move mode; `FUN_00CF34E0` also calls it after `FUN_00CF3360`. The data region at `0x011BD230` contains adjacent function pointers, but no absolute reference to the region or either relevant entry was found in the mapped image. Calling it an active callback table would go beyond the evidence. See EXP-0024 for the downstream position-write path and its validation conditions.

## Evidence classification

- **Confirmed from package exports/defaults:** class inheritance, native annotations, `pPlayerUsePower` object path, Blink's `CastBlink` use-action state and flags, and the Blink component's tweak pointer.
- **Confirmed from binary:** `FUN_00CF34E0` → `FUN_00CF3360` → `FUN_00BFC990`; `FUN_00CF34E0` and `FUN_00CF3540` occupy adjacent pointer entries at `0x011BD254` and `0x011BD258`. Raw absolute-reference searches for the table base and these entries returned no results.
- **Observed bounded negative results:** no script body in the inspected package output links the use-power context directly to `FUN_00BFC990`; no direct code caller or raw absolute reference to the `0x011BD230` region or relevant entry addresses was found. Native dispatch through non-absolute/constructed references, omitted/failed object decompiles, other packages, and runtime event binding are outside these checks.
- **Unknown:** which native item/context callback starts Blink, how `CastBlink` triggers the callback-table entry, and how that path is reached from PlayerController keyboard/gamepad `Use`.

## Next work

1. Determine whether the pointer sequence around `0x011BD230` is referenced indirectly, generated at runtime, or is an unused/dead table; do not assume it is a callback table without a reference or owner.
2. Trace native item-context/use callbacks or animation-state events from `pPlayerUsePower` to Blink vtable slot `+0x1AC` / `FUN_00BFC990`.
3. Keep UI item ID 24, PowerWheel branch 2, controller `_iPower`, active-power array index 0, and use-context events separate until a dataflow edge connects them.
