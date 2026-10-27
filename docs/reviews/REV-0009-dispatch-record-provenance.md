# REV-0009 — Dispatcher record identity and generic callback-registry audit

Date: 2026-10-26. **Source limitation:** report received in chat is truncated at the description of `FUN_00C2F750` in EXP-0031. This review covers only the text available. Source local EXP-0029–0031, Ghidra project, and raw decompiled functions were not accessible via connected GitHub. No game bytes independently read.

## Reported observations

- `FUN_00C0CA70` iterates records and dispatches virtual slots `+0x184` then `+0x134` on the object read at `entry+0x1E0`. `DisItemContext_UsePower` maps these slots to `FUN_00C4B800` and `FUN_00C44D30`. The actual receiver type at runtime is not established.
- Its records are described as `0x30` bytes in the report. To assign `entry+0x1E0` to a particular field, first disambiguate *entry as array element pointer* versus *container base*, and offsets applied to the element versus a nested owner. An offset larger than stride is a **strong reason to inspect the pointer base**, not a contradiction by itself.
- `FUN_00C2CCD0` and `FUN_00C2CD40` write `*(this+0x60)+0x1D4`; prior mention of writing `entry+0x1D4` cannot be treated as the same location. No direct call xrefs were reported.
- `FUN_00C2DF50` and `FUN_00C2E170` also update `+0x1D4` and `+0x1F0` of nested objects, but no proven pointer-identity bridge to the dispatcher record exists. Simple searches found only reads of `+0x1E0`; constructors, bulk copy and indirect initialization remain unexamined.
- Controller Use/Select virtual targets `+0x510/+0x50C` (reported `FUN_00AA0950/FUN_00AA0900`) modify shortcut state. In inspected direct graph `FUN_00AB7D30` does not call `FUN_00C0CA70`, UsePower or Blink mode setter. This is a scoped negative result.
- `FUN_00BFC990` mode=1 is branch-dependent; failing `FUN_00BE8D60` or overly near target reportedly routes through `FUN_00BFAB80(1)` to numeric mode 3. Semantic label for mode 3 must be checked against package enum and raw code.
- `FUN_00CF34E0` was reported as the only **direct** caller to `FUN_00BFC990`. This does not negate earlier reported indirect call via Blink slot `+0x1AC`; distinguish CALL from CALLIND/virtual dispatch.
- `FUN_00C2F750` passes a callback token into `FUN_00C105F0`; a path registers `FUN_00C128B0` via `FUN_00B36CA0` and removes it through `FUN_00AEDF80`. Actual event type/owner not known.
- `FUN_00B36CA0` finds keyed entries in a manager array and updates or appends. No evidence that **the entire registry** is dedicated to callbacks. `FUN_00C12A80` copies 20 DWORDs starting at `+0x50` and conditionally installs/removes callbacks when its first DWORD changes between zero and nonzero. It has seven reported direct callsites; no bridge to UsePower established.

## Unresolved structural ambiguity

An apparent `0x30` stride alongside an `entry+0x1E0` access is a **pointer-provenance question**: the decompiler's `entry` may be an owner of an array, a nested object, or a base containing header plus elements rather than one 48-byte record. Confirm assembly effective addresses and which register holds base before naming a field.

## Research priority

1. Find creator/allocator/bulk copy producer of the `FUN_00C0CA70` iteration storage, and establish exactly which pointer is dereferenced at `+0x1E0`.
2. Verify runtime object's vptr provenance independently; link `+0x184/+0x134` to UsePower only with explicit pointer construction/dispatch.
3. Track writers/readers of nested `+0x1D4/+0x1F0`, maintaining exact base-chain identities. Do not equate numeric offsets.
4. Classify generic registry `FUN_00B36CA0` vs callback lifecycle `FUN_00C105F0/FUN_00C12A80`; prove an event key and source only if supported.
5. Distinguish direct callers and virtual calls of Blink mode setter, then isolate state-success and failure branches.

**Completion:** actual call from game action/input event to proven UsePower instance and subsequent Blink mode/position path. Not yet achieved by supplied report.
