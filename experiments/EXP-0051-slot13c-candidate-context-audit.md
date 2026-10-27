---
id: EXP-0051
title: "Audit generic +0x13C call candidates for Blink receiver evidence"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do the +0x13C call candidates at FUN_00C0BE60 and FUN_00C0DFD0 identify a Blink scheduler or activation edge?"
---

# EXP-0051 — Audit generic +0x13C call candidates for Blink receiver evidence

- Date: 2026-10-27 (Europe/Kiev).
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching BUILD-STEAM-10256413.
- Scope: trace two exact-build `+0x13C` instruction-pattern candidates through their static caller and object-selection paths; test whether either provides receiver-class evidence for Blink.
- Method: read-only offline function index/decompilation, raw x86 decoded from the workspace EXE, and read-only SQLite callgraph queries. No game launch, runtime attach, binary modification, or Ghidra database write. `_excluded_coop_project/` was not accessed.

## Procedure

1. Re-read `docs/research-status.md`, `docs/gameplay/blink/activation-graph.md`, and the build record; rechecked the exact EXE SHA-256.
2. Re-ran `python tools/exp0046_scan_slot13c.py --out .tmp-slot13c-recheck.csv`. It reproduced 79 load-then-call candidates and zero direct memory-call forms. Confirmed candidate rows for `FUN_00C0BE60` (`0x00C0BE79 → 0x00C0BE82`) and `FUN_00C0DFD0` (`0x00C0E077 → 0x00C0E080`); removed the temporary CSV after inspection.
3. Decompiled `FUN_00C0BE60`, `FUN_00C05B80`, `FUN_00C01BB0`, `FUN_00B2B3C0`, `FUN_00B3A580`, `FUN_00B47880`, and `FUN_00C0DFD0` through the offline static MCP.
4. Decoded raw instructions around the two indirect calls and the direct calls into `FUN_00C0BE60` from the exact EXE.
5. Checked the persisted exact-build callgraph for direct and data references to the candidate functions and associated Blink targets.

## Observations

- `FUN_00C0BE60` calls `FUN_00C05B80` with mode `0` and the second argument it received. `FUN_00C05B80` gets one array from `FUN_00C01BB0`, iterates its object pointers, calls each object's slot `+0x148`, and returns the pointer with the greatest returned value. It does not test for a Blink class or vtable.
- If that selection returns a non-null pointer, `FUN_00C0BE60` loads the selected object's vtable slot `+0x13C`, sets ECX to that selected object, passes its first explicit argument, and calls the target. Raw instructions at `0x00C0BE74–0x00C0BE82` confirm this sequence.
- `FUN_00B2B3C0` is the only direct code caller of `FUN_00C0BE60` (two sites). After geometric dot-product/angle checks, both sites pass a pointer loaded from `*( *(this+0x40) + 0x15C )` as the first argument and zero as the second. The same pointed-to object supplies position fields at `+0xC4/+0xC8/+0xCC` and a flag read at `+0x964` in this function. The concrete class identity of that pointer is not established here.
- `FUN_00B3A580` is the direct caller of `FUN_00B2B3C0`; `FUN_00B47880` calls `FUN_00B3A580` from a state/timer update body and supplies a float parameter plus an object obtained through its receiver's slot `+0x10`. This caller chain establishes the static context of the candidate, not a user button event or Blink receiver.
- `FUN_00C0DFD0` contains the other candidate sequence at `0x00C0E077–0x00C0E080`. It loads the current receiver's vtable slot `+0x13C`, passes a pointer returned by `FUN_00A49130(param_1+0x50)`, and calls the target with ECX set to the original receiver. The function's broader state-transition owner and runtime vptr remain unknown.
- The callgraph records a data reference to `FUN_00C0DFD0` at `0x0116DFA4`. Subtracting `0x13C` yields a possible table start `0x0116DE68`, but a raw executable scan finds no immediate reference to that address. The table boundary and class owner are therefore not established; the data reference alone cannot be used as vtable ownership proof.
- Blink's confirmed `+0x13C` target is `FUN_00BFC5D0`, which consumes a floating-point update parameter and switches on the Blink mode byte (EXP-0045). Neither candidate's target was resolved to `FUN_00BFC5D0`; neither candidate produced a receiver-vptr or Blink-class join.
- Ghidra MCP had no database open. Attempting to open the saved `.gpr` path returned `No load spec found`; this audit therefore used the verified offline index, exact-build binary, and callgraph only.

## Interpretation / claims

- **Confirmed:** `FUN_00C0BE60` selects an object from an indexed object array by its `+0x148` result and invokes the selected object's `+0x13C` slot with a pointer argument.
- **Observed, interpretation limited:** its caller chain places that dispatch after geometric/angle checks inside a state/timer update path. This does not name the array element type or prove an input event.
- **Confirmed:** `FUN_00C0DFD0` contains a generic same-receiver `+0x13C` virtual call with a pointer argument; the vtable owner and target are unresolved.
- **Unknown:** whether either dynamic receiver can be Blink in any runtime state. Neither static callsite identifies its target vptr or proves a Blink scheduler, UsePower method, or activation event.
- **Conclusion:** these callsites are generic slot uses, not evidence that Blink's `+0x13C` tick runs or that E7 is closed. Keep receiver identity open until a class/vptr or equivalent dataflow join is established.

## Reproduction and limitations

- Verify the EXE hash against [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Re-run the candidate scan to a temporary output; inspect the two listed candidate sites from their containing function entries.
- Confirm direct callers in `knowledge/database/callgraph.sqlite` and compare the vtable candidate against exact-build constructor/class evidence before assigning an owner.
- No live receiver, runtime vptr, or input trace was available; decompiler output remains an analysis rendering, not source code.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Candidate sweep: [EXP-0046](EXP-0046-blink-tick-dispatch-search.md)
- Blink update behavior: [EXP-0045](EXP-0045-blink-update-slot-dispatch.md)
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
