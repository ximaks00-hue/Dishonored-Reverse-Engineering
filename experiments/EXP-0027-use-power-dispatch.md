---
id: EXP-0027
title: UsePower dispatch and Blink activation boundary
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can UsePower/CastBlink configuration be joined to the Blink move-mode setter, and is nearby pointer data a live table?"
---
# EXP-0027 — UsePower dispatch and Blink activation boundary

- Status: package metadata, the conditional `UsePower`-to-Blink move-mode bridge, and a slot-compatible generic context dispatcher are confirmed. The object class at the dispatch site and the input/event edge remain unresolved.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; inspected through read-only MCP calls (decompile, raw memory reads, xrefs, disassembly searches).
- Package: decompressed analysis copy documented in EXP-0025; no game files or Ghidra program data were changed. `_excluded_coop_project/` was not accessed.

## Question

Can the known package-side `DisItemContext_UsePower` / `CastBlink` configuration be connected to the native path that switches the Blink component to `EBM_BlinkMove`? Is the pointer sequence near `0x011BD230` an established dispatch table?

## Findings

### 1. The `0x011BD230` region remains unattributed

`FUN_00CF34E0` calls `FUN_00CF3360` and then `FUN_00BFC990`. The pointer to `FUN_00CF34E0` is present at `0x011BD254`, with `FUN_00CF3540` at the next entry `0x011BD258`. A raw image search found no absolute occurrences of the candidate table base `0x011BD230` or either entry address, and Ghidra found no direct code caller for `FUN_00CF34E0`.

This is bounded negative evidence only. It weakens the active-table interpretation but does not exclude relative addressing, computed pointers, runtime initialization, or indirect dispatch. The owner and use of the region are unknown; it is not called a callback table here.

### 2. A Blink-vtable virtual chain reaches move-mode entry

The Blink constructor `FUN_00BF9A10` installs vtable `0x01168698`. Raw bytes at `0x011689D8` (`0x01168698 + 0x340`) resolve to `FUN_00BE89E0`.

The decompiled body of `FUN_00BE89E0` has this conditional sequence on the same object:

1. Call virtual slot `+0x160`; if it returns nonzero, clear two fields at indices `0x24` and `0x25` and return `1`.
2. Otherwise call virtual slot `+0x18C`; if that returns nonzero, call slots `+0x178` and then `+0x1AC`, and return `1`.
3. Otherwise return `0`.

The Blink vtable resolves the latter slots as:

| Slot | Table entry | Target | Observation |
|---|---:|---|---|
| `+0x160` | `0x011687F8` | `0x00AE3DD0` | Raw bytes are `8B 81 A0 00 00 00 83 E0 01 C3`: load `[ECX+0xA0]`, mask bit 0, return. Ghidra has no function object at this address, so this is an instruction-level observation; the flag meaning is unknown. |
| `+0x18C` | `0x01168824` | `FUN_00BF3060` | Guard that reads component/tweak-related state and returns a boolean-like result; exact property semantics remain unresolved. |
| `+0x178` | `0x01168810` | `FUN_00BF32F0` | Performs component/tweak-related setup and calls `FUN_00BF30C0`; exact role is not named. |
| `+0x1AC` | `0x01168844` | `FUN_00BFC990` | On its successful branch sets the Blink mode byte at `this+0xC9` to `1`, which package enum `EBM_BlinkMode` labels `EBM_BlinkMove`. |

Therefore, the executable contains a statically resolved *virtual dispatch sequence* from Blink slot `+0x340` through the conditional calls above to the move-mode entry. This is a new upstream candidate for the move-mode transition, distinct from the unattributed `FUN_00CF34E0` pointer sequence.

### 3. A concrete indirect caller exists, but is not a Blink activation edge

Ghidra's direct call graph reports no direct code caller for `FUN_00BE89E0`; the function is referenced as a table target. A bounded search for reads of slot offset `+0x340` found indirect call sites in generic functions.

One concrete site is in `FUN_00652CF0`: at `0x00653223` it loads `[param_2->vtable + 0x340]`, then calls the loaded target at `0x0065322B`. After setting object flags, iterating a pointer array, invoking several virtual methods and running cleanup/list-management code, it reaches this call only when `DAT_0141295C != 0` and `FUN_00784580()` returns zero. The call's receiver is `param_2`. The function's broader body is consistent with generic object/actor lifecycle processing, but the object's exact class and the semantics of slot `+0x340` at this call site are not established. It does not prove a Blink receiver or a user-Use event.

