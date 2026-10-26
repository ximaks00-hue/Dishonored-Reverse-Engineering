# EXP-0037 — Pawn context-manager record creation and UsePower ABI

**Status: planned, not executed.** Date: 2026-10-26. Source build previously reported x86 EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (recheck Ghidra Program and exact EXE before running). This plan is not an overwrite of the user's local primary EXP-0035/0036.

## Core hypotheses

H1: The manager object stored at `DishonoredPlayerPawn+0x59C` constructs/stores `DisItemContext_UsePower` instances in at least one runtime mode.
H2: `FUN_00C04C30` is **not** invoking UsePower `FUN_00C44D30` at slot `+0x134`, because the expected float argument and `RET 4` stack contract reportedly disagree. Verify raw assembly before accepting this exclusion.
H3: The generic manager at `+0x1650` and `FUN_00B36CA0` are unrelated to the UsePower activation edge until an event key, registration and invocation are traced.

## Exact read-only protocol

1. Revalidate SHA, image base and program database identity. Record Ghidra version, function counts, parser warnings.
2. Resolve `FUN_00B58860`, `FUN_00AB3210` vtable ownership and entry thunks; reconstruct reads/writes to `pawn+0x59C`. Follow constructor, initialization, cleanup and manager instance allocation.
3. Trace allocation and filling of manager slots: exact pointer base, stride/count/capacity, vptr installs, class descriptor, writes of context object pointer and possible default-object construction. Search memcopies/serialization and not only direct `MOV [base+offset], immediate`.
4. Inspect raw instructions around the virtual calls in `FUN_00C04C30`; annotate `ESP` delta before/after and explicit stack arguments; compare with `FUN_00C44D30` prologue/epilogue `RET 4` and possible adapter thunk. A mismatched signature may mean a different class owns this slot.
5. Independently follow `DisTweaks_ItemPowers → DisTweaks_UsePower → DisItemContext_UsePower` from package-default metadata into native instantiation. Do not assert runtime creation based solely on a class reference.
6. Inspect registration at manager `+0x1650`: identify object owner and indexed records for keys 3 (`FUN_00C128B0`) and 9 (`FUN_00C0B940`); prove the callback-to-event mapping or leave it unknown.
7. Compare this evidence with `FUN_00C0CA70` and its `0x30`-stride array. Demonstrate pointer identity via producer/consumer chain, not shared slot numbers.
8. If a trusted clean runtime is accessible, instrument inputs and vptr identities at cast time; avoid unknown injected DLLs and preserve read-only static project.

## Exit criteria

- Demonstrate a specific runtime UsePower receiver in Pawn's context manager with constructor/vptr proof.
- Recover the correct ABI/call target at manager dispatcher `+0x134`.
- Establish event/context connection from user input to Blink component `+0x174`, or explicitly reject that candidate route with assembly-level evidence.
- Keep full Blink move-to-coordinate path conditional until independently verified end-to-end.
