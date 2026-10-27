---
id: EXP-0044
title: "Transversal vtable ownership and inherited Blink calls"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Who owns the 0x011BD0A8 pointer table, and what do its +0x1AC/+0x1B0 targets call?"
---

# EXP-0044 — Transversal vtable ownership and inherited Blink calls

- Date: 2026-10-26.
- Executable: `Dishonored RHCP/Binaries/Win32/Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching BUILD-STEAM-10256413.
- Package: extracted analysis copy `assets/extracted/dishonored-blink/DishonoredGame.upk`; SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`; UE3 801/30, 30,049 exports, compression flags 0.
- Analysis: static function index/decompilation, persisted exact-build callgraph, raw PE pointer scan and x86 disassembly, plus read-only UELib parsing of the extracted package.
- Exclusions: no game launch or modification; `_excluded_coop_project/` not accessed. Static evidence does not prove runtime scheduling or user-input execution.

## Procedure

1. Rechecked the required status, activation graph, build record, EXP-0042, and EXP-0043 before changing notes. Recomputed the EXE and package hashes; both match their records.
2. Queried exact-build callgraph edges around `0x011BD200–0x011BD290` and compared table entries at `0x011BD0A8` with Blink vtable `0x01168698`.
3. Scanned the EXE for the little-endian pointer `0x011BD0A8`; mapped raw offsets through PE sections and decoded the containing instructions.
4. Decompiled the two functions that install `0x011BD0A8`, their wrapper/descriptor-adjacent functions, and the Blink base constructor.
5. Parsed `DisDLC06ActivePowerComponent_Transversal`, `DishonoredActivePowerComponent_Blink`, and the base class from the uncompressed UPK with UELib.
6. Decoded raw x86 for `FUN_00CF34E0` and `FUN_00CF3540` to verify the receiver passed to the inherited Blink methods.

## Observations

- UELib declares `DisDLC06ActivePowerComponent_Transversal extends DishonoredActivePowerComponent_Blink`, `native(DLC06Transversal)`, `config(Power)`. Its defaults set `m_PowerName="Transversal"` and `m_eUISelection=eDisUISelectionType_Transversal`. This is a distinct subclass/configuration; it must not be silently relabeled as the base Blink ability.
- The native descriptor-like record at VA `0x01398D40` contains the UTF-16 class-name pointer `0x011B8AFA` (`DisDLC06ActivePowerComponent_Transversal`) and a function pointer at `+0x14` to `FUN_00D041D0`.
- `FUN_00D041D0` initializes the receiver through `FUN_00414DB0`, then stores primary vptr `0x011BD0A8` at `this+0` and secondary/interface pointer `0x011BD088` at `this+0x54`. Raw code at VA `0x00D041E9` contains the primary-vptr store. A second raw pointer occurrence at VA `0x00CE6EF2` is in `FUN_00CE6EF0`; its wrapper `FUN_00CE9E40` calls that function, and `FUN_00CE6EF0` then calls `FUN_00BF8A10`, which installs the base Blink vptr `0x01168698`. The latter path is not used as the descriptor-to-primary-vptr proof.
- The table at `0x011BD0A8` is therefore associated with the Transversal class by both package inheritance/name metadata and the descriptor-linked vptr installer. Its entries include `FUN_00BE7580` at `+0x174`, `FUN_00CF34E0` at `+0x1AC`, and `FUN_00CF3540` at `+0x1B0`.
- Blink base vtable `0x01168698` has `FUN_00BE7580` at `+0x174`, `FUN_00BFC990` at `+0x1AC`, and `FUN_00BFA270` at `+0x1B0`. Thus Transversal inherits the relevant Blink class shape but overrides the latter two slots.
- Raw `FUN_00CF34E0` instructions save incoming ECX in ESI, call `FUN_00CF3360`, restore ECX from ESI, then tail-jump to `FUN_00BFC990`. The inherited Blink consumer receives the same Transversal object pointer.
- Raw `FUN_00CF3540` saves incoming ECX in ESI, passes its stack float argument to `FUN_00BFA270` while retaining the same ECX receiver, then calls `FUN_00CF3360` and executes additional state/camera/effect logic. Its epilogue is `RET 4`, consistent with one 4-byte stack argument. The inherited Blink updater receives the same Transversal object pointer.
- `FUN_00CF3540` is a vtable method for the Transversal table, while `FUN_00BFA270` is the base Blink `+0x1B0` target. The direct callgraph edge to `FUN_00BFA270` is consequently explained by this subclass wrapper; it does not identify the input/scheduler that invokes the wrapper.
- The indexed callgraph records the Transversal table entries as data refs, and no ordinary direct caller for `FUN_00CF34E0` or `FUN_00CF3540`. Virtual dispatch remains the supported explanation for entry to these methods, but the runtime dispatch site/scheduler is not identified here.

## Interpretation / claims

- **Confirmed:** `0x011BD0A8` is the primary vtable installed by the native descriptor-associated initializer for `DisDLC06ActivePowerComponent_Transversal`.
- **Confirmed from package metadata:** Transversal is a subclass of Blink and has a distinct `Transversal` name/UI selection default.
- **Confirmed:** Transversal vtable slots `+0x1AC/+0x1B0` resolve to `FUN_00CF34E0/FUN_00CF3540`; these wrappers forward the same receiver to Blink base `FUN_00BFC990/FUN_00BFA270` respectively.
- **Confirmed:** the previously observed call from `FUN_00CF3540` to the Blink target updater is a Transversal-subclass route. The subclass and base share receiver storage because the package explicitly declares the inheritance and the raw call setup preserves `this`.
- **Unknown:** which runtime scheduler invokes Transversal slots `+0x1AC/+0x1B0`, whether those routes run for a player-controlled Transversal instance, and whether they are reached from the player Use event or the base Blink activation graph.
- **Conclusion:** this resolves the owner of the formerly unowned pointer region and explains the direct caller for the Blink updater. It narrows the scope of that caller to the Transversal subclass. It does not close E7 for the base Blink user-input path or connect selection IDs to `_iPower`.

## Reproduction and limitations

- Recheck EXE and UPK SHA-256 values against the build/EXP records.
- Inspect `knowledge/database/callgraph.sqlite` for data edges from `0x011BD0A8`, `0x011BD21C`, `0x011BD254`, and `0x011BD258`; metadata identifies the database build and EXE SHA-256.
- Inspect raw PE at VA `0x00D041E9` and `0x00CF34E0–0x00CF34EB`, `0x00CF3540–0x00CF3557`; map VA through PE sections, not by subtracting image base as a raw file offset.
- Parse the extracted UPK with UELib. Compressed-package `decompile_object` cannot provide these class declarations; the uncompressed copy is required.
- UELib declaration and Ghidra pseudocode are analysis renderings. The descriptor/vptr, inheritance, and receiver-preservation evidence support the claims above; names such as “tick” or “activation scheduler” remain unassigned.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0024, EXP-0028, EXP-0030, EXP-0042, EXP-0043.
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
