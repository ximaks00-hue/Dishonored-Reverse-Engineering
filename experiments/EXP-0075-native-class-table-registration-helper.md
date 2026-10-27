---
id: EXP-0075
title: Exact-build native class table registration helper
experiment_status: done
claim_status: observed
build: "10256413"
question: "What static registration structure is visible when the exact-build class/native-table handoff routine and its common helper are followed?"
---

# EXP-0075 — Exact-build native class table registration helper

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: static follow-up of `FUN_00A0DBF0`, identified in [EXP-0067](EXP-0067-native-exec-class-table-handoff.md), and common handoff helper `FUN_0044C310` → `FUN_00B699E0`.
- Exclusions: no proof of runtime invocation, table traversal/dispatch format, token-to-function semantics, or complete inventory of all registration sites. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: exact-build read-only Ghidra decompiler cache and callgraph. Cache identity for `00A0DBF0` is build `10256413` and the build-record SHA-256.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256.
2. Inspect exact static edges around `00A0DBF0` and `00B699E0`.
3. Read-only decompile `00A0DBF0`, `00B699E0`, and `0044C310`. Count string-key constructors matching `FUN_00454FE0("...",1)` in the cached `00A0DBF0` pseudocode and inspect the paired `PTR_s_...` expressions.

## Observations

- The exact-build callgraph records `FUN_009DD640` → `FUN_00A0DBF0`. `00A0DBF0` itself contains a long sequence of calls and class/table handoff expressions.
- A reproducible text scan of `knowledge/cache/decompiles/00A0DBF0.json` found 135 unique string literals passed to `FUN_00454FE0(...,1)` and 135 `PTR_s_...` expressions. Examples visible in the body include `DisCrusher` paired with `PTR_s_ADisCrusherexecEncroachingOn_...`, `DishonoredGameInfo` with a `DishonoredGameInfo` table pointer, and `DisGlobalMusicManager` with a corresponding table pointer. These counts describe decompiler output, not a validated serialized table count.
- The body calls `FUN_00B699E0` directly for 51 handoff instances and `FUN_0044C310` for 84 instances in the decompiler view. The common path at `0044C310` forwards a key and table-related pointer through `FUN_00B699E0`, then returns `*param_1 + 8 + param_2 * 0x14` in the recovered pseudocode.
- `FUN_00B699E0` first queries `FUN_00938290` using the supplied key and branches on an index equal to `-1`. In that branch it obtains a value through `FUN_009C6560`, prepares a four-word record from its inputs when a pointer is non-null, and calls `FUN_00C18870`; if that returns zero, it calls `FUN_00423970`. In the existing-index branch it copies three words into a record at `*param_1 + iVar6 * 0x14`. This is the observed pseudocode shape; the record schema and helper semantics are not independently typed.
- These bodies narrow EXP-0067's open question: the common helper exhibits key lookup, a missing-key branch, and record initialization/copy behavior. They do not demonstrate runtime dispatch through the table entries.

## Interpretation and claim limits

- **Observed:** the static body of `00A0DBF0` pairs 135 unique key-constructor strings with 135 native-table-like pointer expressions. The helper body has a key-based lookup and two record-handling branches in Ghidra's output.
- **Inferred, narrow:** this code is consistent with building or registering keyed native-function table records, based on class-like keys, `exec...`-labeled pointer expressions, and the common helper's lookup/initialization shape. This remains an inference, not a proven engine-level registration contract.
- **Unknown:** exact record layout, key namespace, token-to-entry lookup, ownership/lifetime, runtime caller conditions, and whether every pointer expression in the pseudocode represents a valid table start.
- **Limit:** this pass counts decompiler text patterns for one function only. Decompiled pseudocode is not original source, and static call edges do not prove runtime reachability.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0067 selected class/table handoffs](EXP-0067-native-exec-class-table-handoff.md)
- [EXP-0066 native token candidate joins](EXP-0066-uelib-native-token-to-executable-handler-join.md)
