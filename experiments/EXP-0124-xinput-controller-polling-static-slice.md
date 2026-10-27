---
id: EXP-0124
title: Exact-build XInput controller polling static slice
experiment_status: done
claim_status: mixed
build: "10256413"
question: What input-related operations are directly evidenced by the exact-build XInput callsites and their internal callers?
---

# EXP-0124 — Exact-build XInput controller polling static slice

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: manually review five exact-address functions selected from EXP-0072's unknown-subsystem bucket because their bodies or direct call graph connect to imported XInput APIs; record a separate classification overlay without altering the automated triage source.
- Exclusions: no runtime reachability or physical controller behavior; no class names or original source reconstructed; no API semantics inferred beyond the exact imported names and visible argument construction.
- Inputs: build-matched `functions.csv`, `callgraph.sqlite` used in EXP-0060/0072, and decompiler responses from the read-only static Ghidra service.
- Durable outputs: [five-function overlay CSV](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0124.csv) and [overlay summary](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0124.json).

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; hash-check the configured EXE.
2. Query the existing callgraph for direct callers of `XInputGetState` (`00DA5416`) and `XInputSetState` (`00DA5410`).
3. Confirm candidate addresses and sizes against the exact-build function index; verify all five were marked `unknown` and `not_reviewed_by_this_triage` in the EXP-0072 CSV.
4. Decompile `FUN_009C3CC0`, `FUN_009C41A0`, `FUN_009C60A0`, `FUN_009C6810`, and `FUN_009C6B90` through the read-only static service; inspect only the listed bodies/call edges.
5. Keep the EXP-0072 generated artifact unchanged; write manual review rows and recompute the residual unknown/candidate counts as a distinct overlay.

## Observations

| Function | Size | Direct imported calls / reviewed body evidence |
|---|---:|---|
| `FUN_009C3CC0` | 35 | At `009C3CD8`, calls `XInputSetState(param_1, &local_8)` after setting the four-byte local state to zero. |
| `FUN_009C41A0` | 649 | Calls `XInputGetState` at `009C41C8` for indices 0 through 3. Reconciles a global `0x1F0`-byte-record array against availability; on a newly observed slot, initializes a type-3 record and calls `XInputSetState` with a zeroed four-byte local at `009C440D`. |
| `FUN_009C60A0` | 49 | When `DAT_012E2FB0` is nonzero, calls `FUN_009C4930` at `009C60BB` and then `XInputSetState` at `009C60C8`, passing a two-byte-offset region within the local parameter storage. The transform's meaning is not established here. |
| `FUN_009C6810` | 889 | Constructor-like setup initializes object fields and window state, registers a device notification, calls `FUN_009C41A0` at `009C6AB9`, activates the window, and samples `GetKeyState` for indices 0 through 255. Its exact class ownership remains unknown. |
| `FUN_009C6B90` | 4,543 | Polls records; when a record's type field is 3, calls `XInputGetState` at `009C6D15`. The body also reads `GetKeyState` and sends translated state through indirect interface calls. The exact record schema and mapping are not recovered. |

- Callgraph direct-call sites: `XInputSetState` has three callers among this slice (the first three rows); `XInputGetState` has two (`FUN_009C41A0` and `FUN_009C6B90`). `FUN_009C6810` calls `FUN_009C41A0`. `FUN_009C6810` is called at `009C7F14` and `009C7FA7` by `FUN_009C7EB0` and `FUN_009C7F40`; those callers were not decompiled in this experiment.
- All five functions appeared in EXP-0072 as address-derived labels with `subsystem_candidate=unknown` and `semantic_review_status=not_reviewed_by_this_triage`.
- The overlay preserves the original exact-build denominator: 72,437 indexed internal functions. It records five manual body reviews; under this additive overlay, 71,993 remain unassigned to a reviewed subsystem and 444 rows carry either the 439 original symbol-name candidates or one of five input-related static-role candidates. Runtime-verified count remains zero.

## Interpretation / claims

- **Observed:** four of the five reviewed function bodies directly use imported XInput functions. The bodies expose three `XInputSetState` sites and two `XInputGetState` sites; another function calls the controller-slot routine and reads keyboard state.
- **Inferred, limited:** the five functions form an input-related static slice covering controller-slot availability, state polling, submission, and window/input initialization. The inference comes from imported API names, direct call edges, and decompiler-visible operations; no runtime invocation was observed.
- **Unknown:** which higher-level class owns these functions, how the type-3 record is laid out, what `FUN_009C4930` computes, how controller fields map to user-visible actions, and whether/when the code runs in a clean game session.
- **Limit:** decompiler output is a static tool representation, not source. This review does not establish runtime reachability, input configuration, or player-control behavior.

## Links

- Automated function triage: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- Static call/data graph: [EXP-0060](EXP-0060-function-callgraph-coverage-baseline.md)
- Function review overlay: [CSV](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0124.csv), [summary](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0124.json)
- Project completion contract: [roadmap](../docs/roadmap.md)
