---
id: EXP-0048
title: "Trace UsePower virtual slot +0x184 into the active component slot +0x168"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the UsePower context's +0x184 method conditionally dispatch to the active power component's +0x168 method, and what Blink route follows for known Blink-family vtables?"
---

# EXP-0048 — UsePower component-slot dispatch toward Blink

- Date: 2026-10-26.
- Build: Steam build `10256413`; static MCP reports EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, image base `0x00400000`, and the ready 72,437-function index. The hash matches [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: identify the class/vtable target for `DisItemContext_UsePower +0x184`, recover the component pointer and raw indirect call in that method, then follow the target for the Blink and Transversal vtables.
- Method: read-only static MCP decompilation/function dossiers; persisted callgraph SQLite; raw PE pointer reads; Capstone x86 decoding with VA-to-file mapping; a heuristic full executable-section scan for `+0x168` and `+0x184` load-then-call patterns. No game files were changed, no game process was launched, and `_excluded_coop_project/` was not accessed.

## Procedure

1. Re-read project status, activation graph, build record, and session checklist.
2. Confirm build/hash/index readiness through `dishonored_static.health`.
3. Read the primary `DisItemContext_UsePower` vtable entry at `0x01183620 + 0x184`, and the Blink / Transversal entries at `0x01168698 + 0x168` and `0x011BD0A8 + 0x168`.
4. Decompile and inspect raw x86 for `FUN_00C4B800`, `FUN_00BFC020`, `FUN_00BFAAA0`, and `FUN_00BFC990`; keep direct call edges distinct from indirect vtable dispatch.
5. Scan executable sections for generic `+0x168` and `+0x184` load-then-call patterns. Treat the hits as candidates only, not class attribution.

## Observations

- The constructor/vtable association for `DisItemContext_UsePower` is established in EXP-0028: primary vtable `0x01183620`. Its entry at byte offset `+0x184`, VA `0x011837A4`, contains pointer `0x00C4B800` (`FUN_00C4B800`). The same table's `+0x134` target remains `FUN_00C44D30`; the two slots must not be conflated.
- In raw `FUN_00C4B800`, instructions at `0x00C4B80A–0x00C4B814` load `this+0x3C`, then load a nested pointer from `+0x114` into EDI. The method later reaches the slot dispatch only in one branch: `FUN_00BE8C50` returns nonzero and the saved result of `FUN_00B49020` is zero (`0x00C4B845–0x00C4B857`). After building/updating local component data, instructions `0x00C4B8B1–0x00C4B8BE` load the EDI object's vptr, fetch `[vptr+0x168]`, restore ECX to EDI, and call the target. This proves the same nested component pointer is both the vtable source and receiver at this callsite.
- The raw pointer at Blink vtable `0x01168698 + 0x168 = 0x01168800` is `FUN_00BFC020`. The pointer at the descriptor-associated Transversal vtable `0x011BD0A8 + 0x168 = 0x011BD210` is also `FUN_00BFC020`. Blink's table ownership is covered by earlier native-class experiments; Transversal ownership and inheritance are established in EXP-0044.
- `FUN_00BFC020` has no ordinary direct caller in the persisted callgraph; its two recorded references are the Blink and Transversal vtable data entries above. Its decompilation/raw code tests a component flag at `this+0x4C`, a positive value at `this+0x88`, and the result of component slot `+0x1A4`. It then requires `FUN_00BF8A90` and `FUN_00BE8D60` to return nonzero before calling `FUN_00BFAAA0` at `0x00BFC0D4`, with ECX restored to the same component receiver.
- `FUN_00BFAAA0` clears the byte at component `+0xC9` (`0x00BFAAFC`). If the float at the referenced config object `+0x1C` is positive, it calls `FUN_00BF8B40` and returns. Otherwise the raw instructions `0x00BFAB69–0x00BFAB73` fetch vtable slot `+0x1AC` from this component and tail-dispatch while preserving the same receiver in ECX.
- For base Blink, vtable `+0x1AC` resolves to `FUN_00BFC990` (pointer at `0x01168844`). For Transversal, it resolves to `FUN_00CF34E0` (pointer at `0x011BD254`); EXP-0044 establishes that wrapper forwards the same receiver to `FUN_00BFC990`.
- `FUN_00BFC990` compares the candidate target stored at `this+0x60/+0x64/+0x68` with pawn position `pawn+0xC4/+0xC8/+0xCC` and a config distance. It has a failure/cleanup branch and a separate branch that writes byte `this+0xC9 = 1` at instruction `0x00BFCAAC`. EXP-0024 identifies value `1` as `EBM_BlinkMove`. This is a conditional mode transition, not evidence that every call reaches that branch.
- The persisted callgraph has no ordinary direct code caller for `FUN_00C4B800`; its reference is the UsePower vtable entry `0x011837A4`. The heuristic slot `+0x184` scan finds `FUN_00C0CA70` at `0x00C0CB48/0x00C0CB52` and an internal virtual dispatch at `0x00C4B9C4/0x00C4B9CD`. EXP-0049 records an argument-count difference at the former site (two supplied arguments versus the known UsePower target's `RET 4`), but extra arguments may be ignored, so it does not establish or reject the receiver class.
- A full heuristic scan for slot `+0x168` finds 125 generic load-then-call candidates, including `FUN_00C4B800` at load `0x00C4B8B6` / call `0x00C4B8BE`; it finds no `call [base+0x168]` form. The slot `+0x184` scan finds 127 generic candidates and no direct memory-call form. Candidate CSVs are saved under `research/executable/evidence/EXP-0048-*`.

## Interpretation / claims

- **Confirmed static edge:** UsePower vtable `+0x184` → `FUN_00C4B800` → conditionally, nested component vtable `+0x168` on the same receiver.
- **Confirmed conditional route for known Blink-family vptrs:** if the nested component has the base Blink or Transversal vtable, slot `+0x168` resolves to `FUN_00BFC020`; after its guards it calls `FUN_00BFAAA0`; if the config float at `+0x1C` is not positive, the same component's `+0x1AC` dispatch reaches `FUN_00BFC990` directly for Blink or through the Transversal wrapper; `FUN_00BFC990` can set mode byte `+0xC9` to `1` on its successful branch.
- **Unknown:** whether the nested component at this `FUN_00C4B800` callsite is actually Blink/Transversal during gameplay; which code or event invokes UsePower vtable slot `+0x184`; whether the method is driven by the player's Use input; whether the guard conditions hold in play; and whether the later position-write path runs successfully for this same activation. `FUN_00C0CA70` is a generic virtual-dispatch candidate, but its receiver class remains unresolved; its argument-count discrepancy is not decisive (EXP-0049).
- **Not established:** a conversion from PowerWheel item `24`, UI enum `2`, ActivePowers index `0`, or `_iPower` to this context/component call. These identifiers remain distinct.
- **Conclusion:** this adds a second, separately evidenced static route from a UsePower-class virtual method to the Blink move-mode entry. It does not close E7 (user input/event → UsePower method), establish the runtime component identity at this callsite, or prove successful movement.

## Reproduction and limitations

- Confirm `dishonored_static.health` reports build `10256413`, the EXE hash above, and the ready function index.
- Re-read pointer words with PE VA mapping: `0x011837A4`, `0x01168800`, `0x011BD210`, `0x01168844`, and `0x011BD254`.
- Decode from function entries, not arbitrary byte offsets: `FUN_00C4B800` (`0x00C4B800`), `FUN_00BFC020` (`0x00BFC020`), `FUN_00BFAAA0` (`0x00BFAAA0`), and `FUN_00BFC990` (`0x00BFC990`). Relevant callsite windows are listed above.
- Reproduce generic scan results with `python tools/scan_vtable_slot_calls.py --slot 0x168 --max-gap 8 --out research/executable/evidence/EXP-0048-slot168-candidates.csv` and the equivalent `--slot 0x184` output path. The scanner rejects pending candidates when the loaded register is overwritten; its output is still a pattern index, not a complete callgraph.
- Static callgraph gaps do not exclude virtual dispatch, callback tables, computed calls, or runtime-populated pointers. Linear disassembly and heuristic patterns can miss alternative instruction sequences. Ghidra pseudocode is an analysis rendering, not original source.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0024, EXP-0028, EXP-0030, EXP-0044, EXP-0046, EXP-0047, EXP-0049.
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
