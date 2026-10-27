---
id: EXP-0033
title: "UsePower context configuration and callback-owner audit"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What package/default ownership surrounds UsePower context creation and callback registration?"
---
# EXP-0033 — UsePower context configuration and callback-owner audit

- Status: the package configuration for the player Use Power context is confirmed from the preserved UELib dump; the native owner of `FUN_00C2F750` and the runtime creation/dispatch path remain unresolved.
- Date: 2026-10-26.
- Executable: `Dishonored RHCP/Binaries/Win32/Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; PE image base `0x00400000`.
- Package: `assets/extracted/dishonored-blink/DishonoredGame.upk`; preserved probe output `.tmp/uelib-probe/EXP-0033-itempowers-tweak-recheck.log`.
- Ghidra database: `dishonored_exact_full`, x86; read-only MCP decompilation/xrefs.
- Method: inspect the saved package decompilation, decompile selected native functions, and compare Ghidra xrefs with literal addresses in the exact on-disk EXE. No game bytes, package bytes, or Ghidra program bytes were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. The saved UELib output shows `DisTweaks_ItemPowers` nesting `pPlayerUsePower` of class `DisTweaks_UsePower` under `pPlayerSpecific`; `m_ContextSlots_Primary[0]` refers to that object and names the context `Use Power`. The same defaults set `DisTweaks_ItemPowers.m_pSpawnedObjectClass` to `DisItemPowers` and `DisTweaks_UsePower.m_pSpawnedObjectClass` to `DisItemContext_UsePower`. This confirms intended package configuration, not an observed runtime instantiation or input event.
2. The EXE descriptor/constructor evidence already recorded in EXP-0031 identifies `DisItemPowers` constructor `FUN_00C63630`, which installs vtable `0x01183820`. Its slot `+0x1A0` resolves to `FUN_00C0BC00`.
3. `FUN_00C0BC00` obtains an object through an interface at `this+0x40`, checks fields at returned-object offsets `+0xEC` and `+0xF0`, calls generic helper `FUN_00C66070` with arguments derived from its inputs, and passes the result to `FUN_00A23D20`. On a successful filter it performs further virtual calls through fields at `+0x248` or `+0x208` and calls `FUN_00BBEC00`. The code is compatible with an object creation/attachment path, but the returned object's class and its relationship to `DisItemContext_UsePower` are not identified. Do not label this method the Use dispatcher.
4. `FUN_00C66070` is a generic wrapper that checks a flag on its receiver and conditionally dispatches the receiver's slot `+0x13C`. The currently recovered evidence does not name that receiver or prove which class the wrapper creates.
5. Ghidra reports one ordinary code caller of `FUN_00C105F0`: `FUN_00C2F750`. Its decompilation shows calls to `FUN_00BFF440`, passes a returned token to `FUN_00C105F0`, calls `FUN_00C2F690`, sets a bit in `this+0x10C`, and continues through state/condition logic. This confirms a callback-token producer path, not the class owner or event semantics.
6. Ghidra has a data reference at `0x01174BB4` to `FUN_00C2F750`; the exact-build file maps that address to `.rdata` raw offset `0x00D735B4`, where the DWORD is present. However, the presumed surrounding table start `0x01174B98` has no inbound Ghidra xrefs and its little-endian address literal does not occur in the on-disk EXE. Therefore the sequence must remain an unidentified function-pointer region; current evidence does not establish it as a vtable or attribute it to `DisItemContext_UsePower`.
7. The on-disk EXE SHA-256 was recomputed and matches the recorded exact-build hash. The PE section map places `0x01174BB4` inside `.rdata` (image base `0x00400000`, `.rdata` start `0x00F94000`). This validates the address-to-file mapping, not the semantic owner of the pointer sequence.
8. At the time of the original EXP-0033 recheck, `search_objects` and `decompile_object` returned generic invocation errors. This tool-status observation is superseded by the 2026-10-26 MCP recheck recorded in EXP-0035: `inspect_package` and `search_objects` now succeed against the configured compressed package, while `decompile_object` explicitly reports that UELib cannot load its compressed object tables. The preserved decompressed UELib output remains the source for property/default values; no cause is inferred for the earlier generic errors.

## Evidence classification

- **Confirmed from preserved package output:** the nested player `Use Power` context configuration and both `m_pSpawnedObjectClass` defaults.
- **Confirmed from exact-build static evidence:** `DisItemPowers` vtable slot `+0x1A0` target; behavior visible in `FUN_00C0BC00`; generic slot wrapper behavior in `FUN_00C66070`; the `FUN_00C2F750` → `FUN_00C105F0` token route; pointer `FUN_00C2F750` at `.rdata` address `0x01174BB4`; exact EXE hash and PE mapping.
- **Supported interpretation only:** `FUN_00C0BC00` participates in an object creation/attachment path; the package defaults make `DisItemContext_UsePower` the configured context spawned from `DisTweaks_UsePower`.
- **Unknown:** the runtime constructor call for `DisItemContext_UsePower`; which native class owns `FUN_00C2F750`; whether the pointer sequence around `0x01174B98` is a vtable; the keyed callback consumer/event; the callback path's relationship to `FUN_00C0CA70`, Use input, or Blink.

## Next analysis

1. Recover the call chain that consumes `DisTweaks_InventoryItem.m_pSpawnedObjectClass` and instantiates the configured `DisItemContext_UsePower`; confirm the resulting object's vptr at the call site.
2. Identify the owner of `FUN_00C2F750` from a constructor or registration record that stores its receiver vptr; do not infer ownership from nearby function pointers alone.
3. Trace the record consumer behind `FUN_00B36CA0` separately from `FUN_00C0CA70`'s `0x30`-stride array.
4. Join either route to the Blink chain only after a concrete receiver or dataflow edge is recovered.

