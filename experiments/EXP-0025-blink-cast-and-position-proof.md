# EXP-0025 — Blink cast trigger and authoritative position-write verification

Status: **planned**, not executed. Target: previously reported x86 EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`. Use only verified Ghidra program corresponding to exact executable. Preserve read-only state.

## Phase 1: establish method and caller identity

- `FUN_00BFC990`: export xrefs, containing Blink vtable slot, callers and any mode-value writes. Resolve mode `1` against the package `EBM_BlinkMove` enum, but do not infer that the method receives input events without a real caller.
- `FUN_00BFC5D0 → FUN_00BFC160 → FUN_00BECDF0 → FUN_006539C0`: export actual CALL/CALLIND sites, arguments, state guards and branches. Classify each edge as direct, inferred, or unknown.
- Determine whether the component and owner pointer survive all transitions, especially any hidden `this`, interface adjustments, or cast.

## Phase 2: field and argument provenance

- For `FUN_006539C0`, identify the precise base pointer leading to `Pawn+0xC4,+0xC8,+0xCC`. Trace where the written vector originates and whether fields are authoritative `Location`, an intermediate/cached transform or replicated state.
- Inspect references to these three offsets from known Actor/Pawn position update or getters; verify exact memory base and ordering.
- Track trace result through `FUN_00BECDF0` and compare success, failure, collision, and invalid-target control paths.

## Phase 3: attributes and record layout

- Establish interface/vptr at Blink `this+0x54`, slot `+0x10` and `FUN_00A446B0` reading pointer `this+0x8C`; level index `+0x88`. Confirm `m_CurrentLevel` and `m_pPowerTweaks` via independent property layout source, not just ordering in UPK declarations.
- Resolve `FUN_00BF9AB0` normal getter result and fallback `DAT_0146F26C → DisTweaks_DarkVision`, identifying their actual resulting classes; keep DarkVision fallback distinct from Blink attribute object.
- Reconstruct `0x38` native array element layout including base/count/stride, element offsets and read consumers. Compare with serialized `PowerAttributes_Blink = 0x4C`; document any conversions rather than equating.

## Phase 4: join player input to cast

- Identify invocation chain from keyboard/gamepad Use and PlayerController active-power state to Blink cast initiation, not just Scaleform UI highlight.
- Find event invoking `FUN_00BFC990` and show that resulting mode 1 reaches the movement pipeline under plausible game-state constraints.
- If safe clean installation becomes available, design controlled runtime validation recording before/after Pawn position. No execution of unknown injected DLL.

## Required evidence ledger

| Link | Required observation |
|---|---|
| input → cast | exact function/callback edge |
| cast → mode 1 | caller, conditions, state write |
| mode 1 → path | call chain and branch conditions |
| trace result → vector | pointer provenance / struct offsets |
| vector → Pawn position | low-level writes and authoritative field meaning |
| settings → calculations | verified owner and record layout |

Do not close EXP-0025 until every above edge has evidence with source build, RVA and disassembly or runtime observation. This protocol follows user narrative; original local EXP-0023/0024 source logs are not presently available in connected GitHub.
