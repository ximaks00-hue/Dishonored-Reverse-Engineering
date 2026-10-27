---
id: EXP-0022
title: "Controller shortcut state and function-index audit"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do controller shortcut Use/Select handlers write, and how do they relate to power activation?"
---
# EXP-0022 — Controller shortcut state and function-index audit

- Status: shortcut input handlers are confirmed to update controller selection state; direct power activation is not shown. The 488-function index delta is resolved by EXP-0041: it is exactly the external-function count omitted from the internal-function CSV.
- Date: 2026-10-26.
- Binary: `Dishonored RHCP/Binaries/Win32/Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (recomputed in this pass).
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; read-only decompilation and database queries.
- Scope: read-only. No game files or Ghidra program state were changed. `_excluded_coop_project/` was not accessed.

## Purpose

Continue the controller path after resolving `DishonoredPlayerController.Dis_SelectPower` to `FUN_00AB4680` (EXP-0021), and reconcile the 72,437-entry local function index with Ghidra's 72,925 function count.

## Exact-build and index audit

1. Recomputed SHA-256 for the workspace EXE; it matches the build identity already recorded in EXP-0013.
2. Ghidra MCP `list_databases` reports the attached database `dishonored_exact_full`, source `E:\Dishonored Reverse Engineering\Dishonored RHCP\Binaries\Win32\Dishonored.exe`, and `function_count=72925`.
3. `get_database_info` reports the same count but retains a stale `/E:/SteamLibrary/.../Dishonored.exe` source path. This is a metadata inconsistency; `list_databases` and the recomputed workspace file hash identify the current workspace binary. No attempt was made to rebind or save the database.
4. `research/executable/functions.csv` has 72,437 data rows. The adjacent `ExportTriage.java` obtains its iterator using `currentProgram.getFunctionManager().getFunctions(true)`. Ghidra's official API documents `getFunctions(boolean)` as iterating non-external functions, while `getFunctionCount()` includes external functions. The numeric difference is exactly `72,925 - 72,437 = 488`.

**Original-pass assessment (count claim superseded by EXP-0041):** different enumeration scope was a strong explanation for the 488 difference. At that pass, the external count had not yet been queried, so “488 externals” was only a testable hypothesis. EXP-0041 below measures it directly. The API distinction is documented in the [official Ghidra FunctionManager API](https://ghidra.re/ghidra_docs/api/ghidra/program/model/listing/FunctionManager.html). The stale path in `get_database_info` remains a separate metadata inconsistency, contradicted as the effective input path by `list_databases` and the matching binary hash.

### Follow-up — exact function-set reconciliation (EXP-0041)

Read-only headless enumeration measured `getFunctionCount() = 72,925`, `72,437` internal functions, and `488` external functions. Address-set comparison found an exact match between all 72,437 internal entries and `research/executable/functions.csv`; the other 488 addresses are all external. This closes the count discrepancy without implying the executable or internal-function index changed. See [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md).

## PlayerController shortcut targets

The controller vtable identified in EXP-0021 is `0x01118738`. Its entries at the four shortcut slots resolve as follows:

| Input wrapper | Receiver slot | Vtable target | Observed body behavior |
|---|---:|---:|---|
| Keyboard `Use` | `+0x510` | `FUN_00AA0950` | If the shortcut bit is selected and timing/state gates pass, clears the mask and stores the supplied shortcut index in controller state. |
| Keyboard `Select` | `+0x50C` | `FUN_00AA0900` | Under state/timing gates, stores the index, sets selection flags, and sets the selected bit. |
| Gamepad `Use` | `+0x508` | `FUN_00AA0860` | Clears a selected bit; if one selection remains, updates the current index and a state flag. |
| Gamepad `Select` | `+0x504` | `FUN_00AA3090` | Sets a state flag and bit for the supplied index, applies a four-entry mapping/availability gate, and may update the current index. |

The bodies are short state updates. They do not directly call `FUN_00AB4680` (`Dis_SelectPower`) and do not directly reference the Blink component. This does not rule out later per-frame processing of the changed fields.

Controller tick/state handler `FUN_00AB7D30` reads fields around `+0x610`, `+0x648`, `+0x64C`, `+0x650`, and `+0x658`; it calls shortcut UI methods including `FUN_00BC35E0` / `FUN_00BC36C0`, which invoke Scaleform `SetShortcutSelection`. It also calls `FUN_00BBD090` / `FUN_00BBD180`, which translate a shortcut position through controller-owned byte arrays and store the resulting value at `+0x228` and the shortcut index at `+0x238`. These are selection/UI-state operations. The inspected code does not establish that the stored wheel item is used to invoke `Dis_SelectPower`.

The downstream `FUN_00BBD090` mapping reads one byte from the controller array at `+0x208` or `+0x20C`, subject to the 4- or 10-entry mode selected by flags at `+0x218`. The resulting byte is saved at `+0x228`. This confirms a shortcut-index-to-byte mapping in controller state; without identifying the table's runtime values, it does not prove that the byte is PowerWheel item ID 24 or an `_iPower` value.

Xrefs to the four shortcut targets resolve to data references in method tables; they add no direct code-call edge from those methods to `Dis_SelectPower`. The static search cannot rule out indirect dispatch through the state machine or callbacks.

## Blink vtable candidate check

The exact Blink table `0x01168698` was compared with the base active-power table `0x01167F60` using raw DWORD reads from the matching workspace EXE. This is a class-table comparison, not a bulk candidate scan. The Blink table has distinct entries at multiple offsets; the most behaviorally informative inspected entries are:

- `+0x13C → FUN_00BFC5D0`. This update routine decrements timers, compares a stored three-float point at component offsets `+0xB0..+0xB8` with an actor's location at `+0xC4/+0xC8/+0xCC`, and computes normalized distance. Depending on mode, it calls `FUN_00BFC160` or `FUN_00BED480`, then updates manager/effect values. It does not directly store the new point into the actor location fields.
- `FUN_00BFC160`, used by that update path, compares component vectors at `+0x60..+0x68` with the actor's current location, calls `FUN_00BECDF0` on a candidate vector, stores transformed vectors in component fields, and emits/iterates a callback path. The inspected pseudocode does not directly write the actor's location.
- `+0x314 → FUN_00BFBC90`. This routine manages timers and invokes `FUN_00BF9AB0` for an additional timed stage. `FUN_00BF9AB0` reads per-level float records and traverses candidate objects while computing distances relative to player coordinates. The semantic identity of those records and whether this is Blink aiming, a camera effect, or another component phase is not yet established.
- `+0x1B0 → FUN_00BFA270`. Its decompilation transforms component vectors and writes values into an object reached through the player at `+0xA3C`; the surrounding code appears to configure camera/effect transforms. It is not a proven player relocation method.

The vtable records establish these as methods reached through the Blink class table. Their behavior makes `FUN_00BFC5D0` / `FUN_00BFC160` and the `FUN_00BFBC90` / `FUN_00BF9AB0` pair the strongest current Blink target/animation candidates. They may calculate or visualize a destination, but no direct player-location update or `DisTweaks_Blink` property read has been proven.

### Follow-up: per-level record source in `FUN_00BF9AB0`

Read-only Ghidra disassembly/decompilation establishes the branch that supplies `iVar2` before the `0x38`-stride reads, and a caller confirms the same accessor shape in a second method:

- The routine first calls a virtual getter at `param_1[0x15] + 0x10`. If it returns nonzero, that value is used directly as the object base for the subsequent record access.
- If it returns zero, the code checks global `DAT_0146F26C`; if empty it calls `FUN_00BF3030`, then loads that global into ECX and calls `FUN_00497130(0)`.
- `FUN_00BF3030` initializes `DAT_0146F26C` from descriptor `0x01359D48`. The descriptor's UTF-16 class name at `0x0116547A` is `DisTweaks_DarkVision` (package `DishonoredGame`). `FUN_00497130` is a `thiscall` accessor on that class object and returns its default object.
- The routine then reads the selected record at `base + 0x160 + (param_1[0x22]-1)*0x38`, including floats/fields at offsets `+0x160`, `+0x168`, and `+0x174..+0x17C` relative to the record base.
- `FUN_00BFBC90` calls helper `FUN_00AA5700` with `ECX = this + 0x54`. The helper's machine code invokes the virtual method at the embedded object's vtable slot `+0x10`, returns that nonzero result in EAX, or returns the `DisTweaks_DarkVision` default object from the fallback path. Its saved decompiler signature says `void`, but the call site consumes EAX as the object base; the instructions and return behavior establish the value flow. `FUN_00BFBC90` then copies four DWORDs from `base + 0x14C + level*0x38` and 51 DWORDs from `base + 0x1DC` into fields of another object. This demonstrates an object-supplied accessor and a concrete data-copy use, but does not identify the usual returned class or prove the copied values are Blink-specific.

**Interpretation at this pass:** the fallback source for both inspected accessor paths is confirmed to be `DisTweaks_DarkVision`; that fallback alone is not evidence that Blink reads `DisTweaks_Blink`. The ordinary getter target and class-field join were unresolved here. See EXP-0023 for the follow-up that resolves the getter to the component field at `this+0x8C` and strongly maps it to `m_pPowerTweaks`.

UELib's `PowerAttributes_Blink` declaration in the independently repeated package dump contains 15 floats, one 32-bit integer, and three object references (19 four-byte fields, 0x4C bytes under the package's x86 layout). That size does not match the native record stride `0x38` used by these functions. The direct record layout therefore remains unresolved; EXP-0023 strengthens the source-object join but does not erase this size discrepancy.

The previously observed Blink-specific vtable entries `FUN_00C7E200` and `FUN_00C82AA0` were re-decompiled:

- `FUN_00C7E200` returns a boolean after resolving object/class-chain state, iterating records and applying an object-flag/visibility-like predicate. It does not visibly write actor position or consume an obvious Blink distance field.
- `FUN_00C82AA0` forwards arguments through `FUN_004151C0` and `FUN_00C7E6C0`; its role is not established from this wrapper alone.
- Both addresses have 301 data references in the Ghidra database, consistent with shared/inherited vtable entries. That weakens any inference that either is Blink-specific based solely on appearing in the Blink table.
- Another Blink table entry, `0x00414DC0`, was raw-disassembled because it has no indexed function record. It tests whether `[ecx+8] & 0x80000` is nonzero and returns a Boolean. This is a flag predicate, not evidence of teleportation.

These functions are not attributed as Blink teleportation. They remain candidates only for further type/caller analysis; the inspected pseudocode supplies no positive evidence of relocation.

## Evidence classification

**Confirmed:** current workspace EXE hash matches the recorded build; Ghidra enumerates 72,437 internal and 488 external functions (72,925 total), and the internal address set exactly matches `functions.csv` (EXP-0041); the four controller shortcut slots map to the listed functions; the inspected bodies mutate shortcut-selection state; `FUN_00BC35E0` and `FUN_00BC36C0` call Scaleform `SetShortcutSelection`; `FUN_00C44F30` returns an entry from the `+0xA40` pawn array using an index stored at an intermediate object `+0x118`; `FUN_00414DC0` tests an object flag bit.

**Strong inference:** the controller byte table at `+0x208/+0x20C` probably maps shortcut slots to a game/UI item code, but its values and semantic domain were not read.

**Not established at the original EXP-0022 pass (subsequently refined by EXP-0023/0024):** shortcut `Use` directly activates the selected power; any transition from its state machine to `Dis_SelectPower`; the mapping from the stored wheel item to `_iPower`; `FUN_00C7E200` or `FUN_00C82AA0` performing Blink movement; and the ordinary tweak-pointer/dataflow or downstream pawn-location write.

## Next work

1. **Completed by EXP-0041:** reconcile the Ghidra function counts and exact internal address set using a read-only headless export.
2. Trace reads of controller state fields written by `FUN_00AA0860`, `FUN_00AA0900`, `FUN_00AA0950`, and `FUN_00AA3090`; determine whether any consumer calls a power-use path or converts a wheel item to `_iPower`.
3. Follow the Blink vtable update family `FUN_00BFC5D0`, `FUN_00BFC160`, `FUN_00BFBC90`, and `FUN_00BF9AB0` to determine whether it handles targeting/visualization or reaches the actual relocation routine; search specifically for writes to pawn location and reads from the Blink tweak-level data.
