---
id: EXP-0014
title: "Native owner attribution for Blink-name lookup"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Which native owners can be attributed for Blink-adjacent tables, and what remains unresolved for movement?"
---
# EXP-0014 — Native owner attribution for Blink-name lookup

- Status: owner attribution supported; Blink movement path remains unknown.
- Date: 2026-10-26.
- Binary: workspace `Dishonored RHCP/Binaries/Win32/Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`; image base `0x00400000`; x86 little-endian; 72,925 functions.
- Scope: read-only Ghidra queries. No game files or Ghidra program bytes/types were changed. The excluded co-op directory was not accessed.

## Question

Who owns `FUN_00956660`, which reads native name keys `BlinkBlender` and `Blink`, and what can be established about the lookup results?

## Source identity caveat

A fresh PowerShell SHA-256 of the workspace EXE matched the build record. Ghidra's `get_database_info` still reports the stale source path `/E:/SteamLibrary/steamapps/common/Dishonored RHCP/Binaries/Win32/Dishonored.exe`, while the earlier open/list database metadata and a byte sample identified the workspace image. Treat the stale path as unresolved metadata. Do not use it to claim that the native project was persistently re-bound.

## Read-only procedure

Queried the existing Ghidra database for:

- xrefs to `FUN_00956660`, `FUN_00592BE0`, candidate table slots, and name globals;
- raw bytes around candidate table `0x010A6694`;
- decompilation and call graphs for the candidate method, constructor, type-name getter, and lookup helper;
- independent SHA-256 of the workspace executable.

Virtual addresses below are Ghidra VAs. RVAs are derived using the confirmed image base `0x00400000`.

## Findings

### 1. The candidate data is a method-pointer table, and its owner is strongly identified as ArkCpntType_Lookat

- `FUN_00955D60` has two direct code callers, `FUN_009EB6B0` and `FUN_00B4B7D0`. The former allocates `0x27C` bytes and calls `FUN_00955D60`; the latter does the same before calling it. This is constructor/allocation-like use.
- In `FUN_00955D60`, the decompiler shows `*param_1 = &PTR_FUN_010A6694`. This is direct evidence that the constructed object's first word is set to the table beginning at `0x010A6694`.
- Raw little-endian DWORDs from `0x010A6694` form a run of pointers into executable code. The relevant slots are:

| Table VA | RVA | Pointer target VA | RVA | Decompiler name |
|---:|---:|---:|---:|---|
| `0x010A6694` | `0x00CA6694` | `0x00956540` | `0x00556540` | `FUN_00956540` |
| `0x010A6698` | `0x00CA6698` | `0x009561E0` | `0x005561E0` | `FUN_009561E0` |
| `0x010A669C` | `0x00CA669C` | `0x009561F0` | `0x005561F0` | `FUN_009561F0` |
| `0x010A66A0` | `0x00CA66A0` | `0x00956270` | `0x00556270` | `FUN_00956270` |
| `0x010A66A4` | `0x00CA66A4` | `0x00955760` | `0x00555760` | `FUN_00955760` |
| `0x010A66A8` | `0x00CA66A8` | `0x00932E20` | `0x00532E20` | `FUN_00932E20` |
| `0x010A66AC` | `0x00CA66AC` | `0x0094D360` | `0x0054D360` | `FUN_0094D360` |
| `0x010A66B0` | `0x00CA66B0` | `0x00956660` | `0x00556660` | `FUN_00956660` |
| `0x010A66B4` | `0x00CA66B4` | `0x00956A00` | `0x00556A00` | `FUN_00956A00` |
| `0x010A66B8` | `0x00CA66B8` | `0x00952620` | `0x00552620` | `FUN_00952620` |

- `FUN_00956270`, at table byte offset `+0x0C` (slot 3), calls `FUN_00956200`. That helper initializes and returns the two-part name `ArkCpntType_Lookat`. Ghidra has a data xref from `FUN_00956200` to the UTF-16 string at `0x010A66BC`. Thus a virtual-style method reached from this same table returns the type name `ArkCpntType_Lookat`.
- Together, the constructor's vptr assignment and the same table's type-name method are independent ownership indicators. **Supported attribution:** `FUN_00956660` is a method in the `ArkCpntType_Lookat` method table. The source does not establish that this native type is a UE3 reflected class with the identical spelling.
- The table entry for `FUN_00956660` is at slot 7, byte offset `+0x1C` from `0x010A6694`. Calling it a vtable is supported by the constructor vptr store, contiguous executable pointers, and the type-name method; it is no longer based on the single pointer alone.

### 2. What FUN_00956660 does with the Blink keys

- `FUN_00956660` has no direct call xrefs in the analyzed database. Its single reference is a data pointer at `0x010A66B0`, the slot above. This is consistent with indirect dispatch.
- The function reads global key pairs at `0x01458BD0/0x01458BD4` and `0x01458BD8/0x01458BDC`, calling `FUN_00592BE0` for each, then stores the returned DWORDs at `this+0x44` and `this+0x48`. At both call sites (`0x00956899` and `0x009568B3`), Ghidra's disassembly shows ECX set to EDI, where EDI was loaded from `*( *(this+0x18) + 0x3DC )`; the two key DWORDs are pushed as explicit arguments. Thus the lookup array base comes from the object referenced by this routine's `this+0x18` field, at offset `+0x3DC`. The runtime type of that container is not established.
- Earlier static-name stubs at `0x00F837E2` and `0x00F83802` refer to strings `BlinkBlender` (`0x010A5830`) and `Blink` (`0x010A5840`) and initialize distinct globals through helper `FUN_00454FE0`. Ghidra xrefs confirm the stubs' references to the strings and the corresponding reads from the globals in `FUN_00956660`.
- If both lookup results are nonzero, `FUN_00956660` dereferences them. It checks a count-like field at result1+0xD0, accesses fields around result2+0xCC through +0xDC, writes a global pointer-like value into a nested field, zeros another field, and clears bits 0 and 3 in a flags word. This establishes that the results are pointer-like records/objects used by the method; their concrete types and semantic roles remain unknown.
- The method also performs many other array scans, lookups, and object-field initializations. The Blink-key logic is one part of a larger routine, not sufficient evidence that the routine implements Blink movement.

