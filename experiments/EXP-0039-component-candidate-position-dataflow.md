---
id: EXP-0039
title: Component candidate-position dataflow around FUN_00BF8C00
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What state and outputs flow through FUN_00BF8C00 and its callers, and can they be attributed to Blink movement?"
---

# EXP-0039 — Component candidate-position dataflow around `FUN_00BF8C00`

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching BUILD-STEAM-10256413.
- Ghidra project: `Dishonored-RHCP-10256413`, x86, image base `0x00400000`; decompilation used the read-only static MCP headless service. Raw instruction bytes were independently decoded from the same EXE with Capstone 5.0.7.
- Scope: calls to `FUN_00BF8C00`, its caller-side argument setup, and the vtable/field evidence relevant to the candidate's owner. This is not a runtime test.
- Exclusions: no game launch or modification; `_excluded_coop_project/` not accessed. The known Blink `+0x340` route, UsePower bridge, Pawn-manager ABI reject, and confirmed `FUN_006539C0` position write remain separate evidence paths.

## Procedure

1. Confirmed the executable identity against the build record and static service health.
2. Decompiled `FUN_00BF8C00`, its direct callers `FUN_00BFAE60`, `FUN_00BFAFD0`, and `FUN_00BFE3C0`, plus neighboring state helpers using read-only static analysis.
3. Decoded raw instructions around call sites `0x00BFAEF3`, `0x00BFB04E`, and `0x00BFE4B9` to verify ECX and stack arguments where the pseudocode's prototype was insufficient.
4. Read the executable's DWORD table entries around `0x01168380`–`0x01168698` and scanned the image for absolute occurrences of candidate table addresses and relevant function targets.

## Observations

### `FUN_00BFAE60` → `FUN_00BF8C00`

- `FUN_00BFAE60` requires a positive value at `this+0x88`, then calls virtual slot `+0x1A4`. It reads a per-level record from the pointer at `this+0x8C`, at `0x114 + index*0x48`, computes two vectors with `FUN_00BE9310`, and calls `FUN_00BF8C00` at `0x00BFAEF3`.
- Raw instructions at the call site set ECX to the original `this` pointer and push pointers to two local 3-float vectors. Thus `FUN_00BF8C00` operates on that same receiver; the high-level pseudocode prototype alone obscures this argument relationship.
- `FUN_00BF8C00` lazily obtains a helper object into `this+0x94`, calls `FUN_00BF77B0` with the calculated vectors and fields from the receiver, then checks the resulting point against entries from another array. On its accepted branch it writes the calculated XYZ to helper-object offsets `+0xC4/+0xC8/+0xCC`, copies those three values to receiver offsets `+0x60/+0x64/+0x68`, optionally copies an input vector to an output argument, and returns `1`.
- If `FUN_00BF8C00` succeeds, `FUN_00BFAE60` calls receiver virtual slot `+0x178`, runs state/time helpers, updates fields at `this+0xA4/+0xA8`, and returns `1`. The failure path makes UI/helper calls and returns `0`.

### Other callers

- `FUN_00BFAFD0` enters when bit 0 at `this+0xA8` is set. It reads the same `+0x88`/`+0x8C` level-and-record pattern, calls `FUN_00BF8C00` with ECX equal to the same receiver, converts a vector, writes it through `FUN_00BE9520` to the helper object at `this+0x94` plus `+0xC4`, calls `FUN_00BED6D0`, and sets bit 2 at `this+0xA8`.
- `FUN_00BFE3C0` is a state/serialization-style caller. On a gated branch it calls `FUN_00BF8C00` with ECX equal to its receiver, with that receiver's `+0x94` subobject plus `+0xC4` as an input vector; it then writes the returned vector back through `FUN_00BE9520`. It also registers `FUN_00BFDDF0` under key `3` through `FUN_00B36CA0`; EXP-0036 found no Use/Blink join for that shared registry.
- These helpers write candidate/helper coordinates, not the pawn's authoritative coordinates. The known conditional pawn writes remain the separate `FUN_00BECDF0` → `FUN_006539C0` path in EXP-0024.
- EXP-0030 independently records that `FUN_00BFC990` reads the stored target from component offsets `+0x60/+0x64/+0x68` when evaluating the move-mode transition. This gives an exact field-offset overlap between the candidate writer and the move-mode reader, but does not yet prove that both functions receive the same runtime class/instance.

