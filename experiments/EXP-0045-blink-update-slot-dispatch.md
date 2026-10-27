---
id: EXP-0045
title: "Blink update slot dispatches target refresh"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does Blink's +0x13C update method dispatch the +0x1B0 target updater on the same receiver, and what is known about its scheduling?"
---

# EXP-0045 — Blink update slot dispatches target refresh

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching BUILD-STEAM-10256413.
- Package: extracted `DishonoredGame.upk`; SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`.
- Ghidra/index: x86, image base `0x00400000`; read-only static decompilation and persisted callgraph. Raw x86 decoded from the on-disk EXE with PE-section VA mapping.
- Exclusions: no game launch or modification; `_excluded_coop_project/` not accessed.

## Procedure

1. Rechecked `docs/research-status.md`, the Blink activation graph, and the build record; recomputed the EXE and extracted-UPK hashes.
2. Confirmed the Blink and Transversal table entries for `FUN_00BFC5D0` and `FUN_00BFA270` / `FUN_00CF3540` from the exact-build callgraph.
3. Decompiled `FUN_00BFC5D0` read-only and decoded raw x86 around its mode switch and indirect call (`0x00BFC641–0x00BFC6AF`).
4. Read the preserved UELib default-object output for `DishonoredActivePowerComponent_Blink` and its `TickGroup` value.
5. Cross-checked Transversal inheritance and wrapper receiver behavior against EXP-0044.

## Observations

- Blink vtable `0x01168698` has `FUN_00BFC5D0` at `+0x13C` (`0x011687D4`). The Transversal subclass vtable `0x011BD0A8` also has `FUN_00BFC5D0` at `+0x13C` (`0x011BD1E4`).
- `FUN_00BFC5D0` accepts a 4-byte floating-point argument, reads the receiver's mode byte at `this+0xC9`, and dispatches by mode. In case `0` it loads the receiver's vptr, fetches slot `+0x1B0`, sets ECX back to the original receiver, passes the float argument, and calls the loaded target. Raw instructions: `0x00BFC67C–0x00BFC68D`.
- In case `1`, `FUN_00BFC5D0` calls `FUN_00BFC160`; in cases `2` and `3`, it calls `FUN_00BED480`. The package enum in EXP-0024 identifies mode `1` as `EBM_BlinkMove`; the Blink enum identifies mode `0` as `EBM_BlinkWarmup`.
- For a base Blink vptr, slot `+0x1B0` resolves to `FUN_00BFA270`. For Transversal, slot `+0x1B0` resolves to `FUN_00CF3540`; EXP-0044 and raw instructions show that wrapper forwards the same receiver and float argument to `FUN_00BFA270`.
- `FUN_00BFA270` calls `FUN_00BF5520`, which writes candidate coordinates to receiver `+0x60/+0x64/+0x68`; `FUN_00BFC990` consumes those fields on the same class-shaped receiver (EXP-0043/0030).
- `FUN_00BE7580` is present at `+0x174` in both the base Blink and Transversal vtables. It conditionally dispatches the same receiver's `+0x1AC` slot after a manager call (EXP-0028). Therefore, if the active component passed by UsePower is a Transversal instance, this slot resolves to `FUN_00CF34E0`, which tail-dispatches to Blink base `FUN_00BFC990` on the same object (EXP-0044). This is a conditional static route; the runtime receiver at the UsePower callsite is not established.
- The Blink default object in the preserved UELib output specifies `TickGroup=ETickingGroup.TG_PreAsyncWork`. `FUN_00BFC5D0`'s float parameter and timer updates are consistent with a tick/update callback. The package setting does not itself show the engine scheduler's machine-code call site or prove that the method executes in a particular play session.
- The direct-call graph has no code caller of `FUN_00BFC5D0`; its observed references are the Blink and Transversal vtable entries. The generic engine dispatch that invokes slot `+0x13C` is not recovered by this experiment.
- A follow-up caller-index query finds no ordinary direct code caller of base `FUN_00BFA270`; its sole direct caller is Transversal wrapper `FUN_00CF3540` at `0x00CF3552`. Base Blink reaches `FUN_00BFA270` through its `+0x1B0` vtable entry, and `FUN_00BFC5D0` reaches the virtual slot only in mode 0. This bounds the static routes but does not identify the engine's indirect dispatch site.
- The same follow-up rechecked the separate `FUN_00C0CA70` caller cluster: `FUN_00C316E0` selects argument triples from state/timer-indexed records and calls the dispatcher at `0x00C317B0` or `0x00C317CF`; its direct callers are `FUN_00C35A60`, `FUN_00C35AC0`, and `FUN_00C35AF0`. The two first functions use state/timer/global values, and `FUN_00C32730` reaches `FUN_00C2E840` only in a count/state branch. These observations add no input or Blink edge and do not identify the record receiver's dynamic class (EXP-0032).

## Interpretation / claims

- **Confirmed:** Blink update slot `+0x13C` dispatches slot `+0x1B0` on the same receiver when the mode byte is `0` (`EBM_BlinkWarmup`).
- **Confirmed:** with a base Blink vptr, that dispatch resolves to `FUN_00BFA270`; with a Transversal vptr, it resolves to `FUN_00CF3540`, which forwards to the inherited Blink updater with the same receiver.
- **Confirmed conditional static route:** UsePower `+0x134` → component `+0x174` → inherited `FUN_00BE7580` → virtual `+0x1AC`; for a Transversal receiver, `+0x1AC` resolves through `FUN_00CF34E0` to base `FUN_00BFC990`. Actual runtime receiver identity and user-input entry remain unknown.
- **Confirmed static bridge:** the warmup update route can refresh the target fields used by Blink's move-mode method; this does not imply that movement occurs during warmup.
- **Inferred:** Blink's package `TickGroup` plus the float update signature indicate that `FUN_00BFC5D0` participates in scheduled component ticking. The actual engine dispatch site and runtime execution remain unobserved.
- **Unknown:** what input/event enters `FUN_00C44D30`, invokes Blink `+0x340`, or changes the mode from warmup to move; whether the Transversal subclass update path runs for a player-controlled instance.
- **Unknown:** which engine-side tick/indirect dispatcher invokes `FUN_00BFC5D0` at vtable `+0x13C`; the direct-call index cannot enumerate virtual dispatch.
- **Conclusion:** the previously open writer-scheduling question is narrowed to the component's own `+0x13C` mode dispatcher. E7 (user input/event → activation) remains open.

## Reproduction and limitations

- Recompute the two hashes above; confirm build identity in `BUILD-STEAM-10256413`.
- Inspect `knowledge/database/callgraph.sqlite` data edges at `0x011687D4`, `0x011BD1E4`, `0x01168848`, and `0x011BD258`, and direct callers for `FUN_00BFA270` and `FUN_00C316E0`.
- Decode the EXE instructions at `0x00BFC67C–0x00BFC68D` and compare to `FUN_00BFC5D0`'s mode switch. Map VA through PE sections before reading raw offsets.
- Read the preserved UELib dump for Blink default properties. It is an analysis rendering of package data, not source code.
- Static reachability and `TickGroup` configuration do not establish runtime invocation, input provenance, or successful movement.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0024, EXP-0030, EXP-0032, EXP-0043, EXP-0044.
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
