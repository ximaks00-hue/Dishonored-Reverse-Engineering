# EXP-0046 — Engine dispatch to Blink update slot +0x13C

**Status: proposed; not executed here.** Build: reported x86 Dishonored EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`. Rehash and verify Ghidra Program before native analysis.

## Goal

Identify the function and receiver that call Blink vtable `+0x13C` (`FUN_00BFC5D0`) so that warmup-target update `+0x1B0` can be placed in an engine update lifecycle without inventing tick edges.

## Procedure

1. Verify `0x01168698` Blink vtable and constructor vptr store; resolve `+0x13C` from actual bytes. Verify Transversal vtable `0x011BD0A8` and inherited/overridden slot layout.
2. Enumerate direct xrefs, address-taken uses, virtual callsites and dispatchers that load `[vptr+0x13C]`. Inspect decompiler `CALLIND` plus raw assembly, not only direct callgraph.
3. For each putative caller, establish receiver provenance to Blink or subclass from constructor/field/collection, including adjusted `this` pointers under multiple inheritance; do not treat matching offset as class identity.
4. Recover scheduler registration and timing: test `TG_PreAsyncWork` association as hypothesis, look for explicit tick/update lifecycle and state guards.
5. Trace specific warmup branch in `FUN_00BFC5D0` leading to same receiver slot `+0x1B0`; Blink target `FUN_00BFA270`, Transversal wrapper `FUN_00CF3540`, then `FUN_00BF5520` writes xyz to `+0x60/+0x64/+0x68`.
6. Link this target to reader `FUN_00BFC990` only with pointer identity and execution order; keep separate from Pawn coordinate write `FUN_006539C0`.
7. Preserve unresolved callsites and negative findings with coverage bounds; optionally cross-check a clean trusted runtime without unknown injected DLLs.

## Exit

Full evidence: outer caller VA/RVA, vptr owner, pointer chain, exact slot dispatch, branch guards, order of target update and subsequent use. Absent this, retain confirmed internal update path with *unknown engine entry*.