### 3. Construction and first observed invocation

- `FUN_00955D60` is called from two allocation paths, `FUN_009EB6B0` and `FUN_00B4B7D0`. Both allocate `0x27C` bytes and call the constructor. `FUN_00B4B7D0` preserves its incoming ECX as the host pointer, constructs the child object, then calls `FUN_009340D0(host, child)`.
- `FUN_009340D0` writes `child+4 = *(host+0x48)` and appends the child pointer to the host array at `host+0x54` using an index returned by `FUN_00B021E0(1)`. This establishes a parent/collection relationship for the constructed object; the host class is not identified.
- In `FUN_00B52270`, ECX is loaded from `ESI+0x3E4` before the call to `FUN_00B4B7D0`, and the returned child is stored at `ESI+0xD70`. The caller then invokes `FUN_0094D370(child, *(EDI+0x1A8))`; that helper stores the value at `child+0x14`. The caller sets DWORD `[child+8]` to 1 and invokes `[child.vptr+0x1C]`, which resolves to `FUN_00956660` for this constructor-installed table.
- This is a concrete initialization path for an `ArkCpntType_Lookat` object: created with a host context, attached to a host collection, assigned an additional pointer/value, enabled, then initialized through `FUN_00956660`. The enclosing object's class and gameplay role are not established. No player-position update or Blink ability activation was found in this call path.
- Ghidra reports 11 incoming data references to `FUN_00B52270` and no direct code-call references. Sampled bytes around these references show runs of code pointers, consistent with indirect/virtual dispatch, but the table boundaries and owning native classes have not been resolved. This is why the single observed call path cannot yet identify the host type.
- `FUN_009EB6B0` is also installed as a factory pointer by `FUN_009FF0E0`, which stores it in a two-field keyed registration record and appends that record to a dynamic array. The registry's subsystem owner remains unknown.

### 4. Native factory registry

- `FUN_009FF0E0` writes a two-DWORD descriptor: the incoming key value at descriptor offset `0`, and factory pointer `FUN_009EB6B0` at offset `4`. It inserts the descriptor pointer into the global pointer array at `DAT_0145EBD0`; `DAT_0145EBD4` is the live element count and `DAT_0145EBD8` the capacity used by registration code.
- Sibling functions such as `FUN_009FF060` and `FUN_009FF160` populate the same array with different factory pointers (`FUN_009EB640`, `FUN_009EB720`, etc.). This is a family of keyed factory registrations, not an exec-script binding table.
- `FUN_00934100(host, key)` walks the registry, compares descriptor DWORD 0 with `key`, calls descriptor DWORD 1 to create the object, sets `child+4 = *(host+0x48)`, and appends the result to the host's object list at `host+0x54`. This directly establishes a key-to-native-factory dispatch path.
- The selected factory `FUN_009EB6B0` allocates `0x27C` bytes and calls `FUN_00955D60`, whose constructor installs the `ArkCpntType_Lookat` method table. Therefore this registry entry constructs an `ArkCpntType_Lookat` instance.
- `FUN_00934220` receives a stream-like object as its stack argument and preserves its incoming `ECX` separately. It calls `FUN_004015B0` on the stack argument to transfer a count and then each 32-bit key; for each key it calls `FUN_00934100` with the preserved incoming `ECX` as host and the key as the explicit argument. It then invokes the created object's vtable slot `+0x14`, passing the stream-like object. Thus this path concretely connects keys transferred by the stream helper to registry lookup and child construction. Whether `FUN_004015B0` is reading or writing in the current mode, and the exact on-disk representation, are not established here.
- The registration thunk begins at `0x00F8D960`: it pushes `0`, pushes immediate key `0x67`, loads `ECX = 0x0145EBE4`, calls `FUN_009FF0E0` at `0x009FF0E0`, then returns. The corresponding call instruction is at `0x00F8D969`. Thus the key for the factory that constructs `ArkCpntType_Lookat` is **confirmed as `0x67` (decimal 103)**; the extra zero argument's meaning is not established. The descriptor address is passed as `this` and then populated by the registrar.
- Ghidra xrefs show this thunk is called only through the registrar call site; no other incoming code xref was resolved. This does not undo the immediate key evidence in the thunk.

#### Sibling factory registration census (read-only)

The same thunk/registrar pattern was inspected across 21 siblings. Keys, registrar entries, factory targets, allocation sizes, and constructor targets below were read from the static thunk immediates and decompiled factory bodies. Allocation size and constructor mapping are confirmed for this image; native type strings are included only where the constructor's method table and name getter were resolved. Keys are numeric registry values, not identified package class indices.

| Key | Registrar VA | Factory VA | Allocation | Constructor VA | Native type name |
|---:|---:|---:|---:|---:|---|
| 101 | `0x009FF060` | `0x009EB640` | `0x274` | `0x00945EC0` | `ArkCpntType_Locomotion` |
| 103 | `0x009FF0E0` | `0x009EB6B0` | `0x27C` | `0x00955D60` | `ArkCpntType_Lookat` |
| 105 | `0x009FF160` | `0x009EB720` | `0x2C` | `0x00935FC0` | `ArkCpntType_Avoidance` |
| 102 | `0x009FF1E0` | `0x009EB790` | `0x78` | `0x00938A90` | `ArkCpntType_FaceTo` |
| 104 | `0x009FF260` | `0x009EB800` | `0x90` | `0x008F9620` | `ArkCpntType_MeshOffset` |
| 210 | `0x009FF2E0` | `0x009EB870` | `0x1C` | `0x00B038C0` | `DisCpntType_AIKnowledge` |
| 208 | `0x009FF360` | `0x009EB8E0` | `0x40` | `0x00B2BAD0` | `DisCpntType_AIMonitorPawnReachability` |
| 211 | `0x009FF3E0` | `0x009EB950` | `0x40` | `0x00B2BC90` | `DisCpntType_AIMonitorReaction` |
| 0 | `0x009FF460` | `0x009EB9C0` | `0xD0` | `0x00C41BA0` | `DisCpntType_AnimPlayer` |
| 200 | `0x009FF4E0` | `0x009EBA30` | `0x5C` | `0x00C3E1F0` | `DisCpntType_HitReactionThrow` |
| 203 | `0x009FF560` | `0x009EBAA0` | `0x50` | `0x00C70B20` | `DisCpntType_Observable` |
| 209 | `0x009FF5E0` | `0x009EBB10` | `0x2C` | `0x00C66B70` | `DisCpntType_Plague` |
| 204 | `0x009FF660` | `0x009EBB80` | `0x58` | `0x00C66C90` | `DisCpntType_Retargeting` |
| 213 | `0x009FF6E0` | `0x009EBBF0` | `0x3C` | `0x00C70F10` | `DisCpntType_TuneCombat` |
| 212 | `0x009FF760` | `0x009EBC60` | `0x2C` | `0x00C670A0` | `DisCpntType_TuneProtection` |
| 205 | `0x009FF7E0` | `0x009EBCD0` | `0x1B0` | `0x00C71810` | `DisCpntType_VisionNPC` |
| 206 | `0x009FF860` | `0x009EBD40` | `400` (decimal) | `0x00C71A20` | `DisCpntType_VisionWatchtower` |
| 207 | `0x009FF8E0` | `0x009EBDB0` | `400` (decimal) | `0x00C71920` | `DisCpntType_VisionRiverKrust` |
| 214 | `0x009FF960` | `0x009EBE20` | `0x14` | `0x00C66420` | `DisCpntType_MonitorNPCReaction` |
| 202 | `0x009FF9E0` | `0x009EBE90` | `0x30` | `0x00C83380` | `DisCpntType_RBDamages` |
| 201 | `0x009FFA60` | `0x009EBF00` | `0x48` | `0x00C74D70` | `DisCpntType_LODManager` |

