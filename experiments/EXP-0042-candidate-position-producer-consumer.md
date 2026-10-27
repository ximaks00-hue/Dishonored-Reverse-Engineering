---
id: EXP-0042
title: Candidate position producer/consumer identity
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do FUN_00BFAE60 / FUN_00BFAFD0 / FUN_00BF8C00 and FUN_00BFC990 share one Blink instance, and does that feed FUN_006539C0?"
---

# EXP-0042 — Candidate position producer/consumer identity

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra project: `Dishonored-RHCP-10256413`, x86, image base `0x00400000`; headless `-noanalysis -readOnly`.
- Scope: class/vtable provenance for the candidate writer chain and whether it aliases the Blink move-mode reader / pawn writer.
- Exclusions: no game launch; `_excluded_coop_project/` unused. Does not claim full input→Blink activation (E7).

## Procedure

1. Verified EXE SHA against BUILD-STEAM-10256413.
2. Absolute DWORD scan of the EXE for producer/consumer function pointers and known table starts (`tools/exp0042_vtable_probe.py`).
3. Compared slot contents of ActivePower base `0x01167F60`, DevouringSwarm `0x011682F0`, and Blink `0x01168698`.
4. Headless `ExportCandidateOwnerEvidence.java` + `DumpXrefsAndDisasm.java` for xrefs and call-site ECX setup on `FUN_00C44E30`, `FUN_00C43410`, `FUN_00BED550`, constructors, and the producer/consumer functions.
5. Resolved the lazy class global used by the cast helper to its native descriptor / UTF-16 name.

Artifacts (gitignored): `.tmp/EXP-0042-*.csv`, `.tmp/EXP-0042-disasm-*.txt`.

## Observations

### Vtable ownership

- Blink table `0x01168698` (constructors `FUN_00BF9A10` / `FUN_00BF8A10`) contains `FUN_00BFC990` at `+0x1AC`. At `+0x4F8` it holds `FUN_004781C0`, **not** `FUN_00BFAE60`.
- DevouringSwarm constructor `FUN_00BF03C0` (descriptor `0x0135AB08`, name `DishonoredActivePowerComponent_DevouringSwarm`) installs primary vptr `0x011682F0` (two absolute image refs). At `Swarm+0x168` (`0x01168458`) the DWORD is `FUN_00BFAE60`.
- The address `0x01168458` is simultaneously `ActivePowerBase+0x4F8` if the base table is treated as a long contiguous run. That coincidence is **region overlap in `.rdata`**, not proof that Blink dispatches `FUN_00BFAE60`. Blink’s own `+0x4F8` differs. Swarm’s table start has constructor xrefs; the bare slot address still has none (consistent with EXP-0040).
- `FUN_00BFAFD0` and `FUN_00BF8C00` have **no** absolute pointer occurrences in the image. `FUN_00BFAE60` has exactly one (the Swarm/`0x01168458` slot).

### Producer call path (DevouringSwarm)

- Only code xref to `FUN_00BFAFD0`: tail `JMP` at `0x00C44E48` inside `FUN_00C44E30`.
- Raw site: `ECX=[ECX+0x3c]`; `EAX=[[ECX]+0x114]`; `CALL FUN_00C43410(EAX)`; on success `ECX=EAX` then `JMP FUN_00BFAFD0`.
- `FUN_00C43410` walks the UE3 class chain at `obj+0x30` / `+0x44` against global `DAT_0146F290`. Lazy init `FUN_00BED550` loads that global from descriptor `0x0135AB08` → UTF-16 **`DishonoredActivePowerComponent_DevouringSwarm`** (constructor pointer `FUN_00BF03C0`). On match it returns the same object pointer.
- Therefore the `this` passed into `FUN_00BFAFD0` is a component that passed **DevouringSwarm** `IsA`, not Blink.
- `FUN_00BFAFD0` keeps `ESI=ECX`, gates on `this+0xA8` bit0, uses `+0x88`/`+0x8c`, and `CALL FUN_00BF8C00` with `ECX=ESI` at `0x00BFB04E` (same-receiver write path already recorded in EXP-0039).
- Direct code xref to `FUN_00BFAE60`: only DATA from `0x01168458`. No non-virtual callers in this export. Virtual dispatch to it is through the Swarm table slot above (and any other class that still shares that slot DWORD).

### Consumer path (Blink) — unchanged ownership

- `FUN_00BFC990` remains Blink `+0x1AC` with DATA xref from `0x01168844` and direct call from `FUN_00CF34E0` (EXP-0024/0030).
- It still reads stored target `this+0x60/+0x64/+0x68` and, on the successful branch, sets move-mode byte `this+0xC9=1`. Downstream gated pawn write `FUN_00BECDF0` → `FUN_006539C0` remains as in EXP-0024.

### Field-offset overlap reinterpreted

- Writer `FUN_00BF8C00` and reader `FUN_00BFC990` still both use `+0x60/+0x64/+0x68`.
- With Swarm vs Blink receivers, that overlap is **shared ActivePower-shaped layout**, not evidence that one instance is both producer and Blink consumer.

## Interpretation / claims

- **Confirmed:** `FUN_00BFAE60` is a DevouringSwarm vtable method at `0x011682F0+0x168`; Swarm vptr install has constructor evidence.
- **Confirmed:** `FUN_00BFAFD0` is entered only through `FUN_00C44E30` after an `IsA(DishonoredActivePowerComponent_DevouringSwarm)` cast (`FUN_00C43410` / `DAT_0146F290` / descriptor `0x0135AB08`); ECX for `FUN_00BF8C00` is that same receiver.
- **Confirmed:** Blink does **not** place `FUN_00BFAE60` at its `+0x4F8` (or elsewhere in the compared Blink prefix); Blink `+0x1AC` remains `FUN_00BFC990`.
- **Confirmed negative (same-instance Blink join):** static evidence attributes the studied producer chain to **DevouringSwarm**, not Blink. Matching `+0x60/+0x64/+0x68` alone does **not** prove producer/consumer identity with BlinkMove.
- **Confirmed (separate, prior):** Blink move-mode → conditional `FUN_006539C0` pawn write path still stands on its own EXP-0024/0030 evidence.
- **Unknown / open:** gameplay event that calls `FUN_00A96B50` → `FUN_00C44E30`; whether any *other* writer fills Blink’s `+0x60/+0x64/+0x68` before `FUN_00BFC990`; E7 input→Blink activation.
- **Supersedes (hypothesis-scoped):** EXP-0039’s inference that `FUN_00BFAE60`/`FUN_00BFAFD0` are likely Blink candidate receivers based on field/slot compatibility. Keep EXP-0039’s raw ECX/`+0x60` write observations; drop the Blink-owner inference for this chain.

## Reproduction

1. `python tools/exp0042_vtable_probe.py`
2. Headless read-only: `ExportCandidateOwnerEvidence.java`, `DumpXrefsAndDisasm.java` on the addresses above.
3. Confirm descriptor `0x0135AB08 +0x10` → UTF-16 `DishonoredActivePowerComponent_DevouringSwarm`.

## Links

- Prior: EXP-0039, EXP-0040, EXP-0030, EXP-0024, EXP-0023, REV-0011.
- Scripts: `research/executable/scripts/ExportCandidateOwnerEvidence.java`, `DumpXrefsAndDisasm.java`, `tools/exp0042_vtable_probe.py`.
