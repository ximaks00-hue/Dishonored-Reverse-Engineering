---
id: EXP-0038
title: Blink virtual slot 0x340 call-site triage
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do static indirect calls through slot +0x340 identify a Blink receiver or an input/activation event?"
---

# EXP-0038 — Blink virtual slot `+0x340` call-site triage

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (matches `BUILD-STEAM-10256413`).
- Ghidra project: `dishonored_exact_full`, x86, image base `0x00400000`; headless exports used `-noanalysis -readOnly`.
- Scope: static x86 call-site inventory for virtual displacement `+0x340`, followed by bounded inspection of its call contexts and table references. No runtime attach, game launch, patch, or game-file modification.
- Exclusions: no inference from matching field offsets alone; no use of the rejected Pawn-manager ABI path as a Blink edge; `_excluded_coop_project/` not accessed.

## Procedure

1. Confirmed the EXE SHA-256 against `research/builds/BUILD-STEAM-10256413/build.md`.
2. Ran `research/executable/scripts/ExportBlinkVcallSites.java` read-only against the existing Ghidra project for slot offsets `0x340` and `0x134`. The script exports instruction candidates only; matching the displacement does not establish a receiver type.
3. Inspected the `+0x340` candidates and cross-checked incoming direct calls/data references in the locally imported callgraph mirror. Raw candidate exports are in ignored `.tmp/EXP-0038-vcalls-340.csv` and `.tmp/EXP-0038-vcalls-134.csv`.
4. Compared findings with the established Blink vtable/constructor mapping in EXP-0022 and the separate dispatch analysis in EXP-0027.

## Observations

- The `+0x340` scan emitted 20 syntactic candidates. Manual instruction-context triage retained three indirect-call sites:
  - `FUN_00652CF0`: reads receiver vtable slot `+0x340` near `0x00653223`, calls the loaded target near `0x0065322B` under `DAT_0141295C != 0` and `FUN_00784580() == 0`.
  - `FUN_007589C0`: virtual call through `this+0x340` near `0x00758A28`/`0x00758A30`.
  - `FUN_009F1D40`: virtual call through a parameter object's `+0x340` slot near `0x009F1D66` (site verified in the read-only instruction export).
- Other raw scan matches were false positives such as an immediate `0x340`, `LEA`, or a field load not used as the target of an indirect call.
- `FUN_00652CF0` has many direct callers across the image. One caller, `FUN_00BF8DD0`, passes `*(this+0xB0)` when nonzero and clears that field after the helper call. The nested receiver's runtime class is not established.
- The only indexed reference to `FUN_00BF8DD0` is a data reference from `0x011685EC`, corresponding to candidate table address `0x011685C0 + 0x2C`. No direct code caller or recovered reference to the candidate table start was found in the imported callgraph.
- `FUN_007589C0` and `FUN_009F1D40` likewise have no direct code callers in the imported callgraph; their function targets are referenced from data addresses `0x010C36D8`, `0x012E36BC`, and `0x012E4BE4`, respectively. The owning tables/classes remain unidentified.
- The Blink constructor `FUN_00BF9A10` installs vtable `0x01168698`; its `+0x340` entry is `FUN_00BE89E0` (EXP-0022/0027). This confirms the Blink target mapping, not that any of the generic receivers above is a Blink instance.
- `FUN_00BE89E0` has no direct code caller in the imported callgraph; its observed references are vtable data entries, including Blink's `0x011689D8` and a second table entry at `0x011C58E0` whose owner is unknown (EXP-0027).

## Interpretation / claims

- **Confirmed:** the exact-build image contains the three inspected indirect-call sites through a displacement of `+0x340`; `FUN_00652CF0` includes the stated gate and receiver flow.
- **Confirmed:** Blink's constructor-installed vtable maps `+0x340` to `FUN_00BE89E0` (EXP-0022/0027).
- **Observed:** the callgraph mirror has no direct callers for `FUN_00BF8DD0`, `FUN_007589C0`, or `FUN_009F1D40`; the listed data references are present. This is bounded by the imported static index and Ghidra's recognized references.
- **Unknown:** whether any of the three generic call sites receives a Blink object; the owner/constructor of candidate table `0x011685C0`; the semantic type of `FUN_00BF8DD0.this+0xB0`; and the input/event path into Blink `+0x340` or `UsePower +0x134`.
- **Conclusion:** this pass adds no discriminating evidence that joins generic `+0x340` dispatch to Blink activation. E7 remains open. Do not interpret `this+0xB0` here using Blink component fields at the same offset.

## Limitations and reproducibility

- The Java scanner matches textual instruction operands and intentionally over-approximates candidates; manual instruction review is required. It is not a class/vtable ownership resolver.
- The offline callgraph mirror stores Ghidra-recognized call/data references, not all computed or runtime-created pointers. Absence of a reference is bounded negative evidence only.
- The CSV outputs are ignored transient artifacts and are not part of the durable source record. Reproduce with `ExportBlinkVcallSites.java`, arguments `340` and `134`, against the named build/project using headless `-noanalysis -readOnly`; preserve the generated CSV and manual classification if the experiment is repeated.
- Existing Ghidra project data was read-only. No game files were changed.

## Next action

Recover the owner and constructor for candidate table `0x011685C0`, then determine the runtime type and producer of the object passed from `FUN_00BF8DD0.this+0xB0`. Continue E7 only if that establishes a Blink receiver or an input/animation event. In parallel, inspect table owners for `FUN_007589C0` and `FUN_009F1D40` only if constructor evidence can resolve receiver types.
