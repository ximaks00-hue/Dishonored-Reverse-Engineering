---
id: EXP-0021
title: Exact class vtables and native power selection
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What are the exact PowerWheel and PlayerController vtables/targets for selection callbacks?"
---
# EXP-0021 — Exact class vtables and native power selection

- Status: PowerWheel callback target and PlayerController `Dis_SelectPower` target resolved; selection-array path partially reconstructed. Ability activation and movement remain open.
- Date: 2026-10-26.
- Build: Steam app 217980, build 10256413, x86; exact executable hash is recorded in EXP-0013/EXP-0017.
- Scope: read-only inspection of the workspace executable bytes and the persisted Ghidra project/decompiler. No game files or Ghidra program data were changed. `_excluded_coop_project/` was not accessed.
- Address convention: Ghidra/PE virtual addresses (VA); image base `0x00400000`. RVA = VA − `0x00400000`.

## Question

Which concrete native methods receive the PowerWheel `OnSelectionChanged(int)` and PlayerController `Dis_SelectPower(int)` exec wrappers, and what can the targets establish about Blink selection?

## Evidence and procedure

Read-only Ghidra decompilation supplied the registration wrappers, constructor routines, and method bodies. A local read-only scan of the exact workspace EXE supplied raw descriptor/vtable DWORDs and UTF-16 class names. The exact executable identity is SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.

### PowerWheel owner and callback target

- The static descriptor at `0x01354070` contains class-name pointer `0x0115F72E`, which decodes as UTF-16 `DisGFxMoviePlayerPowerWheel`, and constructor pointer `0x00BD1080` at descriptor offset `+0x24`.
- Constructor `FUN_00BD1080` installs instance vtable pointer `0x01161C08` (`*this = &PTR_01161C08`). This directly ties the named class descriptor to the vtable.
- The wrapper registered for `DisGFxMoviePlayerPowerWheel.OnSelectionChanged` is `FUN_009F8290`; it parses one integer and dispatches through receiver slot `+0x1F0` (EXP-0019).
- The DWORD at `0x01161C08 + 0x1F0 = 0x01161DF8` is `0x00BCD800`. Therefore the concrete target is `FUN_00BCD800`.

### PowerWheel callback behavior

- `FUN_00BCD800` calls `FUN_00C3D360` to translate the callback item ID into a pair of values.
- For input item ID `24`, the selected pair is `(2, 0x1B)`. A subsequent range predicate accepts the resulting code `2`, and the handler calls `FUN_00BC3B00(2)` before storing the original callback ID at `this+0x228`.
- In the `2` branch, `FUN_00BC3B00` obtains the Blink class object through `FUN_00A81510`, which lazily returns the class represented by descriptor `0x0135A798` / name `DishonoredActivePowerComponent_Blink`. It walks the active-power array at global-object offset `+0x788`, compares class-chain membership, and prepares Scaleform `UpdateItemInfos` data.
- This proves a UI information-refresh path for the Blink wheel item. It does not show a call to `Dis_SelectPower`, a power-use method, or a position update.

### PlayerController owner and `Dis_SelectPower` target

- Descriptor record `0x01316938` contains the UTF-16 class name `DishonoredPlayerController` via pointer `0x01117192`, and constructor pointer `FUN_00ABD1F0` at `+0x24`.
- `FUN_00ABD1F0` installs main vtable `0x01118738`, plus secondary vptrs at object offsets `+0x534` and `+0x538`.
- Controller exec wrapper `FUN_009EE630` parses `_iPower` as one integer and dispatches through receiver slot `+0x560` (EXP-0014/0019).
- Vtable entry at `0x01118738 + 0x560 = 0x01118C98` is `0x00AB4680`. Thus `FUN_00AB4680` is the concrete `Dis_SelectPower` target for this class.

### Selection-index data path

Decompilation of `FUN_00AB4680` shows:

1. The object at controller offset `+0x248` is cast/tested as `DishonoredPlayerPawn` by `FUN_009FAD20`.
2. The function bounds-checks `_iPower` against the count at pawn offset `+0xA44` and reads a DWORD from the array at `+0xA40 + 4*_iPower`.
3. It compares this result with the value returned by a virtual call at pawn vtable slot `+0x6EC`; equality takes an early state/notification path.
4. After additional eligibility checks, it invokes pawn virtual slot `+0x6E8` with the loaded value and flag `0x10`.

