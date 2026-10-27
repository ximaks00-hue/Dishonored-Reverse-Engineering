---
id: EXP-0140
title: Shared class-table target for native TakeDamage exports
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What static role is supported for the highest-connectivity indexed target in the EXP-0139 class-table candidate overlay?"
---

# EXP-0140 — Shared class-table target for native TakeDamage exports

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: manually inspect the highest-connectivity indexed function in the EXP-0139 class-table target catalog, at VA `0x005C1640`, and compare the visible call shape with all ten joined UELib declarations.
- Exclusions: no concrete class ownership, vtable slot naming, table extent, consumer or dispatch proof, runtime execution, damage behavior, or argument-to-field mapping beyond what the decompiler shows. Pseudocode is decompiler output, not source code.
- Inputs: exact-build function index; EXP-0139 332-edge join and 254-address static candidate catalog; matching UELib JSONL function records; read-only decompiler output cached with executable build/hash identity.
- Durable outputs: [one-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0140.csv), [29-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0140.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0140.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; require build 10256413 and the recorded executable SHA-256.
2. Select the indexed candidate with the most EXP-0139 target edges. Resolve its exact index row and body range.
3. Decompile the exact address with the read-only static gateway. Verify the saved result records the same build and executable hash; hash the pseudocode text.
4. Inspect the raw pseudocode for frame/code-pointer reads, indirect decode callback calls, pointer advancement, conditional bytes, and final call shape. Do not assign source-level parameter types based on stack aliases.
5. Compare the raw class/method names, UELib object paths, token values, script sizes, and declarations for every edge to this target. Record disagreements and keep runtime, ownership, and dispatch claims open.
6. Add the address to the manual body-review overlay as L1 analysis with a limited static-role candidate. Do not add a confirmed claim or runtime record.

## Observations

- `0x005C1640` is an indexed 445-byte function (`FUN_005c1640`, body range `0x005C1640–0x005C17FC`) and has ten EXP-0139 class/method target edges, the highest multiplicity in that catalog.
- All ten raw exec names end in `execTakeDamage`. The UELib paths are `Function'<package>.<class>.TakeDamage'`; every export has `NativeFlag=true`, `NativeToken=0`, and script size 39. The parameter types and order agree across the declarations: damage amount, controller, hit location, momentum, damage type, optional hit info, and optional damage causer. Some parameter names differ, and `KAsset` is marked `native simulated event` while the others are `native event`.
- The saved decompiler result is tied to build 10256413 and executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; pseudocode SHA-256 is `64EB40840B65288229030954559F5044EE007008824F3014CE90ACC89C61F11B`.
- The body repeatedly reads one byte through the code pointer at `param_1+0x18`, advances that pointer, and invokes a callback selected from `DAT_014068F0` with the frame and output storage. Near the end it conditionally consumes an `'A'` byte through `DAT_014069F4`, then makes an indirect virtual call through `local_14` at vtable displacement `+0x148`, passing nine recovered stack values. The decompiler does not recover reliable source types or a name for that virtual slot.
- The selected address was previously in the EXP-0072 `unknown` subsystem bucket and had no EXP-0124–0128 manual body review. This review adds one L1 analysis record; it adds no confirmed semantic claim, L3 dataflow edge, or L4 runtime record.

## Interpretation and claim limits

- **Observed:** an exact-build function targeted by ten raw class-table records whose names and UELib exports identify `TakeDamage` performs repeated frame/code-byte decoding and then an indirect virtual call with seven declared arguments plus two recovered values.
- **Inferred, limited:** the function is a shared native `TakeDamage` executor/thunk candidate, likely decoding script arguments before invoking a receiver virtual method. The matching export names, common declarations, zero tokens, shared target address, and body call shape support this role together.
- **Unknown:** the concrete class or implementation behind vtable slot `+0x148`, exact argument-to-local mapping, whether every listed class consumes the same implementation, how the pointer table is used, and all runtime reachability/effects.
- The body review does not establish damage calculation or application. Exact target/name association is static evidence; it does not prove runtime dispatch.

## Reproduction and limitations

1. Use the repository's read-only static decompiler for address `005C1640`.
2. Compare its saved build/hash identity and pseudocode hash with those recorded above.
3. Rebuild the UELib associations by running the EXP-0139 reproducer against its ignored census inputs, then select rows whose `raw_handler_target_va` equals `0x005C1640`.

The review is one static decompile of one function. Ghidra's local writable database was not opened or changed. Decompiler stack-variable recovery may alias local storage, so this experiment records control/data operations and the final indirect-call shape without naming fields or the virtual method.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent target join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Raw pointer validation: [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- Function progress gates: [function evidence model](../docs/methodology/function-evidence-model.md)