An additional path into this generic helper is `FUN_00BF8DD0`, which calls `FUN_00652CF0(*(this+0xB0), 0, 1)` when its second argument is zero and the field at `this+0xB0` is nonzero, then clears that field. Its remaining calls include `FUN_00BF66A0(0)` and `FUN_0057AA70(param_2)`. A vtable-like pointer sequence around `0x011685C0` contains `FUN_00BF8DD0` at `+0x2C` (`0x011685EC`), but no xref to the sequence start or direct code caller of `FUN_00BF8DD0` was found. The observed field cleanup makes a lifecycle/cleanup role plausible, not proven. Neither the receiver of the nested `+0x340` dispatch nor its relationship to Blink movement is known.

The same function pointer `FUN_00BE89E0` also appears at data address `0x011C58E0`, in a second table whose owner was not identified; no xref to the presumed table start `0x011C55A0` was recovered. This shared target further cautions against treating `FUN_00BE89E0` as Blink-specific. Another inspected routine, `FUN_007589C0`, copies vector-like fields and dispatches through `+0x340`, also consistent with a generic helper. The bounded search does not rule out other call sites or runtime event dispatch.

Raw table comparison adds a limited family clue: the candidate second table begins at `0x011C55A0`, and its `+0x340` entry matches Blink's `0x01168698 + 0x340`. Starting there, both tables contain the same 17 consecutive 32-bit targets through relative offset `+0x380`; their next entries diverge. The inspected DarkVision table at `0x01168870` has `FUN_00459D10`, not `FUN_00BE89E0`, at its `+0x340` slot. Thus the second table shares a substantial method run with Blink and is not the inspected DarkVision table at that slot. This does not identify the second table's class or prove runtime use.

The package evidence in EXP-0025 still establishes only that `DisTweaks_UsePower` spawns `DisItemContext_UsePower`, and Blink's configured use action names animation state `CastBlink` with movement/look/interrupt flags. It does not identify which native callback/event invokes Blink slot `+0x340` or `FUN_00BFC990`.

### 4. A nearby active-power path is specifically DarkVision, not Blink

`FUN_00CAED80` walks the active-power pointer array at the local-player structure's `+0x788`, checks each component's class chain against descriptor `DAT_0146F268`, and calls `FUN_00BE8A50` for a matching component. The descriptor is initialized by `FUN_00BF3000` from the UTF-16 class name `DishonoredActivePowerComponent_DarkVision`.

`FUN_00BE8A50` eventually invokes that component's virtual slot `+0x1AC`. The DarkVision constructor `FUN_00BFBC00` installs vtable `0x01168870`; its `+0x1AC` target is `FUN_00BF82A0`, not Blink's `FUN_00BFC990`. This caller therefore demonstrates a component-family dispatch pattern, but it is not a Blink activation edge and must not be used to attribute `FUN_00BE8A50` to Blink.

### 5. `Dis_SelectPower` changes selection/state; no activation edge was found

Re-decompilation of the exact `DishonoredPlayerController` target `FUN_00AB4680` confirms that `_iPower` indexes the mapping at pawn `+0xA40/+0xA44`. The mapped integer is compared with the value returned by pawn virtual slot `+0x6EC`; equality follows an early state/notification path. After eligibility checks, the mapped integer is passed to pawn slot `+0x6E8` with flag `0x10`. This body contains no direct call to `FUN_00BFC990`, `FUN_00BE89E0`, or `FUN_00652CF0`.

The resolved pawn table maps `+0x6E8` to `FUN_00B4D320`, which bounds-checks against a count at `+0x78C` and dispatches slot `+0x6E4` (`FUN_00B56060`). That target checks the selected pointer from the array at `+0x788`, calls `FUN_00C4BA70` on it, and, if that check succeeds, calls `FUN_00B51790` with manager pointer `[FUN_00C0B4A0(...)+0x30]`, numeric state argument `2`, and the supplied flag. `FUN_00B51790` performs further validity checks and dispatches manager slot `+0x5C8`, then updates an 8-byte-entry state array.

The observed dataflow supports a selection/active-power state transition, but the meanings of state value `2`, the getter at `+0x6EC`, manager slot `+0x5C8`, and `FUN_00B51790` are not fully named. No direct edge from this chain to Blink move-mode entry was found. This strengthens the separation between `Dis_SelectPower` and the still-unresolved Use/activation dispatch; it does not establish that selection can never trigger later indirect processing.