For the identified `DishonoredPlayerPawn` table (`0x0111A3B0`), slot `+0x6E8` points to `FUN_00B4D320`; slot `+0x6E4` points to `FUN_00B56060`. `FUN_00B4D320` bounds-checks the index against a count at pawn offset `+0x78C` and dispatches slot `+0x6E4`. `FUN_00B56060` reads a pointer from the array at `+0x788 + 4*index`, checks it through `FUN_00C4BA70`, and then calls `FUN_00B51790` with a state value and the supplied flags.

`FUN_00C4BA70` compares the candidate component against entries reached through the pawn `+0xA40` mapping and the active-power pointer array at `+0x788`; on a match it updates state fields and calls another state helper. Package defaults independently establish Blink at `m_ActivePowers[0]` and `m_pBlinkPower` (EXP-0015). Taken together, these are strong evidence that `+0x788/+0x78C` is the active-power pointer array/count and `+0xA40/+0xA44` is an index mapping over it. UELib does not expose native field offsets, so this named-field join remains an inference rather than direct reflection-offset proof.

### Follow-up: selection state-manager update (read-only Ghidra recheck)

The exact-build recheck decompiled `FUN_00B51790`, its callers, and the pawn virtual targets. `FUN_00AB4680` calls `FUN_00B51790` with a special state value on the branch where the mapped `_iPower` value equals the result of pawn slot `+0x6EC`; otherwise, after its eligibility checks, it calls pawn slot `+0x6E8(mappedValue, 0x10)`. The confirmed pawn vtable routes this to `FUN_00B4D320`, which bounds-checks against `+0x78C` and calls slot `+0x6E4`; that target is `FUN_00B56060`.

`FUN_00B56060` obtains the active-power pointer at `pawn+0x788+4*index`, validates it via `FUN_00C4BA70(component, 0)`, then calls `FUN_00B51790(manager+0x30, 2, flags)` on success. `FUN_00B51790` performs object/state checks, invokes manager virtual slots `+0x5C8` and `+0x5EC`, writes a two-DWORD record `(object pointer, param_4)` at `manager array + 8*param_3`, calls `FUN_00C05500(param_3, object)`, and increments a manager count when the prior slot was empty. It has 39 direct code references in this Ghidra database, so this is a shared state-manager routine, not a Blink-specific method by address alone.

### Follow-up: `DisItemPowers` selection navigation

The exact-build descriptor at `0x01373DA0` contains the UTF-16 class name `DisItemPowers` and constructor pointer `FUN_00C63630` at descriptor offset `+0x24`. That constructor installs vtable `0x01183820`. Package metadata independently declares `DisItemPowers extends DishonoredInventoryItem` and fields `m_pCurrentActivePower`, `m_iPowerSlot`, and `m_pPowersItemTweaks`; native field offsets are not provided by UELib.

In the constructor-associated vtable, byte offsets `+0x150` and `+0x154` contain `FUN_00C45040` and `FUN_00C45110`. The first increments `this+0x118`, wraps at the resolved pawn's usable-index count, and calls the pawn selection slot `+0x6E8` with the value read from its usable-index mapping and flag `0`. The second decrements that cursor, wraps below zero, and makes the same virtual selection call. If `FUN_009FAD20(FUN_00BFECC0())` does not resolve to a `DishonoredPlayerPawn`, each method uses a fallback count from the uncast object returned by `FUN_00BFECC0()` and calls that object's slot `+0x6E8` with the cursor value. This establishes next/previous-style selection navigation inside the `DisItemPowers` vtable and its static connection to the pawn selection handler on the pawn-resolved branch.

The two methods do not call `DisItemContext_UsePower`, Blink slot `+0x1AC`, or a pawn-location writer. Their relationship to a physical keyboard/gamepad event is not established by these vtable entries alone. The class's package fields make `this+0x118` a candidate cursor/current slot field, but that offset-to-property mapping remains an inference pending constructor stores or native reflection metadata.