### Attribution limits

- EXP-0023 establishes Blink fields `+0x88` and `+0x8C` as strong inferences for current level and tweak pointer. EXP-0039 observes the same offsets and per-level-record access pattern in `FUN_00BFAE60`/`FUN_00BFAFD0`.
- Blink's installed vtable at `0x01168698` maps slot `+0x1A4` to `FUN_00BE71F0`; that target queries slots `+0x18C` and `+0x160` and returns a boolean-like result. `FUN_00BFAE60` also calls `+0x1A4`, a compatibility clue, but no xref proves that its receiver uses Blink's installed vptr.
- The function pointer `FUN_00BFAE60` occurs at data address `0x01168458`; `FUN_00BFE3C0` at `0x01168408`; and `FUN_00BF8DD0` at `0x011685EC`. The image scan found no absolute pointer occurrence for candidate table starts `0x01168410` or `0x011685C0`. These data runs therefore do not establish a live vtable owner or constructor. The earlier proposed owner for `0x011685C0` remains unknown.

## Interpretation / claims

- **Confirmed:** caller-side raw instructions pass the same receiver in ECX to `FUN_00BF8C00`; `FUN_00BF8C00` conditionally computes/validates a candidate and writes it to helper-object coordinates and receiver `+0x60/+0x64/+0x68`.
- **Confirmed:** `FUN_00BFAE60` and `FUN_00BFAFD0` use a per-level record addressed through receiver `+0x8C`, with level-like index at `+0x88` and record stride `0x48` in this access path.
- **Confirmed cross-experiment field overlap:** candidate writer `FUN_00BF8C00` stores receiver `+0x60/+0x64/+0x68`; move-mode entry `FUN_00BFC990` reads those offsets as its stored target (EXP-0030). This proves the code-level field overlap, not a shared runtime receiver.
- **Inferred:** these functions may belong to Blink/active-power candidate machinery because their field pattern matches EXP-0023, slot `+0x1A4` is compatible with the Blink table, and the fields they write are consumed by the Blink move-mode entry. Concrete receiver class and same-instance flow remain unproved.
- **Unknown:** owner/constructor of data tables around `0x01168410` and `0x011685C0`; whether any receiver in these functions is actually Blink; what gameplay event calls `FUN_00BFAE60`; and whether its candidate output feeds the confirmed `FUN_00BECDF0` → `FUN_006539C0` movement path.
- **Conclusion:** this pass identifies a stronger candidate bridge from candidate computation to Blink's stored move target, based on exact matching offsets. It does not yet add a confirmed activation or same-instance movement edge. Keep the relation explicitly inferred until receiver ownership is established.

## Reproduction and limitations

- Re-decompile the named functions read-only, then inspect raw x86 around the three listed call sites to verify ECX and stack arguments.
- Table/function address scans are bounded to absolute pointer representations in the mapped EXE. Computed pointers and runtime initialization are not excluded.
- Ghidra pseudocode is a decompiler rendering, not original source; use raw instructions for calling-convention conclusions.

## Next action

Identify the constructor/vptr producer for the receiver in `FUN_00BFAE60` or find a concrete caller that passes a known Blink object. The exact `+0x60/+0x64/+0x68` overlap with `FUN_00BFC990` is the discriminating lead: prove that both methods operate on a Blink instance, then test whether that stored target feeds the known `FUN_00BECDF0`/`FUN_006539C0` pawn-position path.
