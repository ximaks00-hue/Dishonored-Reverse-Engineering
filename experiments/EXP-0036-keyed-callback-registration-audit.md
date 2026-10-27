---
id: EXP-0036
title: "Keyed callback-registration helper audit"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What does FUN_00B36CA0 register, and does any key route join Use/Blink?"
---
# EXP-0036 — Keyed callback-registration helper audit

- Status: `FUN_00B36CA0` is confirmed as a shared keyed insert/update registration helper with distinct key-3 and key-9 callback routes. Neither route identifies a user-Use event or joins to Blink or `FUN_00C0CA70`.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; read-only decompilation, disassembly, and xrefs.
- Scope: inspect `FUN_00B36CA0`, its direct references, and two caller/callback lifecycles already noted in EXP-0031/EXP-0021. No game bytes or Ghidra program data were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. Ghidra reports 107 direct code references to `FUN_00B36CA0` in the current database (call sites, not necessarily 107 unique owner classes). This broad reuse supports treating it as a generic helper rather than assigning it to a single gameplay subsystem.
2. The function scans a manager array rooted at receiver offsets `+0x1650` (data) and `+0x1654` (count), comparing each entry's first DWORD with the key at the supplied record's first DWORD. If a key is already present, it builds a callback-related record from the key and supplied fields and routes through `FUN_00933B60`; otherwise it constructs a record and routes through `FUN_009FAC70` to add it. The exact manager class and full storage schema remain unidentified.
3. `FUN_00C105F0(this, token)` stores the token at `this+0x50`. On a transition from zero to nonzero, it builds a registration tuple with key `3` and callback `FUN_00C128B0`, then calls `FUN_00B36CA0`. On a transition from nonzero to zero, it calls `FUN_00AEDF80` with the same callback/key family to remove the association. Raw disassembly confirms the key value, callback pointer, receiver, and calls at `0x00C10604`–`0x00C10620` and the removal branch at `0x00C1062D`–`0x00C10647`.
4. `FUN_00C128B0` receives a callback payload, compares its `+8` value with `this+0x50`, and, on a match, clears `this+0x50` and unregisters the key-3 callback through `FUN_00AEDF80`. This confirms a token-guarded callback cleanup path, not what event produces the callback.
5. `FUN_00C2F750` is the only ordinary code caller of `FUN_00C105F0` in the current xref result. It obtains a token through `FUN_00BFF440` and changes several state/timing fields around the registration call. A data reference to `FUN_00C2F750` at `0x01174BB4` was recorded in EXP-0033, but no owner class or actual event meaning has been proven. Do not label it a UsePower or Blink callback.
6. Independent key-9 route: `FUN_00C0F9F0`, previously associated with `DisItemPowers` vtable slot `+0x130` in the EXP-0021 follow-up, compares an interface result through `this+0x40`, computes/stores a value at `this+0xE4`, and registers callback `FUN_00C0B940` using key `9` through `FUN_00B36CA0`. `FUN_00C0B940` rechecks the interface slot and forwards the saved value/object to `FUN_00C89CD0`. The event represented by key 9 and the callback's downstream semantics are unknown.
7. The key-3 and key-9 paths have different callbacks, local owners, and token/state fields. Their shared helper establishes common registration infrastructure only. No examined call or dataflow connects either route to the Pawn manager at `pawn+0x59C`, the `FUN_00C0CA70` 0x30-stride dispatcher, `DisItemContext_UsePower`, or Blink movement.

## Evidence classification

- **Confirmed:** 107 direct code references in this Ghidra database; keyed search/update/add behavior in `FUN_00B36CA0`; key-3 registration/removal around `FUN_00C105F0`; token comparison and cleanup in `FUN_00C128B0`; key-9 registration in `FUN_00C0F9F0` and callback body in `FUN_00C0B940`.
- **Supported interpretation:** `FUN_00B36CA0` is a generic callback/delegate registration helper, based on the key lookup and the two independently traced registration lifecycles.
- **Unknown:** owner/type of the `+0x1650/+0x1654` registry manager; exact callback record schema; meanings of keys 3 and 9; event producers; owner class of `FUN_00C2F750`; semantics of `FUN_00C89CD0`; any link to user Use, `FUN_00C0CA70`, or Blink.

## Next analysis

1. Trace creation and ownership of the object whose registry array lives at `+0x1650/+0x1654`; identify the call sites that dispatch/invoke stored callbacks.
2. Recover the token returned by `FUN_00BFF440` to its producer and the native owner/state for `FUN_00C2F750` through a constructor-installed vtable or class descriptor.
3. Identify the callback trigger for key 3 and determine whether it is an asynchronous completion/state notification or input event; keep it separate from Blink until a concrete edge appears.
4. Resolve the key-9 downstream callback independently; do not infer power activation from its `DisItemPowers` owner alone.
5. Retain EXP-0032's `FUN_00C0CA70` records and EXP-0035's Pawn context-manager entries as separate schemas until shared object identity or pointer flow is observed.
