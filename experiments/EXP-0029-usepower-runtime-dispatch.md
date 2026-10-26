# EXP-0029 — Resolve UsePower dispatch and runtime Blink receiver

**Status: planned, not executed.** Date 2026-10-26. Based on user-reported static paths and exact previously reported x86 EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`. No raw Ghidra traces are available in this chat.

## Central research question

What actual event dispatches `DisItemContext_UsePower` vtable slot `+0x134` (`FUN_00C44D30`), and under which conditions does it invoke the `DishonoredActivePowerComponent_Blink` receiver through `+0x174` (`FUN_00BE7580`) → `+0x1AC` (`FUN_00BFC990`) to set `EBM_BlinkMove`?

## Procedure

1. Verify the original EXE SHA-256, imported Ghidra Program executable SHA, x86 architecture and image base before analysis. Keep the current Ghidra project read-only and don't override active transactions.
2. **Prove the UsePower owner:** identify native class descriptor, constructor, vptr store, class-name evidence and exact vtable base so offset `+0x134` is not treated as universal. Identify any secondary interface base/adjustor thunks and compare inherited class variants.
3. **Recover incoming edges:** for `FUN_00C44D30`, find code/data xrefs, calls through its vtable, assignments of the UsePower context to controller/player objects, registration tables and event dispatcher call sites. Distinguish direct, virtual, computed and unresolved edges.
4. **Recover receiver identity:** at each `+0x174` dispatch in `FUN_00C44D30`, trace exact component pointer, its source and type, and conditions on flag/state/selected component. Correlate with earlier PlayerController selection state and pawn component lookup only if a code path actually joins them.
5. **Confirm Blink side:** establish Blink vtable/constructor with slot `+0x174 → FUN_00BE7580`, and within that method precise call site for slot `+0x1AC → FUN_00BFC990`; decompile guard conditions and mode write.
6. **Join movement mode with position write:** show actual conditions from mode 1 to `FUN_00BFC5D0 → FUN_00BFC160 → FUN_00BECDF0 → FUN_006539C0`. Confirm pawn-pointer provenance and whether `+0xC4/+0xC8/+0xCC` are authoritative world position rather than a cache.
7. **Test alternative paths:** preserve a separate `Blink +0x340` conditional method entry and the independent `FUN_00CF34E0 → FUN_00CF3360` chain. Do not infer that `0x011BD230`/`0x011C55A0` are known callback owners absent separate evidence.
8. **Runtime check only on a trusted clean installation:** compare before/after pawn position, ability selection, cast state, success/failure cases; do not execute unknown injected `dinput8.dll`.

## Evidence checklist

| Missing link | Required artifact |
|---|---|
| User action → UsePower dispatch | event handler / callback edge and runtime receiver |
| UsePower receiver vtable | descriptor + constructor vptr install + slot target |
| Context → Blink | pointer provenance, type proof, conditional branch |
| Blink +0x174 → +0x1AC | actual callsite, target, guard and state update |
| BlinkMove → position write | complete static edges, branch predicates and Pawn ownership |
| Runtime execution | controlled observation verifying a successful cast and coordinate update |

## Failure criteria

If a method is invoked only by a UI selection path, don't mark it as cast. If only a pointer table candidate is found, don't assign owner. If a mode setter is reachable on a branch but not executed, call it *conditional static reachability*, not verified runtime activation.

## Known limits

The full primary local `EXP-0027`, `EXP-0028`, and Ghidra xref/p-code logs were not directly accessed here. This experiment plan does not prove that `UsePower +0x134` receives user input.