The seven native names filled in during the follow-up were recovered from constructor-installed method tables: the constructor stores the table address, and slot `+0x0C` reaches a helper that initializes the UTF-16 native type name. This resolves all **21/21** inspected key→factory→constructor→native-name chains. The thunk arguments encode numeric keys passed to the shared registrar; the extra zero on key `0x67` remains unexplained. Key order is not table order. This census still does not connect any entry to Blink or prove the stream's direction.

Reproduction for the seven newly named rows: key `101`, constructor `FUN_00945EC0`, table `0x010A55A0`, name helper `FUN_0093DD50`; key `211`, `FUN_00B2BC90`, table `0x0113A35C`, helper `FUN_00B2BD10`; key `200`, `FUN_00C3E1F0`, table `0x01184F48`, helper `FUN_00C3E270`; key `203`, `FUN_00C70B20`, table `0x0118BAE8`, helper `FUN_00C70BB0`; key `205`, `FUN_00C71810`, table `0x0118BC48`, helper `FUN_00C71880`; key `206`, `FUN_00C71A20`, table `0x0118BD68`, helper `FUN_00C71A80`; key `207`, `FUN_00C71920`, table `0x0118BCD8`, helper `FUN_00C71990`. Each helper passes the exact wide string shown in the table to `FUN_00454FC0`.

### 5. Package-name cross-check

Case-insensitive `ue_explorer.search_objects` queries for `ArkCpntType_Lookat` returned zero matches in `DishonoredGame.upk`, `Core.upk`, `Engine.upk`, `AkAudio.upk`, and `GFxUI.upk`. This supports treating the name as an executable-side native identifier rather than an export in these five checked packages. It does not establish absence from the other CookedPCConsole packages or other install packages.

### 6. Lookup helper layout

`FUN_00592BE0` accepts a base pointer and two 32-bit key values. Its decompilation iterates a count at `base+0x1E0`, reads records from `base+0x1DC` with stride `0x0C`, compares record DWORDs at offsets `0` and `4` to the two keys, and returns the DWORD at offset `8` on a match; otherwise it returns zero.

This confirms a three-DWORD lookup record (12 bytes) and the lookup semantics in this call path. It does **not** prove that the pair is an Unreal `FName`, nor establish the semantic type of the third DWORD.

### 7. Blink cheat exec wrappers are separate virtual dispatch paths

- In the executable's 8-byte native-exec registration records, the entry at `0x012E4838` contains name pointer `0x010C8A70` (`UDishonoredCheatManagerexecBlinkShowRangeFull`) and wrapper pointer `0x009F4090`; the next entry at `0x012E4840` contains name pointer `0x010C8AA0` (`UDishonoredCheatManagerexecBlinkShowRange`) and wrapper pointer `0x009F4020`. These pairs were checked with Ghidra's string index and raw read-only bytes. The package object listing independently identifies the corresponding functions as `native exec` members of `DishonoredCheatManager` (`EXP-0009`).
- Decompilation of `FUN_009F4020` parses one value into a local DWORD and invokes the receiver's virtual method at byte offset `+0x510`; `FUN_009F4090` follows the same pattern but invokes offset `+0x514`. The wrapper code does not itself implement targeting, range visualization, or movement.
- The two wrappers therefore identify adjacent virtual-call slots used by cheat-manager exec bindings. They do not provide a direct connection to `ArkCpntType_Lookat`, the Blink power component, or player relocation; the concrete virtual targets remain unresolved in this pass.
- The table is the native-exec name-to-wrapper registration table; its records do not encode the virtual targets called by the wrappers. The receiver vtable address and the concrete functions in slots `+0x510/+0x514` were not recovered.

### 8. Dis_SelectPower wrapper boundary

