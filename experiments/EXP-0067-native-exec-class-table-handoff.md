---
id: EXP-0067
title: Static handoff of class native-exec table pointers
experiment_status: done
claim_status: observed
build: "10256413"
question: "Does the exact-build executable contain code that passes native-exec table addresses alongside class-name keys to a common routine?"
---

# EXP-0067 — Static handoff of class native-exec table pointers

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: read-only exact-build static follow-up to the candidate name/code-pointer records in [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md). Inspect direct xrefs, function decompilation, and raw PE words for selected `.data` table starts.
- Exclusions: no runtime execution, Ghidra database edits, or proof of downstream lookup/dispatch semantics; `_excluded_coop_project/` was not accessed.
- Tools: existing Ghidra 12.1.2 exact-build project and function index; `mcp__dishonored_static` decompilation; local cached decompile outputs; raw PE inspection.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256.
2. Queried Ghidra references to selected `.data` addresses from the EXP-0066 catalog, including `0x0128D940` and `0x0128D920`.
3. Decompiled `FUN_006067A0`, the direct caller associated with `0x0128D940`, and inspected its setup calls and callgraph context.
4. Inspected `FUN_006C5470` and `FUN_00A0DBF0`, the other direct callers of the common routine `FUN_0044C310`, for additional class/table cases.
5. Compared one table-start address and adjacent name/target values in the raw PE.

## Observations

- Ghidra reports a data xref to `0x0128D940` from `0x00606871` inside `FUN_006067A0`; the address itself is not an indexed function.
- At that code location, decompilation shows `FUN_006067A0` set a table pointer to `&PTR_s_AVolumeexecEncompassesPoint_0128d940`, obtain a `Volume` key via `FUN_00454FE0`, and pass the key and pointer to `FUN_0044C310`.
- The same function contains repeated pairs of class-name key construction and table-pointer arguments to `FUN_0044C310`; one example is `Actor` with `&PTR_s_AActorexecShouldBeHiddenBySHOW_N_0128d578`.
- Raw PE DWORDs at `0x0128D940` are `0x01007D40` (the VA of `AVolumeexecEncompassesPoint`) and at `+4`, `0x006CD8F0` (in `.text`).
- `FUN_009DD640` directly calls `FUN_006067A0` within a longer sequence of setup/helper calls. Its context appears initialization-like; this experiment does not assign a lifecycle meaning to it.
- `FUN_00A0DBF0` contains a separate, similar pattern for Dishonored-specific classes: e.g. it obtains `DisCrusher`, sets `&PTR_s_ADisCrusherexecEncroachingOn_012e3e64`, and passes both to `FUN_00B699E0`. Later portions use `FUN_0044C310` with key/table pairs. This is another static handoff example, but the helper differs in the shown call sites.
- The tested `0x0128D920` (`AActorexecSleep` table region) did not yield a direct Ghidra xref in the query. The observed `FUN_006067A0` example therefore does not account for every EXP-0066 row.
- Decompiled `FUN_0044C310` has uncertain recovered types/calling convention and calls `FUN_00B699E0`; its behavior is not named or established here.

## Interpretation / claims

- **Observed:** `FUN_006067A0` passes class-name keys and pointers to selected native-exec table starts to `FUN_0044C310` in the exact-build executable. This is a static class-table handoff path.
- **Observed:** another function, `FUN_00A0DBF0`, contains class/table handoff patterns, including calls through `FUN_00B699E0` and `FUN_0044C310`.
- **Unknown:** what either helper stores, whether the selected pointer is traversed or transformed, how `NativeToken` determines an entry at dispatch time, how remaining tables are handed off, and whether these handlers are runtime-reachable in gameplay.
- **Limit:** decompiler output is a representation of analyzed machine code, not original source. Initialization-like call context and helper names remain unproven semantics.

## Reproduction and limitations

- Re-run read-only decompilation and data-xref queries for the exact addresses using the configured exact-build Ghidra project. Compare raw DWORDs through the PE section map, not decompiler labels alone.
- The checked-in experiment records only selected examples. It does not inventory all class/table pointer pairs in the executable, and it does not complete EXP-0066's candidate token-to-handler mapping.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent candidate join: [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md)
- Selected function: `FUN_006067A0` (`0x006067A0`)
- Caller context: `FUN_009DD640` (`0x009DD640`)