The controller's state handler `FUN_00AB7D30` also calls adjacent helper `FUN_00AB47D0` at `0x00AB7E08`, passing the byte at controller `+0x631` after state/timer checks. For values not handled by its special cases, `FUN_00AB47D0` scans the pawn's array at `+0x788` and compares each pointed-to object's byte at `+0x74` with the passed value; on a match it calls pawn slot `+0x6E8` with the array index and flag `0x10`. This gives a concrete controller-state → mapped active-power selection path. The meaning of controller byte `+0x631` and whether this routine responds to Use or only selection/state refresh remain unresolved; it still does not reach Blink move-mode code directly.

The value flow can be traced one step further. `FUN_00C4BA70` verifies that a component belongs to the active-power list, records the matched array index and component pointer in a related state object, then loads the byte at `component+0x74`. At `0x00C4BC85`–`0x00C4BC8F`, it loads controller pointer `DAT_0145F614` into ECX, pushes that byte, and calls `FUN_00AA0A90`. `FUN_00AA0A90` copies `controller+0x632` to `controller+0x631`, then stores the new byte at `+0x632`. `FUN_00AB7D30` later reads `+0x631` and can pass it to `FUN_00AB47D0`, which searches the active-power list for a component with the same `+0x74` byte and re-selects its index through pawn slot `+0x6E8`.

This establishes a round-trip between a component byte and the controller's previous/current selection bytes, plus a reverse lookup to the active-power array. The package declares a component property `m_eUISelection` of enum type `eDisUISelectionType`, and Blink's default sets it to enum value `2`; `component+0x74` is therefore a strong candidate for that property. The exact property-offset join is still an inference because the UELib reflection output does not expose native offsets. The path does not show that the same value triggers the `UsePower` context or Blink movement.

### 6. Adjacent state-update candidate does not close activation

`FUN_00BF30C0` is called by both the selection-state helper `FUN_00C4BA70` and Blink method `FUN_00BF32F0`. It walks a manager-owned array, filters entries by flags and an identifier, and invokes their virtual slot `+0x18C` with output data. Another caller, `FUN_00CF64B0`, has only a data reference at `0x011CD1D8` in an unattributed pointer table and no direct code caller; its body runs `FUN_00CF6370`, effect/timing code, and then `FUN_00BF30C0`. Neither examined body directly calls `FUN_00BFC990`, `FUN_00BE89E0`, or `FUN_00CF34E0`. The shared update routine may be a useful state-notification path, but its owner and relation to UsePower are unknown.

### 7. PlayerController shortcut `Use` handlers lead into shortcut/UI state

The exact PlayerController vtable maps keyboard shortcut `Use` slot `+0x510` to `FUN_00AA0950` and gamepad shortcut `Use` slot `+0x508` to `FUN_00AA0860`. `FUN_00AA0950` conditionally clears/sets the pending shortcut bitmask at `+0x648` and records its index at `+0x64C`; `FUN_00AA0860` clears the corresponding bit and updates `+0x64C` from the remaining bitmask. Neither function calls `Dis_SelectPower`, `DisItemContext_UsePower`, or Blink code directly.

The controller state handler `FUN_00AB7D30` is called from `FUN_00ABA900` and consumes `+0x610/+0x648/+0x64C/+0x650/+0x658`. Its direct callees include shortcut-array helpers `FUN_00BBD090` / `FUN_00BBD180`, assignment handler `FUN_00BC3400`, Scaleform selection methods `FUN_00BC35E0` / `FUN_00BC36C0`, and UI routine `FUN_00BE4280`. In the observed state branch it calls `FUN_00BE4280(2, controller+0x64C, 0)`. For mode `2`, `FUN_00BE4280` calls `FUN_00BC35E0` with the slot index and then `FUN_00BE2BB0`; that routine sends the Scaleform command `OpenShortcuts`. The same routine sends `_root.bIsPCShortcuts` and `_root.shortcutsPC_mc` data to Scaleform. Another mode path opens the power wheel with the Scaleform command `OpenWheel`. These are direct UI/shortcut transitions; the examined native bodies do not directly invoke `FUN_00BFC990`, `FUN_00BE89E0`, or `FUN_00AB4680`. A later external UI callback or indirect engine event is not excluded.