- The native-exec name table contains `ADishonoredPlayerControllerexecDis_SelectPower` at string address `0x010CC324`; its record begins at `0x012E5240` and stores wrapper pointer `0x009EE630` in the second DWORD. The package object listing independently contains a `Function Dis_SelectPower` export in `DishonoredGame.upk`.
- Ghidra xrefs to `FUN_009EE630` resolve to the wrapper pointer in the exec-name table (`0x012E5244`) and a second data-table reference (`0x012E39D8`); no direct code-call xref was recorded. This is consistent with native exec dispatch through registration tables, but does not identify runtime callers.
- `FUN_009EE630` parses one DWORD from the exec parameter stream and invokes the receiver vtable at byte offset `+0x560` with that value. This locates the native dispatch boundary for the script-visible selection command but does not reveal the concrete virtual target, selected-power state changes, or any Blink-specific call.
- The neighboring Controller entries provide a consistent slot bracket: `Dis_OpenPauseMenu` wrapper `FUN_009EE5F0` calls `+0x55C` with no argument, and `DisToggleSprint` wrapper `FUN_009EE690` parses a boolean and calls `+0x564`. These are adjacent 4-byte slots around `Dis_SelectPower`'s `+0x560`; this supports the Controller vtable interpretation but does not identify the functions stored there.
- The slot number is not a global method identity. A separate exec registration at `0x012E4000` maps `ADishonoredPawnexecJumpOffPawn` to `FUN_009ECBF0`, whose decompilation calls its receiver's `+0x560` slot with no argument. UELib confirms `DishonoredGame.DishonoredPawn.JumpOffPawn` is `native function JumpOffPawn();`. A raw-code search for the little-endian displacement `0x560` also finds 29 occurrences across unrelated functions. Therefore `+0x560` alone cannot identify `Dis_SelectPower`'s concrete target; class-specific vtable evidence or runtime observation is needed.
- The Blink cheat wrappers dispatch at different receiver offsets (`+0x510/+0x514`) and are registered under `UDishonoredCheatManager`; no direct reference connects those entries to `Dis_SelectPower` or the Blink component.
- Direct UELib decompilation of the decompressed package identifies `DishonoredGame.DishonoredPlayerController.Dis_SelectPower` as `native exec function Dis_SelectPower(int _iPower);`; it has no package script body to trace beyond the native boundary. In `Default__DishonoredPlayerPawn`, the emitted default block assigns the Blink component instance to `m_pBlinkPower` and to `m_ActivePowers[0]`, while `m_pPowersComponent` points to a separate `DishonoredPowersComponent` instance. This establishes the serialized player-pawn association and active-power array position, but not that `_iPower == 0` selects Blink or which native method implements that selection.
- The same UELib class output shows base class `DishonoredPawn` declares `m_ActivePowers` as an array of `DishonoredActivePowerComponent`; `DishonoredPlayerPawn` adds `m_UsableActivePowerIndices`, `m_UsablePassivePowerIndices`, `m_iFirstAcquiredActivePower`, and `m_iFirstAcquiredPassivePower`. These are plausible inputs to power-index selection, but no binary field offsets or dataflow from `_iPower` to these arrays has been established.
- The package enum `DisGlobalEnums.eDisUISelectionType` assigns `eDisUISelectionType_Blink = 2`, while the player pawn's serialized active-power array stores Blink at `m_ActivePowers[0]`. The component base declaration exposes `m_eUISelection` with this enum type, and the Blink default sets it to `eDisUISelectionType_Blink` (`EXP-0009`). Thus the enum code (2) and array position (0) are distinct package values; they must not be conflated. Since the `Dis_SelectPower` parameter is declared as plain `int`, whether it accepts the UI enum, an active-array index, or another code remains unresolved.
- UELib emitted diagnostics while reading some default-object component arrays and failed to deserialize some nested `PowerBlink` default instances because of an enum-value parsing issue. The class declaration, native function signature, and emitted property references above were readable; treat broader nested defaults as incomplete.

### 9. Script-export callsite scan for power-menu selection

- The compressed-package `ue_explorer.decompile_object` endpoint correctly reports that it cannot load compressed object tables. To inspect the already decompressed, ignored copy at `assets/extracted/dishonored-blink/DishonoredGame.upk`, a temporary UELib 1.13.3 console under `%TEMP%` loaded it with `FileAccess.Read` and called `InitializePackage()`; no package data was written.
- The scan iterated all 1,097 exported objects whose class is `Function`, decompiled each where possible, and searched output for `Dis_SelectPower`, `Dis_WheelShortcuts_KeyboardSelect`, `Dis_WheelShortcuts_GamepadSelect`, and `OnShowPowerMenu`.
- Four matches were declarations only: the three `native exec` controller functions (`Dis_SelectPower`, keyboard select, gamepad select) and native `OnShowPowerMenu`. No script-function body emitted a textual call to these names in this package scan.
- This is a scoped negative result, not proof that the methods have no callers: native dispatch, bytecode name/reference encoding, omitted or failed UELib decompilation, other packages, and GFx/ActionScript are outside what this text scan establishes. It does show that the package's decompiled function text did not reveal the desired upstream call chain.
- Practical next lead is the DishonoredPlayerController/PowerWheel native and UI boundary. The executable's native exec initializer groups the controller's 47 name/wrapper records at `0x012E51B8` onward, including the three selection entry points; their implementations remain native dispatch wrappers.

### 10. PowerWheel metadata and native selection boundary

- `DisGFxMoviePlayerPowerWheel` is a native(UI) class extending `DisGFxMoviePlayerBase`. It declares `OnSelectionChanged(int _ItemIdx)` as native; its selection state includes `m_CurItemIdx`, `m_GamepadShortcuts`, and `m_KeyboardShortcuts`. Its config defaults serialize distinct auto-assignment orders for gamepad and keyboard.
- In the package enum `DisGlobalEnums.EDisPowerWheelItem`, `DPWI_Blink` has value **24**. In `Default__DisGFxMoviePlayerPowerWheel`, the auto-assignment order places Blink at gamepad order index `1` and keyboard order index `5`. These are order-array positions; the enum value `24` is a separate value.
- Ghidra's native-exec table entry at `0x012E4740` pairs the string `UDisGFxMoviePlayerPowerWheeleexecOnSelectionChanged` (string VA `0x010C85B0`) with wrapper `FUN_009F8290`. The wrapper parses one DWORD from the exec parameter stream and dispatches it to the receiver's virtual slot at byte offset `+0x1F0`.
- This establishes the PowerWheel selection callback boundary and a distinct wheel-item enum value for Blink. It does **not** show that `_ItemIdx` equals `DPWI_Blink`, that the callback invokes `Dis_SelectPower`, or that either integer is the `Dis_SelectPower._iPower` encoding. No direct xref or recovered target connects `FUN_009F8290` to the player-controller wrapper or to the Blink component.

### 11. PlayerController wheel-state fields

