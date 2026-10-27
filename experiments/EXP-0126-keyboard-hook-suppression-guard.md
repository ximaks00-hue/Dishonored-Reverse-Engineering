---
id: EXP-0126
title: Keyboard-hook suppression guard and unresolved indirect helper
experiment_status: done
claim_status: mixed
build: "10256413"
question: What exact static conditions control the keyboard-hook callback's conditional early return, and can the indirect helper's role be identified from its callers?
---

# EXP-0126 — Keyboard-hook suppression guard and unresolved indirect helper

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: inspect the decompiler bodies of `FUN_009C30A0`, `FUN_006A6580`, and its second known caller `FUN_005CB4D0`; cross-reference earlier reviewed writers/readers of the callback's two globals.
- Exclusions: no naming of the globals or indirect target without evidence; no interpretation of numeric window/hook messages as Win32 constants; no runtime, input-suppression, or player-action claim.
- Inputs: exact-build function index, callgraph database, EXP-0124/0125 function records, and read-only decompiler outputs.
- Durable outputs: [two newly reviewed but unassigned functions](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0126.csv), [cumulative 15-row overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0126.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0126.json).

## Procedure

1. Read repository instructions, status, Blink graph, and build record; verify the EXE hash.
2. Review `FUN_009C30A0` and identify all conditions that precede its `return 1` path.
3. Decompile `FUN_006A6580`; inspect its direct callsites and separately decompile `FUN_005CB4D0` to characterize the second caller's local operations.
4. Cross-reference the previously reviewed `FUN_009C8210`, `FUN_009C6810`, and `FUN_009C9D50` observations for the written/read global flags; do not infer symbol names.
5. Add both examined addresses to the manual review overlay as reviewed but still subsystem-unassigned; preserve automated EXP-0072 outputs.

## Observations

- `FUN_009C30A0` first forwards to `CallNextHookEx` when its first argument is nonzero. Its conditional early-return branch is considered only when that argument is zero, the second argument is exactly `0x100` or `0x101`, and the integer at the third-argument pointer is `0x5B` or `0x5C`.
- For those values, the callback sets a local boolean false if `DAT_0144721C` is null, the dword at `DAT_0144721C+0x48C` is null, or the dword at offset `+0x40` of that pointed-to object is null. If those pointers are non-null, it calls `FUN_006A6580`; a zero result leaves the local boolean false, a nonzero result sets it true.
- The callback returns `1` only when that local boolean is true, `DAT_0141B21C` is nonzero, and `DAT_0145BDD8` is nonzero. All other paths call `CallNextHookEx`.
- In `FUN_009C8210`, the branch for numeric message value `0x1C` writes `DAT_0145BDD8 = (param_3 == 1)`. This establishes a writer/reader relation for that global but does not identify the message or flag's intended meaning.
- In `FUN_009C6810`, a branch gated by `DAT_0141B21C != 0` and `DAT_0141295C == 0` reads `GameFramework.MobilePlayerInput.bFakeMobileTouches` and, if still false, checks `-simmobile`. `FUN_009C9D50` also branches on `DAT_0141B21C` when registering its window class. These are observed neighboring uses; the global's exact meaning remains unnamed.
- `FUN_006A6580` is 10 bytes in the exact-build index. Its decompiler output is a single indirect call through an object at `param_1+0x40`, using vtable offset `+0x58`; no target method or concrete object type is resolved. The decompiler gives this wrapper a `void` return, while both callers consume its result, so its recovered return type is not trusted.
- The second known caller, `FUN_005CB4D0` (53 bytes), advances a pointer field, conditionally handles a character equal to `'A'`, then calls `FUN_006A6580` and stores the returned value through an output pointer. This separate call path does not identify the indirect method's semantics or prove the helper is input-specific.
- Both `FUN_006A6580` and `FUN_005CB4D0` were in EXP-0072's unknown-subsystem bucket. The overlay now records 15 body-reviewed functions total; 13 carry input-related static-role candidates and these two remain reviewed but unassigned. The unresolved unknown-subsystem count stays 71,985, candidate count stays 452, and runtime-verified count stays zero.

## Interpretation / claims

- **Observed:** the hook callback's conditional early return requires the exact numeric arguments and pointer/global predicates above. The two global flags have readers/writers in the earlier reviewed window/input functions.
- **Inferred, limited:** the `DAT_0141B21C` branch is associated with a mobile/fake-touch code path because the same flag gates code that reads those configuration names. This does not prove that the flag itself means “mobile mode” or that the hook is suppressing a particular user-visible key.
- **Unknown:** the identity of the indirect `+0x58` method, the object's owner and field semantics, the intended meaning of `0x100/0x101`, `0x5B/0x5C`, and `0x1C`, and whether the callback runs or returns `1` at runtime.
- **Limit:** static decompilation and cross-references establish code conditions, not execution. The `FUN_006A6580` return type is specifically unresolved by the decompiler.

## Links

- Input/window path: [EXP-0125](EXP-0125-windows-input-path-static-expansion.md)
- XInput caller slice: [EXP-0124](EXP-0124-xinput-controller-polling-static-slice.md)
- Automated triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- Overlay outputs: [new rows](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0126.csv), [cumulative rows](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0126.csv), [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0126.json)
- Project completion contract: [roadmap](../docs/roadmap.md)