The exported ActionScript for `powerwheel.gfx` was checked directly in `.tmp/ffdec-26.4.0/powerwheel-scripts/`. Root `OpenShortcuts(bInWheel)` in `scripts/frame_1/DoAction.as` selects `shortcutsPC_mc.Open(bInWheel)` or `shortcuts_mc.Open()` and enables non-PC shortcut inputs; root `SetShortcutSelection(shortcutIdx)` only forwards the slot index to the corresponding shortcut movieclip. In `scripts/__Packages/_powerWheel/PC_ShortcutsHandler.as`, `MouseWheel_up/down` call `_root.SetShortcutSelection(slot)`, while `DockBarPressed` calls `_root.AssignShortcut(slot)`. The regular shortcut handler's `SetShortcutSelection(idx)` only changes `_selSlotIdx` and selection visuals. These inspected methods contain no external power-use callback. This confirms that the specific `OpenShortcuts` / selection-forwarding path is UI navigation and assignment. It does not cover native input processing outside these ActionScript methods or prove that all Scaleform callbacks in the full movie are absent.

The GFX is a binary export at `assets/extracted/ui_powerwheel/UI_PowerWheel_SF/SwfMovie/powerwheel.gfx`; the ActionScript is a separate FFDec decompilation artifact. The broader EXP-0019 census of 85 exported ActionScript files found no `onUse`, `UsePower`, or `SelectPower` token and no `Dis_SelectPower`/`SelectPower` calls. Together these checks narrow the Scaleform shortcut UI as a source of the activation edge, while leaving native or animation-event dispatch open.

## Evidence classification

- **Confirmed from package data (EXP-0025):** native `DisItemContext_UsePower`; `DisTweaks_UsePower` spawn-class link; Blink use-action animation state `CastBlink` and configured flags.
- **Confirmed from the exact-build executable:** Blink constructor/vtable mapping; slot `+0x340` → `FUN_00BE89E0`; the conditional virtual calls in that function; targets of Blink slots `+0x18C`, `+0x178`, and `+0x1AC`; `FUN_00BFC990` sets mode value `1` on its successful branch; the raw slot `+0x160` bytes implement a bit-0 check on `[this+0xA0]`; `FUN_00652CF0` loads a virtual target from receiver slot `+0x340` at `0x00653223` and calls it at `0x0065322B` under the stated conditions; `FUN_00BF8DD0` conditionally calls `FUN_00652CF0` using the pointer at `this+0xB0` and clears that field.
- **Confirmed differential attribution:** the inspected `FUN_00CAED80` active-power loop filters `DishonoredActivePowerComponent_DarkVision`; its `+0x1AC` target differs from Blink's, and its `+0x340` target is `FUN_00459D10`, not `FUN_00BE89E0`.
- **Confirmed selection-path boundary:** `FUN_00AB4680` maps `_iPower`, compares via slot `+0x6EC`, and after checks calls pawn slot `+0x6E8`; that target dispatches `+0x6E4` and passes through `FUN_00B56060` / `FUN_00B51790` to a state manager. The examined bodies have no direct call to Blink's move-mode path.
- **Confirmed controller-state selection path:** `FUN_00AB7D30` conditionally passes controller byte `+0x631` to `FUN_00AB47D0`; that helper can match the value against entry field `+0x74` in the pawn's `+0x788` array and dispatch the matching index through slot `+0x6E8`.
- **Confirmed selection-ID value flow:** `FUN_00C4BA70` passes active component byte `+0x74` to controller setter `FUN_00AA0A90`; that setter shifts current byte `+0x632` to previous byte `+0x631` and stores the new byte. The state-handler lookup can map the previous byte back to an active-power index.
- **Bounded update-routine triage:** `FUN_00BF30C0` enumerates matching manager entries and dispatches slot `+0x18C`; the inspected `FUN_00CF64B0` caller reaches this routine but contains no direct move-mode call. Its table owner and event remain unknown.
- **Confirmed shortcut-Use boundary:** controller slots `+0x510/+0x508` reach `FUN_00AA0950/FUN_00AA0860`, which update shortcut index/bitmask fields; the state handler routes those fields through shortcut-array and Scaleform UI routines. Its mode-2 branch calls `SetShortcutSelection` and `OpenShortcuts`. The examined path contains no direct call to `Dis_SelectPower` or Blink move-mode methods.
- **Confirmed within the inspected Scaleform methods:** `OpenShortcuts` opens the shortcut movieclip and `SetShortcutSelection` forwards a slot index; the PC handler routes mouse-wheel navigation to this method and dock-key presses to assignment. These methods contain no power-use callback. Combined with the bounded 85-script search in EXP-0019, no ActionScript activation edge was identified; native/animation dispatch remains possible.
- **Bounded negative evidence:** no direct caller for `FUN_00BE89E0` / `FUN_00CF34E0` in Ghidra's call graph; no absolute pointer occurrence for the candidate `0x011BD230` region in the mapped image; the inspected `+0x340` call sites did not identify a proven Blink receiver.
- **Unknown:** whether slot `+0x340` is dispatched by a tick, animation, item-use callback, or another engine event; how `DisItemContext_UsePower` and `CastBlink` reach it; the meaning of Blink field `+0xA0` bit 0 and exact roles of `FUN_00BF3060` / `FUN_00BF32F0`; whether this sequence is the normal user-initiated activation path.
- **Unknown:** the semantic meanings of `Dis_SelectPower`'s mapped values, slot `+0x6EC`, manager state value `2`, slot `+0x5C8`, and whether later state-machine dispatch reaches a power-use method.
- **Unknown:** what user action or state-machine event causes the previous/current selection bytes to be set and replayed; in particular, whether this path corresponds to the user-facing Use action or only selection/state refresh.
- **Unknown:** whether any Scaleform callback or indirect engine event after the shortcut/UI state path starts `DisItemContext_UsePower`, or whether a distinct input callback owns power activation.
- **Strong inference:** component byte `+0x74` is the package property `m_eUISelection`; the byte value `2` for Blink may therefore be the component identifier copied into controller `+0x632`. No property layout offset is available to promote this join to confirmed.