- UELib's read-only decompilation of `DishonoredPlayerController` declares transient fields `m_WheelPreviousSelection` and `m_WheelCurrentSelection` as `DisGlobalEnums.eDisUISelectionType`; it separately declares `m_CurWheelShortcutIdx` and `m_RelativeShortcutOffset` as integers. `Dis_SelectPower` remains declared with an untyped `int _iPower` parameter.
- This supplies a concrete controller-side wheel state using the UI-selection enum and makes the earlier Blink enum value `2` a plausible selection-code hypothesis. It does not establish that `Dis_SelectPower` accepts that enum, that `m_WheelCurrentSelection` is written by this method, or how wheel-item enum `24` is converted to UI enum `2` or active index `0`.
- UELib logged a `Components` property-size diagnostic while decompiling the controller export; the declaration-level fields and function signatures above were emitted, but nested component/default serialization remains subject to the parser limitation recorded under EXP-0009.

### 12. Native-name search boundary

- Ghidra's string-index search returned no hits for `PowerBlink`, `DishonoredActivePowerComponent_Blink`, `m_pBlinkPower`, `m_ActivePowers`, `m_fBlinkDistanceMax`, `BlinkWarmup`, `BlinkMove`, or `BlinkCooldown` in the analyzed EXE.
- This is a bounded negative string-search result only. It does not show that the native implementation is absent; names may be stripped, encoded, represented only in package metadata, or absent from compiled native code. The positive `Blink` and `BlinkBlender` name-key strings already documented in section 2 are distinct evidence and remain valid.
- The next native search must therefore follow structural edges (registration keys, constructor-installed tables, virtual calls, and object-field accesses) rather than expect package property/state names to appear in the EXE string index.

### 13. UELib property-object metadata and offset limitation

- A read-only reflection pass over the decompressed package's actual `UProperty` exports confirms `DishonoredPlayerPawn.m_pBlinkPower` is a `ComponentProperty` referencing `DishonoredActivePowerComponent_Blink`; `DishonoredPawn.m_ActivePowers` is an `ArrayProperty` with component semantics; and `DishonoredPlayerController.m_WheelCurrentSelection` is a `ByteProperty` whose enum reference is `eDisUISelectionType`.
- These exports expose their name, owner, property class, flags, and referenced object/enum, but the installed UELib 1.13.3 object model supplies no native memory offset for these properties (`ElementSize` is zero in the parsed exports, and no offset member is exposed). This pass therefore cannot map a reflected property name to an EXE `this+offset` access through UELib alone.
- This is an important join limitation: package-side types are confirmed, but Ghidra field accesses remain unnamed until a separate class-layout/offset source or a native constructor/registration mapping provides offsets.

### 14. Recheck of executable bindings and read-only vtable search

