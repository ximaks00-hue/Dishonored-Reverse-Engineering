# REV-0012 — Blink Warmup virtual update, Transversal and false Swarm producer

Date: 2026-10-26. Source: user's EXP-0042 through EXP-0045 summaries. The underlying local E: experiment files, Ghidra database and game binaries were not available to this connected GitHub session. **All native conclusions are report-derived, not independently rerun.**

## Corrections and established static edges (according to reports)

1. The EXP-0039 family `FUN_00BFAE60/FUN_00BFAFD0/FUN_00BF8C00` belongs to `DishonoredActivePowerComponent_DevouringSwarm`, not Blink. The first method is at DevouringSwarm vtable `0x011682F0+0x168` and constructor is `FUN_00BF03C0`. The `0x01168458` slot address must not be reinterpreted as a Blink `+0x4F8` dispatch merely because of overlapping address arithmetic: Blink `+0x4F8` reportedly points to `FUN_004781C0`.
2. Blink vtable `0x01168698`, slot `+0x1B0 → FUN_00BFA270` calls `FUN_00BF5520` with the **same Blink ECX/this**, which writes calculated float coordinates at `this+0x60/+0x64/+0x68`. Blink `+0x1AC → FUN_00BFC990` reads this same target triplet. This closes the reported receiver-level producer/consumer link, without proving complete event-to-pawn relocation.
3. `DisDLC06ActivePowerComponent_Transversal` reportedly owns vtable `0x011BD0A8`; subclass of Blink with separate UI selection. Its `+0x1AC/+0x1B0` point to `FUN_00CF34E0/FUN_00CF3540` and forward `this` to Blink base implementations `FUN_00BFC990/FUN_00BFA270`. Data xrefs to the two wrapper methods at `0x011BD254/+0x258` are consistent with this vtable, not a generic standalone callback table.
4. Blink slot `+0x13C → FUN_00BFC5D0` executes a conditional call to `+0x1B0` on the **same runtime receiver** when `EBM_BlinkWarmup`. For Blink this calls `FUN_00BFA270`; for Transversal this calls `FUN_00CF3540`, which forwards to the base updater. The report confirms this *internal* virtual dispatch, not the engine caller of `+0x13C`.
5. Package `TickGroup=TG_PreAsyncWork` is consistent with tick scheduling; do not claim a specific engine tick callsite until source VA, actual receiver and class-layout adjustment are observed.
6. Earlier `FUN_00C0CA70` and `FUN_00C316E0` investigation still does not establish a user Use entry or the runtime owner of its `+0x184/+0x134` receiver. Keep it separate from the proven inner UsePower→Blink static bridge.

## Static target and movement distinction

The target stored at Blink object `+0x60/+0x64/+0x68` and Pawn position at `+0xC4/+0xC8/+0xCC` are **different objects and stages**. The conditional movement path through `FUN_006539C0` remains an independent proof obligation with guards, pointer provenance and runtime state.

## Next work

- EXP-0046: identify **actual** outer dispatcher for Blink `+0x13C` in the engine update/tick path, class receiver/this adjustment, and dispatch guards.
- EXP-0047: independently identify input/cast event invoking `DisItemContext_UsePower+0x134` or Blink entry slot `+0x340`. Do not reuse UI-only shortcut callers as if they cast.
- Sync primary local EXP-0039–0045 into the proper project repository once available and licensed to commit; preserve original evidence rather than copying narrative as raw logs.
