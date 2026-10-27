---
id: EXP-0020
title: PowerWheel native registration and lazy initialization triage
experiment_status: superseded
claim_status: superseded
build: "10256413"
question: "Which constructor/global initializes DisGFxMoviePlayerPowerWheel? (Superseded by EXP-0021.)"
---
# EXP-0020 — PowerWheel native registration and lazy initialization triage

- Status: initial interpretation superseded by EXP-0021. The global initialized through `0x013543E0` belongs to `DisGFxMoviePlayerStore`; it is not the PowerWheel instance vtable. The PowerWheel instance table and `+0x1F0` target are established in EXP-0021.
- Date: 2026-10-26.
- Build: Steam app 217980, build 10256413, x86; workspace executable recorded in `EXP-0017`.
- Ghidra database: `dishonored_exact_full`, 72,925 functions. `list_databases` identifies `Dishonored RHCP/Binaries/Win32/Dishonored.exe` as its input. No database edits or saves were made.
- Package: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, compressed package, version 801/30.
- Scope: read-only UE Explorer package metadata and Ghidra xref/decompilation; no game files or Ghidra program data were changed; `_excluded_coop_project/` was not accessed.

## Question

Can the class-specific PowerWheel native registration and its lazy initialization path identify the concrete instance method called by `OnSelectionChanged` at receiver offset `+0x1F0`?

## Procedure and observations

1. Called `ue_explorer.inspect_package` on the configured workspace package. It returned the path under `Dishonored RHCP`, package version `801/30`, `compressionFlags=2`, 30,049 exports, and 652 imports.
2. `ue_explorer.search_objects` found the `Class DisGFxMoviePlayerPowerWheel` export and its `Default__DisGFxMoviePlayerPowerWheel` export. `decompile_object` for this class and for `DishonoredPlayerController` returned the explicit limitation that UELib cannot load object tables from this compressed package. These calls confirm the configured MCP path and current parser boundary; they provide no new class method body.
3. Re-read the Ghidra native-registration routine `FUN_00A0DBF0`. It registers class name `DisGFxMoviePlayerPowerWheel` with exec table pointer `0x012E4728`, then calls `FUN_00BBD3A0`.
4. Ghidra xrefs to `FUN_00BBD3A0` show calls from `FUN_00A0DBF0` and `FUN_00B88240`. Its decompilation lazily initializes global `DAT_0146F004` through `FUN_00479370(&DAT_013543E0)` and then calls `FUN_00BB9F50`.
5. `FUN_00BB9F50` calls `FUN_00426F30`, `FUN_00B8C260`, and `FUN_00424880` using the global at `DAT_0146F004`. The Ghidra decompiler's recovered helper signatures omit some call arguments; this prevents treating the pseudocode as a complete high-level type reconstruction. The inspected path contains no direct assignment to a candidate vtable in its decompiled output, and its helper identities/roles are not yet resolved.
6. The second caller, `FUN_00B88240`, is called by `FUN_00B8B810`. Its body traverses a linked chain beginning at `param_1+0x30` (next pointer at `+0x44`) and checks for pointer equality with `DAT_0146F004`. This is consistent with the global being used as a type/class-chain marker, but the chain structure and object type are not independently identified. `FUN_00B8B810` calls `FUN_00BBF700`, `FUN_00C3DAF0`, then tests the object at `param_1+0x100`; if it passes the membership check it invokes `FUN_00BBD3D0`. This adds a usage context for the global without revealing a vtable slot or proving its class name.
7. As a spot-check of constructor-assignment candidates near this code region, `FUN_00BB85C0` and `FUN_00BFFD50` both install `0x0116BD48`. Its `+0x1F0` slot points to `FUN_004781C0`; decompilation identifies that routine as UObject destruction/cleanup behavior (`FinishDestroy` checks and object-array cleanup), not a one-integer PowerWheel selection handler. The table is rejected for this proposed slot. No evidence found here links its constructor functions to `DisGFxMoviePlayerPowerWheel`.
8. A local read-only join of the 1,176 rows in `.tmp/vtable-assignment-candidates-baseptr.csv` with `research/executable/functions.csv` found only nine candidates whose `+0x1F0` targets have an indexed two-parameter signature; all nine resolve to the same middleware function `AKRESULT SetMonitoring(long, bool)` at `0x0057D890`. This rules out those nine proposals, not the other candidates. Ghidra's inferred/indexed signatures are incomplete for many stripped functions, so signature count is only a coarse triage filter and not proof that the remaining candidates have incompatible signatures.

## Evidence classification

**Confirmed:** the package is compressed and searchable for export names through `ue_explorer`; the PowerWheel class/default exports are present; the exact-build native registration routine associates class name `DisGFxMoviePlayerPowerWheel` with exec table `0x012E4728` and calls `FUN_00BBD3A0`; that function lazily initializes global `DAT_0146F004` and calls `FUN_00BB9F50`; descriptor `0x013543E0` names `DisGFxMoviePlayerStore`; and the tested table `0x0116BD48` is installed by the two listed functions and its `+0x1F0` target is UObject destruction/cleanup code.

**Superseded inference:** the first pass associated `FUN_00BBD3A0` with PowerWheel based only on call adjacency. Descriptor-name evidence disproves that association: this initializer is Store-related. The second caller's linked-chain comparison is still observed, but its precise runtime role is not established here.

**Unknown within this experiment:** the complete runtime role of global `DAT_0146F004`, the chain checked by `FUN_00B88240`, whether the PowerWheel callback reaches `DishonoredPlayerController.Dis_SelectPower`, and how values `24`, `2`, and `0` map into activation or movement. The PowerWheel instance vtable and `+0x1F0` target are no longer unknown; see EXP-0021.

## Correction from follow-up inspection

The descriptor at `0x013543E0` contains a pointer to the UTF-16 string `DisGFxMoviePlayerStore` at `0x0115FA96`. Its constructor pointer is `FUN_00BD7910`, which installs vtable pointer `0x01163388`. Therefore `FUN_00BBD3A0` initializes the Store class object. The call immediately after PowerWheel exec registration in `FUN_00A0DBF0` was only adjacency; it did not initialize PowerWheel. The original observation that the routine initializes `DAT_0146F004` remains valid, but the PowerWheel association is superseded.

The PowerWheel owner and target were subsequently resolved from its own static class descriptor and constructor; see EXP-0021. The candidate table `0x0116BD48` and coarse signature triage remain as recorded above, but they are not needed for that attribution.

## Conclusion

This experiment's first interpretation of the lazy initializer as PowerWheel-related was a false association and is explicitly superseded. It remains useful as a record of the negative triage and the Store-class correction. Use EXP-0021 for the confirmed PowerWheel vtable and callback target.