- UELib 1.13.3 was run directly against the ignored, decompressed copy `assets/extracted/dishonored-blink/DishonoredGame.upk` (SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`). The MCP `ue_explorer` search for the original compressed package works, but its configured root points to `Dishonored RHCP`; it rejects the decompressed path outside that root. No configuration or game files were changed.
- Direct `UFunction.Decompile()` output identifies `DishonoredPlayerController.Dis_SelectPower` as `native exec function Dis_SelectPower(int _iPower);`, `DishonoredPlayerController.OnShowPowerMenu` as native, and `DisGFxMoviePlayerPowerWheel.OnSelectionChanged(int _ItemIdx)` as native. These outputs contain declarations only, not script bodies/bytecode statements.
- Ghidra's byte search for little-endian `0x560` across the analyzed image returned 29 occurrences in unrelated regions; it does not identify the Controller class's concrete slot target. A search in `.data` for the little-endian VA of the separate `FUN_00956660` method table found no Controller vtable identification. The wrapper at `FUN_009EE630` remains an adapter that dispatches its parsed DWORD through receiver offset `+0x560`.
- The direct UELib run exposed parser diagnostics while loading some unrelated/default nested package objects, including an enum-value parse failure. The three queried `UFunction` declarations were successfully emitted. Treat the absence of decompiled bodies as confirmed for these native declarations, not as a claim that every script export in every package parsed cleanly.
- This pass did not resolve the concrete target of `Dis_SelectPower`, `OnSelectionChanged`, or the Blink native methods. The next discriminating route is to identify the relevant class vtable through native registration/constructor evidence and the target initializer, rather than infer a function from a raw slot displacement.

### 15. Teleport and power lifecycle callback boundaries

- A raw read of the 8-byte native-exec registration record at `0x012E5310` contains name pointer `0x010CC71C` (`ADishonoredPlayerControllerexecOnTeleport_Native`) and wrapper pointer `0x009EDC30`. Decompiling `FUN_009EDC30` shows it parses one parameter and dispatches to receiver slot `+0x4F8`.
- Correction to the prior interim note: `FUN_009F4100` is not the `OnTeleport_Native` wrapper. Its table references include the player-controller `Dis_WheelShortcuts_MouseNext` record at `0x012E52D0`; it dispatches slot `+0x518`. The prior association of `FUN_009F4100` with teleport is superseded by the raw name/wrapper record and wrapper decompilation.
- The base `DishonoredPawn.OnTeleport_Native` is a separate function. Its exec record at `0x012E4050` contains wrapper pointer `0x009EC880`; decompilation parses one parameter, dispatches receiver slot `+0x538`, and stores the virtual return value for the script-call return. The slot and return shape differ from the controller callback.
- Direct UELib decompilation of the decompressed package identifies `DishonoredPlayerController.OnTeleport_Native(SeqAct_Teleport _pAction)` as a native function. `DishonoredPawn` also declares a distinct `OnTeleport_Native(SeqAct_Teleport _pAction)` that returns `bool`; do not conflate their class-specific wrapper dispatch.
- The same package declares `DishonoredPlayerPawn.OnAddPower(DisSeqAct_AddPower _pAction)` and `OnCancelPlayerActivePower(DisSeqAct_CancelPlayerActivePower _pAction)` as native. Their records map wrappers `FUN_009EF0C0` and `FUN_009EF8A0`, which dispatch to receiver offsets `+0x788` and `+0x7E4`, respectively. The already recorded `Dis_SelectPower` wrapper dispatches to controller offset `+0x560`.
- This yields confirmed, named native callback boundaries for power addition/cancellation, power selection, and two class-specific teleport notifications. It does not prove their call order, direct calls between them, or that Blink triggers `SeqAct_Teleport`; each implementation target remains virtual and unresolved. Treat the shared word “teleport” as a candidate join, not proof that this is Blink's movement implementation.
- The broad native-registration initializer `FUN_00A0DBF0` registers the controller's exec-name table at `0x012E51B8` under `DishonoredPlayerController`, then calls many small name-initialization functions. It is not itself a controller vtable constructor. No PDB/MAP/symbol file is present in the inspected workspace binary directory, so this static pass still lacks an external class-layout symbol source.

### 16. PlayerController wheel shortcut and teleport registration cluster

- A raw read of the contiguous 8-byte records from `0x012E52D0` through `0x012E5310`, combined with the string-index names and decompilation of each wrapper, yields this exact name-to-wrapper-to-slot map:

| Controller native exec | Record VA | Wrapper VA | Wrapper dispatch |
| --- | ---: | ---: | --- |
| `Dis_WheelShortcuts_MouseNext` | `0x012E52D0` | `0x009F4100` | `+0x518`, no parsed argument |
| `Dis_WheelShortcuts_MousePrevious` | `0x012E52D8` | `0x009EDEF0` | `+0x514`, no parsed argument |
| `Dis_WheelShortcuts_KeyboardUse` | `0x012E52E0` | `0x009EDE90` | `+0x510`, parsed DWORD |
| `Dis_WheelShortcuts_KeyboardSelect` | `0x012E52E8` | `0x009EDE30` | `+0x50C`, parsed DWORD |
| `Dis_WheelShortcuts_GamepadUse` | `0x012E52F0` | `0x009EDDD0` | `+0x508`, parsed DWORD |
| `Dis_WheelShortcuts_GamepadSelect` | `0x012E52F8` | `0x009EDD70` | `+0x504`, parsed DWORD |
| `Dis_Wheel_Close` | `0x012E5300` | `0x009EDD00` | `+0x500`, parsed and normalized bool |
| `Dis_Wheel_Open` | `0x012E5308` | `0x009EDC90` | `+0x4FC`, parsed and normalized bool |
| `OnTeleport_Native` | `0x012E5310` | `0x009EDC30` | `+0x4F8`, parsed object argument |

- UELib signatures confirm the four Keyboard/Gamepad `Use` and `Select` functions each take `int _ShortcutIdx`; the two mouse next/previous functions have no parameters; wheel open/close each take `bool _bWithGamepad`; controller `OnTeleport_Native` takes `SeqAct_Teleport _pAction`. The wrapper's DWORD decode is therefore consistent with these declared argument types.
- `DisGFxMoviePlayerPowerWheel` declares `m_GamepadShortcuts[DisWheelShortcut]` and `m_KeyboardShortcuts[10]`. Its emitted default block contains `m_AutoAssign_GamepadItemOrder[1]=DPWI_Blink` and `m_AutoAssign_KeyboardItemOrder[5]=DPWI_Blink`, but no explicit assignments to the current shortcut arrays. Therefore the observed auto-assignment order positions cannot be equated with the runtime shortcut-array contents or `_ShortcutIdx` mapping from this default block alone.
- This cluster proves that the PlayerController exposes distinct native `Use` and `Select` paths for keyboard/gamepad shortcuts, in addition to `Dis_SelectPower(int _iPower)`. It gives a stronger set of named entry points to trace than the standalone selection wrapper. It does **not** prove that either `...Select` method calls `Dis_SelectPower`, that `_ShortcutIdx` is a power-wheel enum/index, or that the teleport callback is invoked by Blink.
- The wrappers dispatch through adjacent slots `+0x4F8`–`+0x518`, but the table entries point to exec adapters, not the concrete functions stored in the receiver's C++ vtable. The concrete targets remain unresolved.

### 17. Direct xref audit for selection adapters

- Ghidra `get_xrefs_to` for `FUN_009EDD70` (GamepadSelect) returned only DATA references at `0x012E52FC` and `0x012E3A34`; `FUN_009EDE30` (KeyboardSelect) returned only DATA references at `0x012E52EC` and `0x012E3A2C`.
- `FUN_009EE630` (`Dis_SelectPower`) returned only DATA references at `0x012E5244` and `0x012E39D8`. `FUN_009F8290` (PowerWheel `OnSelectionChanged`) returned five DATA references at `0x012E4744`, `0x012E41FC`, `0x012E3218`, `0x012E32FC`, and `0x012E347C`.
- No direct code-call reference to these wrapper addresses was returned in this Ghidra database. The positive references identify registration/dispatch data, not callsites. This is expected to miss indirect Unreal `ProcessEvent`/native dispatch and must not be interpreted as proof that no callers exist.
- The direct-xref pass therefore does not connect controller shortcut selection to `Dis_SelectPower` or PowerWheel selection. Recovering that path requires concrete vtable slot targets, runtime observation, or another serialized/UI dispatch source.

### 18. PE CodeView record and exact PDB lookup

- `llvm-readobj.exe --coff-debug-directory Dishonored RHCP/Binaries/Win32/Dishonored.exe` found one PE CodeView entry: PDB GUID `{21384D5C-A1AB-44BF-944E-54D2C991BD45}`, age `1`, and embedded path `c:\Users\aarbona\Perforce\antonio.arbona_GMSORL-PC-0004_Dishonored_Campfire_8790\Binaries\Win32\DishonoredGame-Shipping.pdb`. The debug-directory timestamp is `2022-02-17 20:20:23`.
- A targeted local search for `DishonoredGame-Shipping.pdb` under the workspace, Steam library, Codex data, common Dbg symbol-cache directory, and local temp directory returned no file. A HEAD request to Microsoft's symbol-store path for this exact PDB name/GUID/age returned HTTP 404. Web searches for the exact PDB/GUID also returned no result.
- **Interpretation:** the EXE retains a CodeView reference to a build PDB, but that reference is only a path/GUID record; it does not embed type or function symbols. The named PDB appears to be from a developer Perforce workspace. The target vtables remain unresolved because the PDB itself was not found or obtainable from the tested symbol store.
- Reproduction: `llvm-readobj.exe --coff-debug-directory "Dishonored RHCP\\Binaries\\Win32\\Dishonored.exe"`; symbol-server HEAD URL used the exact CodeView key `21384D5CA1AB44BF944E54D2C991BD451`.

### 19. MSVC RTTI class-name census

- A read-only raw-byte scan of the exact EXE for null-terminated MSVC TypeDescriptor name prefixes `.?AV` found 296 unique class-name strings. Some third-party RTTI is present; for example, `.?AVFxRefObject@Face@OC3Ent@@` appears in the binary.
- None of the 296 names contains `Dishonored`, `PlayerController`, `PlayerPawn`, `DisGFxMoviePlayerPowerWheel`, `DishonoredActivePowerComponent`, `Blink`, or `ArkCpntType`. Thus no class-name RTTI TypeDescriptor for the target Dishonored gameplay classes was recovered by this scan.
- This is a scoped negative result over this MSVC RTTI string form. It does not prove that no other type metadata, proprietary RTTI, or symbols exist. Combined with the unavailable private-path PDB from section 18, it means this pass cannot label candidate function-pointer arrays as the target gameplay vtables by class-name metadata alone.

## Confirmed vs inferred vs unknown

**Confirmed by this pass**

- Current workspace EXE SHA-256 equals the recorded build hash.
- `FUN_00955D60` assigns the object vptr/table at `0x010A6694`.
- The table contains `FUN_00956660` at slot 7 / byte offset `0x1C`.
- A method in that table obtains the type name `ArkCpntType_Lookat` through a string-backed two-part name.
- `FUN_00956660` uses the two initialized name pairs, stores lookup results at `this+0x44/+0x48`, and dereferences those results when both are nonzero.
- `FUN_00592BE0` searches 12-byte records using a two-DWORD key and returns the third DWORD.
- `FUN_00B52270` creates an object through `FUN_00B4B7D0`, stores it at `this+0xD70`, sets an internal DWORD, and invokes vtable slot `+0x1C`, resolving to `FUN_00956660` for this constructor-installed table.
- Searches found no `ArkCpntType_Lookat` object-name match in DishonoredGame, Core, Engine, AkAudio, and GFxUI packages; other packages were not exhaustively searched.
- `FUN_009FF0E0` registers factory `FUN_009EB6B0` under key `0x67` in the keyed native factory registry consumed by `FUN_00934100`; this registration constructs an `ArkCpntType_Lookat` object. The key's relationship to Blink remains unknown.
- The 21 inspected sibling registrations resolve to 21 native type names through each factory's constructor-installed method table and its UTF-16 name helper; the full key/factory/constructor/name map is in the registry census above. This is a complete map only for the 21-entry family inspected, not proof that no additional registrations exist elsewhere in the executable.
- The two package-declared Blink cheat exec wrappers dispatch through receiver vtable offsets `+0x510` and `+0x514`; their virtual targets and any relationship to Blink targeting remain unknown.
- The `ADishonoredPlayerControllerexecDis_SelectPower` registration points to `FUN_009EE630`, which dispatches one parsed DWORD to receiver vtable offset `+0x560`; its virtual target and resulting power-selection path remain unknown.
- The decompressed package associates `Default__DishonoredPlayerPawn.PowerBlink` with both `m_pBlinkPower` and `m_ActivePowers[0]`; this does not prove the native `Dis_SelectPower` index mapping.
- The package declares usable-power index arrays and a first-acquired-power index on `DishonoredPlayerPawn`; their relation to `_iPower` is a candidate for testing, not a confirmed mapping.
- The package UI enum assigns Blink value 2 while the serialized active-power array places Blink at index 0; the `int _iPower` argument's encoding remains unknown.
- Targeted Ghidra string searches found no EXE strings for the Blink component class, PowerBlink, its named fields, or its state enumerators; the native implementation must be identified through structural/code-flow evidence rather than these labels.
- The native structure/type and the gameplay meaning of the two Blink-name lookup results remain unassigned.

**Inference**

- The constructor assignment, executable pointer run, and virtual type-name method support interpreting the table as the `ArkCpntType_Lookat` method/vtable table.
- The returned values behave as pointers to mutable records/objects.
- The `ArkCpntType_Lookat` instance appears in a larger native object's initialization path; the enclosing object's type and gameplay purpose are unknown.
- The registry key likely serves as a native type identifier because `FUN_00934220` transfers 32-bit keys through a stream helper and uses each key to select a factory. The function's argument flow establishes the connection; stream direction and exact archive format remain unknown. Key `0x67` itself is directly established for the `ArkCpntType_Lookat` factory registration, but no observed stream value yet proves that this key occurs in a serialized object list.
- Because `BlinkBlender` and `Blink` are resolved within `ArkCpntType_Lookat` initialization, an animation, look-at, or visual-support role is plausible. This is not proved.

**Unknown**

- Whether either lookup result represents `DishonoredActivePowerComponent_Blink`, a blender/effect, or another native object.
- Whether `ArkCpntType_Lookat` directly or indirectly participates in ability selection or player relocation.
- Where the Blink component's native implementation/registration lives and which code consumes `m_pPowerAttributes`, distance, step, or timing values.
- Whether the two-part keys use UE3 `FName` semantics.
- Whether the EXE was obtained byte-for-byte from the Steam depot; build ID association and local hash match do not independently establish depot provenance.

## Package cross-check limitation

Initial `ue_explorer.search_objects` requests using the decompressed absolute path and bare package filename returned a generic invocation error. Retrying with the root-relative cooked path succeeded. Searches returned zero matches in `DishonoredGame.upk`, `Core.upk`, `Engine.upk`, `AkAudio.upk`, and `GFxUI.upk`; these package-scoped zero-hit results do not establish absence from the other packages in the installation.

## Follow-up

1. The sibling key/factory/constructor census is complete for the 21 inspected registrations, and `FUN_00934220`'s argument flow confirms that stream-transferred keys are dispatched through the registry. Next identify callers/modes of this stream routine and determine whether a real serialized object list contains key `0x67`.
2. Identify the data structures behind both Blink keys by following their registration and result consumers; do not infer `FName` layout from two DWORD comparisons.
3. Identify the host type passed into the `ArkCpntType_Lookat` factory and trace the host's list serialization/initialization path.
4. Search the same executable for exact property names and native registration records for `DishonoredActivePowerComponent_Blink` and `DisTweaks_Blink`; correlate only with direct xrefs, class indices, or field-offset evidence.
5. Resolve the receiver vtable targets for PowerWheel `OnSelectionChanged` at `+0x1F0` and `ADishonoredPlayerControllerexecDis_SelectPower` at `+0x560`, then establish whether either path connects the wheel enum (`DPWI_Blink=24`) to a UI selection code (`Blink=2`) or to an active-array position (`Blink at index 0`). The scan of 1,097 exported function decompilations found declarations but no textual script callsite; treat that as limited negative evidence only.
6. Trace the player-power selection path into the Blink component, then distinguish visual targeting from movement/position update.
7. Resolve the receiver vtable targets used by the Blink cheat exec wrappers at `+0x510` and `+0x514`; treat them as cheat-manager paths unless direct evidence links them to the power component.
8. Preserve the Ghidra source-path inconsistency. Do not force-save or close the database while Ghidra reports an active transaction.

## Reproduction addresses

### 8. Controller native-registration neighborhood is not a controller constructor

Read-only decompilation of the 15 calls immediately following the `DishonoredPlayerController` registration setup in `FUN_00A0DBF0` (`FUN_00AC4710`, `FUN_00B8A720`, `FUN_00AC36B0`, `FUN_00AC4740`, `FUN_00AC4770`, `FUN_00AC48D0`, `FUN_00A85750`, `FUN_00A857B0`, `FUN_00A857E0`, `FUN_00AA2980`, `FUN_00AA29B0`, `FUN_00ACECF0`, `FUN_00ACF490`, `FUN_00AC9BE0`, and `FUN_00AC66B0`) shows the same pattern in all 15: test a global pointer, call `FUN_00479370` with a distinct static descriptor if null, call a distinct per-object initializer, store and return the pointer. Examples include `FUN_00AC4710` (`DAT_0145FA94`, descriptor `DAT_01318D58`, initializer `FUN_00ABFD50`) and `FUN_00B8A720` (`DAT_014673A0`, descriptor `DAT_01346470`, initializer `FUN_00B85E10`).

**Confirmed, bounded result:** these sampled neighboring calls are lazy global-object accessors, not direct evidence of a `DishonoredPlayerController` constructor or vtable initializer. Their object types and relationship, if any, to native registration are unknown. This avenue did not resolve the target of `Dis_SelectPower` at controller-relative slot `+0x560`; it must remain open. The complete registration routine was not exhaustively classified, so this finding applies only to the 15 calls listed above.

Reproduction: Ghidra MCP `decompile_function` on the 15 addresses listed above, database `dishonored_exact_full`; image base `0x00400000`. The database metadata still reports a stale source path as described in “Source identity caveat.”

### 9. Reproducibility recheck of compressed-package extraction and Blink defaults

Re-ran the existing local decompressor and UELib dump workflow after noticing that prior diagnostic logs were absent from the workspace. The decompressor is present at `tools/ue-package-decompressor/decompress.exe` (SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`); its source checkout under `.tmp/UEViewer-source` is at upstream commit `a0bfb468d42be831b126632fd8a0ae6b3614f981`. The original installed package was read as input and its SHA-256 was `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`. The decompressor wrote only to ignored `assets/extracted/dishonored-blink/` and reported package `801/30`, 24,432 names, 30,049 exports, 652 imports, output length 17,320,971 bytes.

