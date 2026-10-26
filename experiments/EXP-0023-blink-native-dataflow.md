# EXP-0023 — Blink native dataflow / movement proof
Date: 2026-10-26. **Status: planned, not executed**. Scope: Windows x86 EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; image base `0x00400000`. Hash must be independently rechecked. Local EXP-0019–EXP-0022 and raw Ghidra output are not available in this GitHub branch.

## Research question
Are reported Blink-specific candidates `FUN_00BFC5D0`, `FUN_00BFC160`, `FUN_00BFBC90`, `FUN_00BF9AB0` calculating targets, validating positions, applying movement, or generating previews? Earlier report observes coordinates/distances/timers and a `0x38` record stride **across the family**, but no direct pawn-position store in the inspected bodies. Do not assign a specific behavior to one function without its disassembly.

## Prerequisites
1. Verify exact local EXE SHA, architecture, base and current Ghidra source identity; do not force-save a locked project.
2. Recover Blink and base component constructor vptr stores and table addresses; diff slot-by-slot. Inheritance and thunks matter.
3. Keep all generated output in local ignored paths, no game assets or unrelated co-op artifacts in Git.

## Procedure (read-only)
1. Execute `Exp0023BlinkDataflowExport.java` to export incoming references, p-code CALL/CALLIND, STORE, LOAD, PTRADD, POINTER arithmetic, and RETURNS for the four Blink methods, plus `0x00AB4680`, `0x00BCD800`, `0x00414DC0`. This is evidence export, not automatic semantic classification.
2. For each Blink method separately, identify receiver, arguments, side effects, return values, direct and virtual callers/callees and any exact parameter loads. Capture high-level and disassembly context.
3. For `0x38` structures, discover base, allocator/owner, count/capacity, index computation, member reads/writes and consumers. Compare alternative record interpretations before naming them as vectors or trajectories.
4. Trace `m_pPowerAttributes` and the instance `Twk_Powers.Blink.Twk_Blink` towards native loads. Distinguish class defaults from instance values; reflected property name alone cannot determine native field offset.
5. Follow the returned/modified data to the function that **actually modifies the pawn/world position**. A p-code STORE somewhere, or an indirect CALLIND, is not proof of player movement. Verify target pointer provenance and an independently reproducible game state transition.
6. Separate UI wheel-selection `24→2 → UpdateItemInfos`, controller index selection, Blink cast initiation, target checks, and final relocation. Establish actual directed edges.

## Gates
- **A: identity** — verified Blink constructor/vtable and four method slot positions.
- **B: data model** — `0x38` record layout and attribute consumers supported by concrete code.
- **C: movement** — specific player-position change with call path, input/output, build RVA and independent verification. Until C, movement is NOT reconstructed.

## Follow-up EXP-0024 (separate)
Map the controller's `_iPower` through pawn array pointer/count at `+0xA40/+0xA44`, downstream Pawn slots `+0x6E8/+0x6E4`, active power storage `+0x788/+0x78C` and shortcut byte `+0x228`. Do not equate wheel item 24, UI code 2, active array index 0, shortcut autoassign 1/5 or `_iPower` without dataflow. **Pawn field** `+0x788` is NOT the same concept as **vtable displacement** `+0x788` from an earlier native-exec wrapper.

## Evidence and limitations
Preserve unknowns and failed decompilation, distinguish report observations from independently reproduced results, and do not publish game binary/content. The original report states no direct position write found in examined bodies only; this is a scoped negative result.
