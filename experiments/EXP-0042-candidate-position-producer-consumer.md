# EXP-0042 — Blink candidate position producer/consumer identity

**Status: planned (not executed).** Date: 2026-10-26. Previous exact x86 EXE SHA-256: `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; verify on local file and current Ghidra project before analysis. This EXP plan is separate from primary local EXP-0039–0041.

## Goal

Determine whether `FUN_00BF8C00` (called by `FUN_00BFAE60` and `FUN_00BFAFD0`; writes `this+0x60/+0x64/+0x68`) and `FUN_00BFC990` (reads same offsets as Blink target) operate on the **same concrete object instance**, and whether their values can reach Pawn relocation function `FUN_006539C0`.

## Procedure

1. Verify imported EXE SHA, image base and read-only DB state. Record Ghidra/tool versions, function addresses and analyzed build.
2. Independently recover constructor and vptr for receivers of `FUN_00BFAE60` and `FUN_00BFAFD0`. Compare known Blink constructor table at `0x01168698` and the two valid constructor xrefs. Do not label nearby raw addresses as vtable starts on positional proximity.
3. Enumerate code/data xrefs, direct calls, possible virtual table entries and indirect dispatchers for `FUN_00BFAE60`, `FUN_00BFAFD0`, `FUN_00BF8C00`, and `FUN_00BFC990`; preserve unknown indirect edges.
4. Reconstruct calling conventions and pointer identity at `FUN_00BF8C00` invocation sites and `FUN_00BFC990` read sites. Note secondary-inheritance `this` adjustments, pointer fields and aliasing across references.
5. Prove exact writes at `+0x60/+0x64/+0x68` and corresponding reads with disassembly site, base register, effective address and branch conditions. Document full vector source/validation logic and callers after the write.
6. Prove temporal path (writer can execute before reader on same object) or retain as unlinked observations. Same class/type alone is insufficient.
7. Only after receiver provenance, follow consumer outputs through BlinkMove/trace chain to `FUN_006539C0`, verifying source pointer, vector components, guard conditions and authoritative pawn position ownership.
8. Store evidence in local ignored output and link exact RVA/EXP/source SHA. Avoid modifying EXE, game packages or Ghidra byte data.

## Exit evidence

- Strongest: verified object identity and execution ordering, supported by concrete static call/data flow plus clean runtime observation.
- Intermediate: class type and offsets proven, instance identity unknown (explicit partial status).
- Negative: proven different object receiver/layout or disproven movement edge, with original findings retained as superseded.

Do not claim full Blink activation: keyboard/gamepad Use input to runtime cast context remains a separate open problem.