The re-created decompressed output SHA-256 is `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`, matching EXP-0009. The existing compiled read-only dump utility ran against that file with Eliot.UELib 1.13.3; it reported `CompressionFlags=0`, 30,049 exports, and 652 imports, and repeated the Blink class declarations and both `DisTweaks_Blink.m_Levels` serialized entries. It reconfirmed `m_fBlinkStepDistance=500` in the component default and the two level entries with distances `2000/1400/400`, default step distance `300`, and interval `0.01`, as recorded in EXP-0009. The complete fresh output is local-only at `.tmp/ue-readonly-dump/EXP-0009-recheck.log`.

One initial `dotnet run` rebuild attempt failed because the host package under the global NuGet cache was inaccessible; running the already-built utility DLL directly succeeded. This environment issue did not affect the successful parse. The old logs were absent, but the decompressor, compiled dumper, package source, and recorded source checkout were present; this successful recheck replaces reliance on the missing logs. No installed game files were changed.

| Symbol | VA | Derived RVA |
|---|---:|---:|
| `FUN_00955D60` constructor | `0x00955D60` | `0x00555D60` |
| `ArkCpntType_Lookat` table | `0x010A6694` | `0x00CA6694` |
| `FUN_00956270` name getter slot | `0x00956270` | `0x00556270` |
| `FUN_00956660` slot 7 | `0x00956660` | `0x00556660` |
| `FUN_00592BE0` lookup helper | `0x00592BE0` | `0x00192BE0` |
| `FUN_00454FE0` name-key initializer | `0x00454FE0` | `0x00054FE0` |
| `BlinkBlender` | `0x010A5830` | `0x00CA5830` |
| `Blink` | `0x010A5840` | `0x00CA5840` |
| `ArkCpntType_Lookat` UTF-16 string | `0x010A66BC` | `0x00CA66BC` |
| `FUN_009EB6B0` factory | `0x009EB6B0` | `0x005EB6B0` |
| `FUN_00B4B7D0` object factory | `0x00B4B7D0` | `0x0074B7D0` |
| `FUN_00B52270` observed caller of object factory | `0x00B52270` | `0x00752270` |
| `FUN_009FF0E0` factory-record setup | `0x009FF0E0` | `0x005FF0E0` |
| `FUN_00934100` keyed factory lookup/instantiate | `0x00934100` | `0x00534100` |
| `FUN_00934220` archive list dispatcher | `0x00934220` | `0x00534220` |
| Registration thunk for key `0x67` | `0x00F8D960` | `0x00B8D960` |
| Registration thunk call instruction | `0x00F8D969` | `0x00B8D969` |
| `execBlinkShowRange` native wrapper | `0x009F4020` | `0x005F4020` |
| `execBlinkShowRangeFull` native wrapper | `0x009F4090` | `0x005F4090` |
| `ADishonoredPlayerControllerexecDis_SelectPower` wrapper | `0x009EE630` | `0x005EE630` |

