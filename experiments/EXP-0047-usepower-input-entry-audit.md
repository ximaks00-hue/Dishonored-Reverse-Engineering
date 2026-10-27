---
id: EXP-0047
title: "Audit candidate callers of the UsePower context entry"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the exact-build static call/data graph identify a user-input caller for DisItemContext_UsePower slot +0x134, and is the neighboring Swarm path a valid join?"
---

# EXP-0047 — Audit candidate callers of the UsePower context entry

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching BUILD-STEAM-10256413.
- Ghidra/index: x86, image base `0x00400000`; read-only static MCP and persisted exact-build callgraph.
- Scope: inspect references to UsePower native entry `FUN_00C44D30`, then distinguish the nearby `FUN_00C44E30` Swarm path from Blink activation.
- Exclusions: no game launch or modification; `_excluded_coop_project/` not accessed. This is a static caller audit and does not observe an input event.

## Procedure

1. Rechecked project status, Blink activation graph, build record, and session checklist. Static MCP health reports the expected build ID and executable SHA-256.
2. Queried all persisted incoming `call` and `data` edges for `FUN_00C44D30`, `FUN_00C44E30`, and `FUN_00BFC5D0`.
3. Read-only decompiled `FUN_00C44D30`, `FUN_00C44E30`, `FUN_00A96B50`, and the UsePower constructor `FUN_00C43700`; compared with EXP-0028 and EXP-0042.
4. Kept direct-code xrefs separate from vtable data references and from inferred dynamic calls.

## Observations

- `FUN_00C44D30` has no direct code-call xrefs in the persisted callgraph. Its recorded incoming data reference is at `0x01183754`, the `+0x134` entry of the UsePower primary vtable installed by `FUN_00C43700` (class/vtable association established in EXP-0028).
- `FUN_00C44D30` receives one explicit 4-byte argument, performs context/component state checks, and conditionally calls component virtual slot `+0x174` (EXP-0028). The static function body does not expose the upstream input event.
- `FUN_00C44E30` has one direct code caller in the saved graph: `FUN_00A96B50` at `0x00A96BB3`. Its body obtains a component-like pointer through nested fields and interface calls, checks several results, then calls `FUN_00C44E30`.
- `FUN_00C44E30` obtains a component at `param_1+0x3C`, passes its nested `+0x114` object to `FUN_00C43410`, and calls `FUN_00BFAFD0` only when that helper succeeds. EXP-0042 resolves the helper/global descriptor to `DishonoredActivePowerComponent_DevouringSwarm`; the downstream receiver is therefore the Swarm component, not an established Blink receiver.
- These references establish a separate conditional Swarm route. They do not show that `FUN_00A96B50` is a keyboard/gamepad event, do not connect it to `FUN_00C44D30`, and do not identify the dynamic caller of the UsePower vtable entry.
- `FUN_00BFC5D0` remains referenced by Blink and Transversal vtable entries at `0x011687D4` and `0x011BD1E4`, with no ordinary direct code-call edge in the persisted index (EXP-0046).

## Interpretation / claims

- **Confirmed:** `FUN_00C44D30` is present at UsePower vtable `+0x134`; no direct code-call edge to it appears in the persisted exact-build callgraph.
- **Confirmed:** `FUN_00A96B50` directly calls `FUN_00C44E30`, whose guarded path requires the DevouringSwarm class check before entering the Swarm component writer chain (EXP-0042).
- **Unknown:** which user input, animation event, or generic context scheduler invokes UsePower vtable `+0x134`; whether it is reached for Blink during gameplay; whether `FUN_00A96B50` itself is driven by user input.
- **Rejected for this join:** `FUN_00A96B50 → FUN_00C44E30 → FUN_00BFAFD0` is not evidence of Blink activation; the target component class is DevouringSwarm. This does not reject other possible callers or paths into Blink.
- **Conclusion:** the direct-call audit did not close E7. It separates a concrete Swarm-specific branch from the still-unidentified dynamic UsePower/Blink entry.

## Reproduction and limitations

- Confirm `dishonored_static.health` reports build `10256413` and the recorded EXE SHA-256.
- Query `knowledge/database/callgraph.sqlite` for incoming edges to `00C44D30` and `00C44E30`; inspect vtable data edge `01183754`.
- Decompile the listed functions read-only and verify the class check against EXP-0042's descriptor resolution.
- The callgraph's lack of a direct caller does not exclude vtable, callback, or computed dispatch. The association of `FUN_00A96B50` with an input action is not established.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0028, EXP-0032, EXP-0042, EXP-0045, EXP-0046.
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
