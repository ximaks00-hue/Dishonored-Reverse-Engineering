---
id: EXP-0125
title: Windows input initialization and keyboard path static expansion
experiment_status: done
claim_status: mixed
build: "10256413"
question: How do the DirectInput, window-message, keyboard-hook, and key-state helpers connect to the XInput polling slice from EXP-0124?
---

# EXP-0125 — Windows input initialization and keyboard path static expansion

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: manually review eight exact-address functions around the EXP-0124 XInput slice, selected by direct input/window API calls and callgraph links; extend the manual overlay without changing the automated EXP-0072 triage.
- Exclusions: no runtime reachability, input-device behavior, or user-visible action claim; no original class/source recovery; no interpretation of undocumented object fields or Windows message constants beyond their recorded numeric values.
- Inputs: exact-build `functions.csv`, `callgraph.sqlite` from EXP-0060/0072, and read-only decompiler outputs for the listed function addresses.
- Durable outputs: [eight new function rows](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0125.csv), [cumulative 13-row overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0125.csv), and [cumulative overlay summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0125.json).

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; verify the executable SHA-256.
2. Query call/data graph edges around `009C30A0`–`009C9D50`, including the XInput import callers from EXP-0124.
3. Confirm all eight selected functions were unknown-subsystem, address-derived, and not reviewed in the automated EXP-0072 table.
4. Decompile `FUN_009C30A0`, `FUN_009C3F00`, `FUN_009C48A0`, `FUN_009C7D70`, `FUN_009C7FE0`, `FUN_009C8210`, `FUN_009C9B30`, and `FUN_009C9D50` through the read-only static service.
5. Record direct API callsites, function-pointer/data-reference joins, and body observations. Add eight rows to the manual overlay; retain the original automated output.

## Observations

| Function | Size | Body and direct static links |
|---|---:|---|
| `FUN_009C9D50` | 1,321 | Calls `CreateThread` at `009CA1C7` with start-routine pointer `FUN_009C3F00` at `009CA1C0`; calls `DirectInput8Create` at `009CA1E9`; calls controller-slot routine `FUN_009C41A0` at `009CA260`. It registers `FUN_009C9B30` as `WNDCLASSEXW.lpfnWndProc` and calls `RegisterClassExW` at `009C9E93`. The body also reads/writes `WinDrv.Accessibility` configuration keys and calls `SystemParametersInfoW` three times.
| `FUN_009C3F00` | 188 | Runs a `GetMessageW` loop. For private message `wParam==1`, it installs a hook with `SetWindowsHookExW` and passes callback `FUN_009C30A0` (data reference at `009C3F55`); for `wParam==2`, it unhooks. It also unhooks on loop exit.
| `FUN_009C30A0` | 180 | Calls `CallNextHookEx` on the ordinary path. For `param_2` values `0x100` or `0x101` and `*param_3` values `0x5B` or `0x5C`, the body evaluates a global/player-state predicate and can return `1`; otherwise it forwards through `CallNextHookEx`. No message or key names are assigned here.
| `FUN_009C9B30` | 245 | Searches a global window/object array for the incoming `HWND`; when a match exists and `DAT_01412980==0`, it calls `FUN_009C8210` at `009C9C02`. Otherwise it calls `DefWindowProcW` at `009C9C18`. A data xref from `FUN_009C9D50` supplies this callback to the registered window class.
| `FUN_009C8210` | 1,342 | Handles message-code branches; calls `FUN_009C7FE0` at `009C823A` when a field flag is set and calls `FUN_009C48A0` at five sites (`009C82D5`, `009C8336`, `009C8561`, `009C86AE`, `009C8710`). Some paths fall through to `DefWindowProcW` at `009C8278`.
| `FUN_009C7FE0` | 138 | If `DAT_0145BDB8` is set, writes a flag and returns. Otherwise calls `FUN_009C7D70` for virtual-key values `0xA2`, `0xA3`, `0xA0`, `0xA1`, `0xA4`, and `0xA5`, then updates fields in the caller object.
| `FUN_009C7D70` | 152 | Calls `GetKeyState` at `009C7DB7`, compares the high bit with a saved per-key state, updates that state, and on a change invokes an indirect interface method with the transition value.
| `FUN_009C48A0` | 143 | Calls `GetKeyState` at five sites for arguments `0xA2`, `0xA3`, `0xA0`, `0xA1`, and `0x12`; copies those values plus four received parameters into a record obtained through `FUN_0050EC30`.

- Callgraph and body links now connect the EXP-0124 controller path to initialization and keyboard paths: `FUN_009C9D50` starts the thread and calls `FUN_009C41A0`; `FUN_009C3F00` passes `FUN_009C30A0` to the hook API; the window callback `FUN_009C9B30` routes to `FUN_009C8210`; and `FUN_009C8210` routes selected messages to the key-state helpers.
- All eight addresses were present in EXP-0072 as `subsystem_candidate=unknown`, with address-derived labels and `not_reviewed_by_this_triage` status.
- Cumulative manual review now covers 13/72,437 indexed internal functions: the five in EXP-0124 and these eight. The additive overlay has 71,985 unresolved unknown-subsystem rows and 452 candidate rows (439 original symbol-name candidates plus 13 input-related static-role candidates). No runtime-verified function count changes.

## Interpretation / claims

- **Observed:** these bodies connect a DirectInput initialization call, a message-processing thread with hook install/removal, a callback, window-message dispatch, `GetKeyState` polling, and the XInput paths recorded in EXP-0124.
- **Inferred, limited:** the selected functions belong to a shared Windows input/window handling slice. The inference follows explicit function-pointer, call, and API edges; it does not show the execution schedule or prove every routine's class ownership.
- **Unknown:** the exact input record schemas, the semantics of indirect interface methods and globals, the complete DirectInput device configuration, why the callback filters the two numeric values, and how any raw input maps to gameplay actions.
- **Limit:** decompiler pseudocode is not original source. No matching game process was observed, so all runtime behavior and reachability remain unverified.

## Links

- Initial XInput slice: [EXP-0124](EXP-0124-xinput-controller-polling-static-slice.md)
- Automated function baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- Static callgraph baseline: [EXP-0060](EXP-0060-function-callgraph-coverage-baseline.md)
- Function review overlay: [new rows](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0125.csv), [cumulative CSV](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0125.csv), [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0125.json)
- Project completion contract: [roadmap](../docs/roadmap.md)