## Updated model

```text
User Use / item-use event
    └── unresolved context creation and event source
          └── manager entry receiver pointer at +0x1E0 (dynamic class unknown)
                └── candidate dispatcher FUN_00C0CA70
                      ├── virtual +0x184
                      └── virtual +0x134
                            └── if receiver is UsePower:
                                  FUN_00C4B800 → FUN_00C44D30
                                    └── guarded component virtual +0x174
                                          └── Blink FUN_00BE7580
                                                └── manager +0x270(1)
                                                └── Blink +0x1AC → FUN_00BFC990
                                                      └── conditional EBM_BlinkMove
                                                            └── EXP-0024 update/trace path
                                                                  └── conditional pawn position write

Separate Blink branch, not yet joined to the user event:
candidate dispatch through Blink slot +0x340 → FUN_00BE89E0
    → conditional Blink slot +0x1AC → FUN_00BFC990
```

The UsePower vtable targets and the conditional internal Blink route are established. `FUN_00C0CA70` is only slot-compatible: the object's runtime class and the incoming user event are unproved. The slot `+0x340` route remains a separate branch with no demonstrated connection to the UsePower route or normal input. EXP-0024 independently establishes the conditional movement/write path; the same runtime instance has not been joined across the routes.

## Next work

1. Resolve the class and producer of objects stored at manager-record offset `+0x1E0` in `FUN_00C0CA70`; establish whether any has the `UsePower` vptr and how the record key at `+0x1D4` is populated.
2. Trace `FUN_00C2E840`, `FUN_00C2EA00`, `FUN_00C316E0`, and `FUN_00C35AF0` to their owning classes and event sources. Determine whether any call path corresponds to animation-state `CastBlink` or user-triggered use.
3. Preserve the separate Blink slot `+0x340` branch and continue recovering its second table's owner and the object stored at `this+0xB0` in `FUN_00BF8DD0`.
4. Resolve the state manager receiver and slot `+0x5C8` reached through `Dis_SelectPower`; test whether its later dispatch invokes any power-use or Blink method.
5. Inspect constructors and field initialization for Blink `this+0xA0`, plus the exact conditions in `FUN_00BF3060` and `FUN_00BF32F0`, without assigning names from behavior alone.
6. Keep the Scaleform shortcut operations classified as UI/assignment; continue searching native item-context and animation-event paths for activation.
7. Identify the owner of the data-table entry at `0x011CD1D8` only if it can be linked to the active-power/use context; otherwise retain it as unowned.
8. Keep `FUN_00CF34E0` and `0x011BD230` as separate unresolved leads until an owner/reference path is recovered.
9. Join activation to EXP-0024 only after dataflow proves the same Blink instance and owner pawn.
