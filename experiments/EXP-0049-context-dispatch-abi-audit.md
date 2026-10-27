---
id: EXP-0049
title: "Compare Pawn context-dispatch record calls with UsePower method ABIs"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does FUN_00C0CA70 invoke a DisItemContext_UsePower object, and what does the raw argument/cleanup pattern establish about that candidate?"
---

# EXP-0049 — Context dispatcher receiver and ABI audit

- Date: 2026-10-26.
- Build: Steam build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, image base `0x00400000`; exact-build static MCP/index readiness confirmed.
- Scope: inspect `FUN_00C0CA70` raw calls through record object `entry+0x1E0`; compare stack arguments and callee cleanup with the known `DisItemContext_UsePower` targets at slots `+0x184/+0x134`.
- Method: read-only decompilation and function index/callgraph; raw x86 decoded from function entry in the workspace EXE. No game files were changed, no runtime process was launched, and `_excluded_coop_project/` was not accessed.

## Procedure

1. Re-read the required status, activation graph, and build record.
2. Decompiled `FUN_00C0CA70`, `FUN_00C4B800`, and `FUN_00C44D30`; checked their exact-build vtable entries and function boundaries.
3. Decoded raw instructions from the start of `FUN_00C0CA70` (`0x00C0CA70–0x00C0CB78`), `FUN_00C4B800` through its return (`0x00C4B800–0x00C4BA62`), and `FUN_00C44D30` (`0x00C44D30–0x00C44DA2`).
4. Queried direct callers of `FUN_00C0CA70` from the persisted exact-build callgraph.

## Observations

- `FUN_00C0CA70` iterates records with stride `0x30`, compares a record key at `entry+0x1D4`, obtains an object from `entry+0x1E0` through `FUN_005AC480`, then uses that object's vptr twice. Raw instructions at `0x00C0CB48–0x00C0CB52` call slot `+0x184` with two pushed 4-byte arguments and ECX set to the returned object. At `0x00C0CB58–0x00C0CB6E` it calls slot `+0x134` on the same object with three pushed 4-byte arguments (two floats and zero); the function returns with `RET 0xC` at `0x00C0CB76`.
- `FUN_00C4B800` is the `DisItemContext_UsePower` primary-vtable `+0x184` target (`0x011837A4`), established by constructor/vtable evidence in EXP-0028 and rechecked in EXP-0048. Its raw epilogue at `0x00C4BA60` is `RET 4`; it consumes one explicit 4-byte argument.
- `FUN_00C44D30` is the `DisItemContext_UsePower` primary-vtable `+0x134` target (`0x01183754`), established in EXP-0028/0047. Its raw epilogue at `0x00C44DA0` is `RET 4`; it consumes one explicit 4-byte argument.
- The call-site argument byte counts differ from the known UsePower implementations' single-argument `RET 4` pattern: `FUN_00C0CA70` pushes 8 bytes before `+0x184` and 12 bytes before `+0x134`. This is an ABI discrepancy to investigate, but not a strict exclusion. On 32-bit x86 a caller may pass unused extra stack arguments; both known methods read the first argument, and `FUN_00C0CA70` resets ESP to EBP in its epilogue before returning. The extra pushes therefore do not, by themselves, establish a broken stack contract or disprove the UsePower receiver.
- The direct callgraph lists five callers of `FUN_00C0CA70`: `FUN_00C2E840`, `FUN_00C2EA00`, `FUN_00C316E0` (two call sites), and `FUN_00C35AF0`. These xrefs identify code callers, not a player input event. Prior EXP-0032 describes the caller cluster as state/timer-oriented; no user-input binding is established here.
- The `+0x184` method's presence as a UsePower vtable target and its internal component `+0x168` call (EXP-0048) are real. The ABI mismatch weakens the proposed join to the `entry+0x1E0` receiver in `FUN_00C0CA70`; it does not invalidate the dispatcher or rule out a different compatible context/class at that record.

## Interpretation / claims

- **Confirmed:** `FUN_00C0CA70` calls `+0x184` and `+0x134` on the same object returned from record field `+0x1E0`, using the raw argument counts above.
- **Open/weakened:** the record object in this `FUN_00C0CA70` path may or may not be the exact known `DisItemContext_UsePower` class/vtable with targets `FUN_00C4B800` and `FUN_00C44D30`. The extra-argument pattern requires receiver/signature checking but is not enough to reject that identity because unused extra arguments can be tolerated by the callees and the caller resets its frame before return.
- **Unknown:** the runtime class of the object returned by `FUN_005AC480`; the producer/lifecycle of the `entry+0x1E0` pointer; whether any caller of `FUN_00C0CA70` originates in input handling; and which path invokes the UsePower `+0x184` vtable entry.
- **Conclusion:** keep `FUN_00C0CA70` open/weakened as a general context dispatcher. Matching slot numbers still do not prove that it dispatches `DisItemContext_UsePower` or Blink; the raw argument discrepancy alone does not disprove the candidate either.

## Reproduction and limitations

- Confirm the exact-build hash and function index through `dishonored_static.health`.
- Inspect the listed functions from their entry addresses; arbitrary mid-function disassembly can produce false instruction boundaries.
- Read the UsePower vtable words at `0x01183754` and `0x011837A4`; class/constructor association is covered by EXP-0028.
- This ABI comparison does not identify the dynamic vptr. Extra stack arguments may be unused, and the caller's frame reset prevents treating the residue as proof of incompatibility. A class/vtable or semantic argument-dataflow source is still required.
- Ghidra decompilation is an analysis rendering; the stack argument counts and `RET` immediates above are based on raw x86 instructions.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0028, EXP-0029, EXP-0032, EXP-0037, EXP-0047, EXP-0048.
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
