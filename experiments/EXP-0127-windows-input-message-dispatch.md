---
id: EXP-0127
title: Windows input message dispatcher and input-object wrappers
experiment_status: done
claim_status: mixed
build: "10256413"
question: Which Windows message families does the large input-window dispatcher route, and how do nearby entry wrappers reach the previously reviewed input initializer?
---

# EXP-0127 — Windows input message dispatcher and input-object wrappers

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: Which Windows message families does the large input-window dispatcher route, and how do nearby entry wrappers reach the previously reviewed input initializer?
- Scope and exclusions: Static decompiler and indexed callgraph review of `FUN_009C8970`, `FUN_009C7EB0`, and `FUN_009C7F40`; no runtime reachability, native type recovery, or behavior claims beyond visible branches.
- Prerequisites / starting state: Build identity checked against `research/builds/BUILD-STEAM-10256413/build.md`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Tools and versions: Read-only static MCP decompiler using `analyzeHeadless -noanalysis -readOnly`; persisted exact-build function index and callgraph.

## Procedure

1. Resolve the three addresses in the persisted function index and verify indexed body ranges.
2. Decompile each function and compare direct calls against the input slice reviewed in EXP-0124/0125.
3. Record exact numeric message branches and direct internal call relationships; leave opaque interface methods unnamed.

## Observations

- `FUN_009C8970` is indexed at `009C8970` with size 4047 bytes and decompiles as a two-argument `__thiscall` message dispatcher. Its second argument is read at offsets `+4`, `+8`, and `+0xC`; the source-level type is not recovered.
- Visible branches include numeric messages `0x100/0x104`, `0x101/0x105`, and `0x102/0x106`; these paths read key/message fields, adjust modifier-key virtual-key values, access an input-like interface at `param_1 + 8`, and call `FUN_009C64B0` or `FUN_009C3AC0`.
- Numeric `0x200` enters a pointer/mouse-move path; `0x201/204/207/20B`, `0x202/205/208/20C`, and `0x203/206/209/20D` enter separate mouse-button/down, up, and double-click-like paths. These labels describe numeric branch grouping only.
- Numeric `0x7` and `0x8` execute paired focus-like lifecycle paths; the `0x7` branch calls `FUN_009C7FE0`. Numeric `0x21` also calls `FUN_009C7FE0` and performs an indirect method call.
- Numeric `0x219` calls `FUN_009C41A0`, the XInput slot reconciliation function reviewed in EXP-0124. This establishes a static call edge from the message dispatcher to that function, not runtime delivery or semantic identity for the message.
- `FUN_009C7EB0` (143 bytes) checks `FUN_00404280(0x4FC, 8, ...)`; on nonzero result it forwards seven received values plus `0, -1, -1` to `FUN_009C6810` and returns its result; otherwise returns zero.
- `FUN_009C7F40` (153 bytes) performs the same allocation guard, then forwards a modified argument list to `FUN_009C6810`, including `&DAT_010C1428`, two zeroes, and the final three received values. If the initializer returns nonzero, this wrapper returns that value plus four; otherwise zero.
- The decompiler leaves signatures and object types unresolved. The two wrappers are statically linked to the input initializer reviewed in EXP-0124, but their higher-level caller/ownership roles are not established here.

## Interpretation

- **Observed:** `FUN_009C8970` routes multiple Windows-style keyboard, mouse, focus/lifecycle, and device-related numeric message branches and directly invokes previously reviewed input functions.
- **Observed:** `FUN_009C7EB0` and `FUN_009C7F40` are allocation-guarded forwarding wrappers to `FUN_009C6810` with different argument construction and return handling.
- **Inferred:** The three functions are input-related static-role candidates because the dispatcher handles input-like message fields and the wrappers call the reviewed initializer. This is a subsystem association based on static code only.
- **Unknown:** Runtime registration/reachability of `FUN_009C8970`, exact message struct and interface types, semantic meaning of the `0x219` message in this program, and wrapper owners/callers.
- Confidence: High for shown call edges and literal branch values; medium for broad input-related role; no runtime claim.
- Alternative explanations: Numeric cases and opaque vtable slots may combine windowing, focus, cursor, or platform lifecycle responsibilities beyond input dispatch.
- Evidence that would falsify this interpretation: A corrected build-specific decompile or xref showing the three addresses belong to unrelated functions, or evidence that the shared `FUN_009C6810` edge is an artifact of incorrect function boundaries.

## Reproduction

- Reset/cleanup steps: None; read-only indexed analysis.
- Repeat count and variation: One decompile per address; no runtime variation.
- Known sources of variance: Decompiler pseudocode and inferred parameter types may change with analysis database/version; numeric constants and direct addresses are the retained evidence.

## Links

- Build: `research/builds/BUILD-STEAM-10256413/build.md`
- Files/functions/objects: `FUN_009C8970`, `FUN_009C7EB0`, `FUN_009C7F40`, `FUN_009C6810`, `FUN_009C7FE0`, `FUN_009C41A0`
- Related experiments: EXP-0124, EXP-0125, EXP-0126
- Open questions: Window-procedure registration/callers and wrapper ownership; runtime message reachability.
