---
id: EXP-0043
title: Blink target writer and activation-entry separation
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does Blink vtable slot +0x1B0 write the same receiver target fields consumed by the +0x1AC move-mode entry?"
---

# EXP-0043 — Blink target writer and activation-entry separation

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching BUILD-STEAM-10256413.
- Ghidra project: `Dishonored-RHCP-10256413`, x86, image base `0x00400000`; read-only static MCP decompilation and the persisted callgraph index.
- Scope: verify the reported Blink vtable method `FUN_00BFA270`, its call to the field writer `FUN_00BF5520`, call-site receiver relationships, and any static join to `FUN_00BFC990` / the known activation helper chain.
- Exclusions: no game launch or modification; `_excluded_coop_project/` not accessed. This is static analysis, not proof that a gameplay event executes the route.

## Procedure

1. Checked static MCP health and the build identity; confirmed SHA-256 and project readiness.
2. Decompiled `FUN_00BFA270`, `FUN_00BF5520`, Blink constructors, and nearby functions `FUN_00CF3540`, `FUN_00CF3360`, `FUN_00CF34E0`, and `FUN_00BFC990` read-only.
3. Queried persisted direct-call and data-xref edges for `FUN_00BFA270`, `FUN_00BF5520`, and `FUN_00BFC990`.
4. Decoded raw x86 from the PE using Capstone 5.0.7, mapping virtual addresses through PE sections; inspected the call setup at `0x00BFA2D8–0x00BFA2E1` and field stores at `0x00BF5E29–0x00BF5E4C`.
5. Compared the receiver against the Blink vtable entries and the `FUN_00BFC990` reads recorded in EXP-0030.

## Observations

- Static MCP reported build `10256413`, the expected executable SHA-256, image base `0x00400000`, and a ready 72,437-row internal function index.
- The persisted callgraph has a data edge from `0x01168848` to `FUN_00BFA270`. With Blink vtable base `0x01168698`, this is slot offset `+0x1B0`.
- The callgraph has one direct code caller of `FUN_00BFA270`: `FUN_00CF3540`, call site `0x00CF3552`. The target also has the Blink vtable data reference above.
- `FUN_00BFA270` calls `FUN_00BF5520` at `0x00BFA2E1`. Raw caller instructions at `0x00BFA2D8–0x00BFA2E1` load `[ESI+0x80]`, push that value as the explicit argument, set `ECX=ESI`, then call the helper. `ESI` is the original `FUN_00BFA270` receiver. In the helper, raw instructions set `ESI=ECX`, store the explicit argument at `[ESI+0x80]`, and write computed values to `[ESI+0x60]`, `[ESI+0x64]`, `[ESI+0x68]` (`0x00BF5E29`, `0x00BF5E44`, `0x00BF5E4C`). Therefore the writes are to the same Blink receiver, while `+0x80` carries its associated object argument.
- `FUN_00BF8B40` is another direct caller of `FUN_00BF5520` (call site `0x00BF8B63`); its raw call setup likewise passes its own `this` in ECX and pushes the object at `this+0x80`. This is a reset/cleanup-shaped path in the available decompilation and confirms the helper writes the current receiver’s fields for this caller too.
- The decompiled `FUN_00CF3540` calls `FUN_00BFA270(param_2)` and then `FUN_00CF3360`; it does not call `FUN_00BFC990`. `FUN_00CF3540` also reads configuration values and updates camera/effect-like state on conditional branches.
- The callgraph lists `FUN_00CF3540` as one direct caller of `FUN_00CF3360`, alongside `FUN_00CF34E0` and `FUN_00CF34F0`. `FUN_00CF34E0` calls `FUN_00CF3360` followed by `FUN_00BFC990`; its own direct code caller remains absent from the saved callgraph (EXP-0025/0030).
- `FUN_00BFC990` remains independently identified in Blink vtable slot `+0x1AC` at data address `0x01168844`, and directly called by `FUN_00CF34E0`. No direct callgraph edge links `FUN_00BFA270` or `FUN_00BF5520` to `FUN_00BFC990`.
- `FUN_00BFC990` reads the receiver fields `+0x60/+0x64/+0x68` as its stored target (EXP-0030); its address is also at Blink vtable `0x01168698+0x1AC`. The writer call site proves `FUN_00BF5520` receives the same Blink object in ECX from the `+0x1B0` method. Thus writer and consumer address the same receiver fields at the static class/method level. The callgraph alone does not prove the runtime scheduling order or that a particular player action reaches either method.

## Interpretation / claims

- **Confirmed:** `FUN_00BFA270` occupies Blink vtable slot `+0x1B0` in the recorded table and is called directly from `FUN_00CF3540`.
- **Confirmed:** Blink vtable slot `+0x1B0` resolves to `FUN_00BFA270`; raw call setup proves it calls `FUN_00BF5520` with the same Blink receiver in ECX.
- **Confirmed:** `FUN_00BF5520` writes candidate XYZ to that receiver’s `+0x60/+0x64/+0x68`, and `FUN_00BFC990` reads those exact fields from a Blink receiver at slot `+0x1AC` (EXP-0030). The static same-instance field bridge is established.
- **Confirmed negative for the direct-call join:** `FUN_00CF3540` calls `FUN_00BFA270` and then `FUN_00CF3360`, but does not call `FUN_00BFC990`; the separate `FUN_00CF34E0` path calls both `FUN_00CF3360` and `FUN_00BFC990`.
- **Unknown:** whether and when the `FUN_00CF3540` update route runs in response to player input; who enters `FUN_00CF34E0`; and how either route is scheduled relative to `DisItemContext_UsePower` / Blink `+0x340`.
- **Conclusion:** Blink’s `+0x1B0` update method computes and stores the target on the same Blink instance whose `+0x1AC` method consumes it for the conditional move-mode transition. This closes the stored-target writer/consumer join, but does not close E7 or establish a complete user-input-to-movement path.

## Reproduction and limitations

- Use `dishonored_static.health` to confirm indexed build/hash, then decompile the listed functions read-only. For calling-convention proof, map VA→RVA→raw PE offset and inspect the listed raw x86 instructions; do not infer ECX from decompiler call syntax.
- Inspect `knowledge/database/callgraph.sqlite` edges for the listed targets, or regenerate from `ExportCallGraph.java` if the index is missing/stale.
- Pseudocode is Ghidra's analysis rendering, not original source. Callgraph absence only covers the exported direct-call graph; virtual/callback dispatch may add paths not represented by direct edges.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0024, EXP-0025, EXP-0028, EXP-0030, EXP-0039, EXP-0042.
- Open graph: [Blink activation graph](../docs/gameplay/blink/activation-graph.md)