This adds a static selection-to-component-state path, but does not prove that `_iPower` selects Blink: that still depends on runtime contents of the usable-index array. It also does not prove activation. The inspected path contains no direct call to the `DisItemContext_UsePower` method `FUN_00C44D30`, no dispatch to Blink's move-mode slot `+0x1AC`, and no location write. The meaning of the manager's stored pair and callbacks remains unknown.

The method at pawn vtable slot `+0x6EC` is an unindexed code address `0x00B50B80`. Raw disassembly shows it follows an object reached from pawn offset `+0x59C`, checks a class-chain condition, then tail-calls `FUN_00C44F30`. That helper reads an index at object offset `+0x118` and returns the corresponding DWORD from the pawn array at `+0xA40` after resolving/casting the current pawn. This directly confirms that this path dereferences the `+0xA40` mapping; the semantic meaning of the intermediate object's `+0x118` value, and whether the getter represents the currently selected power, remain unknown. `FUN_00B51790` updates a state manager; its complete semantic contract is also unknown. Do not rename either method as an activation routine yet.

### Correction: Store initializer, not PowerWheel

EXP-0020 initially associated `FUN_00BBD3A0` with PowerWheel because the call immediately follows PowerWheel exec registration in `FUN_00A0DBF0`. The descriptor at `0x013543E0` actually points to UTF-16 name `DisGFxMoviePlayerStore` at `0x0115FA96`; its constructor `FUN_00BD7910` installs vtable `0x01163388`. Therefore the initializer is for Store, and adjacency was misleading. EXP-0020 now records this correction. It does not affect the independent PowerWheel descriptor/constructor/vtable proof above.

## Claim classification

**Confirmed by static evidence:** PowerWheel descriptor → constructor → vtable `0x01161C08`; callback slot `+0x1F0` → `FUN_00BCD800`; controller descriptor → constructor → vtable `0x01118738`; `Dis_SelectPower` slot `+0x560` → `FUN_00AB4680`; item ID `24` maps in the PowerWheel handler to code `2` and the Blink-class item-info branch; `_iPower` indexes an array at pawn offsets `+0xA40/+0xA44`, and the resulting value is passed through pawn virtual slots `+0x6E8/+0x6E4` into active-power-related state handling. Follow-up decompilation confirms that the successful non-current selection branch reaches `FUN_00B56060`, validates the active-power object through `FUN_00C4BA70`, and updates a shared manager through `FUN_00B51790`; that routine writes an object/parameter pair and calls manager virtual slots. The `DisItemPowers` descriptor/constructor identifies vtable `0x01183820`; its entries `+0x150/+0x154` resolve to increment/decrement cursor handlers that call pawn selection slot `+0x6E8` with values from the usable-index mapping.

**Strong inference:** pawn `+0x788/+0x78C` corresponds to `m_ActivePowers`; pawn `+0xA40/+0xA44` corresponds to `m_UsableActivePowerIndices`; the PowerWheel branch code `2` denotes Blink for UI refresh. The `+0xA40` array behavior is directly observed in two functions, while its join to the UnrealScript property name still lacks native reflection offsets. The UI meaning of branch code 2 is supported by its Blink class lookup.

**Unknown:** actual serialized/runtime contents of `m_UsableActivePowerIndices`; whether `_iPower == 0` selects Blink; whether Wheel item ID `24`, callback branch code `2`, controller parameter, and active-array index `0` are converted into one another; offset-to-property mapping for `DisItemPowers.this+0x118`; which input event dispatches the `DisItemPowers` cursor handlers; semantics of virtual `+0x6EC`, manager slots `+0x5C8/+0x5EC`, and the state-manager record; the event path from power selection to `DisItemContext_UsePower`; Blink target/trace/collision logic; and the native code that changes player position or consumes `DisTweaks_Blink`.

## Conclusion and next work

The two central dispatch targets are now resolved. `OnSelectionChanged(24)` has a confirmed static path to Blink-specific UI item information, while `Dis_SelectPower(_iPower)` has a confirmed path into a usable-power index mapping and active-power state handling. No proven edge joins those paths, and the position-changing Blink implementation is still unknown.

Next, inspect the distinct PlayerController shortcut `Use` and `Select` targets, trace the usable-index array's population/defaults, and compare Blink's active-power vtable overrides to locate candidate activation and movement methods. Any candidate must be followed through its callers and state/position writes before assigning Blink semantics.
