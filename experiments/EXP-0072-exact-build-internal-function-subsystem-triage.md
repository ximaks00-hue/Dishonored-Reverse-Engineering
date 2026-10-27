---
id: EXP-0072
title: Exact-build internal function label and graph triage
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can all 72,437 exact-build internal function addresses be reconciled into explicit label/subsystem-candidate and unknown buckets with reproducible callgraph and data-xref context?"
---

# EXP-0072 — Exact-build internal function label and graph triage

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: assign exactly one conservative label-family and subsystem-candidate/unknown bucket to each row in the reconciled 72,437-entry internal Ghidra function index; add direct-call role, indexed size bucket, and incoming non-call data-xref counts/source-section context from the build-matched graph.
- Exclusions: no full semantic review or body-by-body decompilation; no inferred runtime reachability; no claim that a symbol label proves implementation ownership; no game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: Python 3 standard library, exact-build [function index](../research/executable/functions.csv), build-matched `knowledge/database/callgraph.sqlite`, PE section parser in [callgraph_coverage.py](../tools/callgraph_coverage.py), and [function_subsystem_triage.py](../tools/function_subsystem_triage.py).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the EXE SHA-256 from disk.
2. Require the index addresses to be unique eight-digit VAs and reconcile 72,437 rows to 72,437 unique addresses.
3. Check the callgraph `build_id` and executable hash against the build record. Stream call/data edges, build direct-call source/target roles, and count data-xref targets by source PE section using the exact-build section table.
4. Apply exact, documented label-pattern/name buckets: address-derived `FUN_` and `thunk_FUN_`; `Unwind@address`; address-qualified `Catch`/`Catch_All`; exact observed Wwise-like API names; exact Winsock, Direct3D, DirectInput/XInput, and PhysX delay-load names; CRT/C++ runtime label patterns; generic lifecycle/destructor names; FID-conflict labels; and an explicit remaining `named_symbol_owner_unknown` family. Subsystem candidates derived only from label names remain candidates; every other row is assigned `unknown`.
5. Record one output row per indexed function with its address, index label/signature/size, label family, candidate/unknown bucket, direct-call role, incoming data-xref count/section counts, and an explicit `not_reviewed_by_this_triage` marker.
6. Save the full per-address CSV and aggregate JSON under [function-triage](../research/executable/evidence/function-triage/). The script writes no Ghidra database changes.

Reproduce from the repository root in PowerShell:

```powershell
python tools\function_subsystem_triage.py
```

## Observations

- The current exact-build internal index has 72,437 rows and 72,437 unique addresses. The function triage CSV has exactly 72,437 rows and unique addresses.
- The callgraph metadata matches build 10256413 and the recorded EXE SHA-256. The pass read 217,768 direct-call edges and 299,821 non-call data-reference edges. Direct-call role counts match EXP-0060: 29,167 caller-and-target, 34,719 caller-only, 4,685 target-only, and 3,866 in neither direct-call role. There are 36,347 functions targeted by at least one recorded data edge, also matching EXP-0060.
- Name-derived label-family counts are: 56,618 address-derived `FUN_` labels; 15,177 `Unwind@address` labels; 107 address-derived `thunk_FUN_` labels; 181 exact names in the script's Wwise-like API list; 112 constructor/destructor-like labels; 91 CRT/C++ runtime-name labels; 41 other named labels without owner; 35 generic lifecycle names; 24 Winsock API names; 20 FID-conflict labels; 17 address-qualified Catch/Catch_All labels; 6 PhysX delay-load labels; 5 Direct3D API names; and 3 DirectInput/XInput API names. Family totals sum to 72,437.
- The explicit unknown subsystem bucket contains 71,998 functions. The remaining 439 rows carry one of the classifier's subsystem-name candidates: audio-middleware API names 181; object-lifecycle-like names 112; CRT/runtime names 91; network API names 24; catch/exception-handler-like names 17; physics delay-load names 6; graphics API names 5; and input API names 3.
- All 72,437 rows state `not_reviewed_by_this_triage`. The output also preserves indexed function sizes and per-target data-xref source-section counts for follow-up ranking.

## Interpretation and claim limits

- **Confirmed for the exact-build index and current static graph export:** all 72,437 indexed addresses are represented exactly once in the triage CSV; the build/hash identity matches the record; direct-call role and data-xref denominators reproduce EXP-0060.
- **Observed:** label families and call/data graph roles yield reproducible candidate buckets and an explicit unknown bucket. `Unwind@address`, FID conflict, catch-like, API-like and lifecycle-like labels are retained as labels, not treated as confirmed code semantics.
- **Inferred candidate only:** exact Wwise-like, graphics, input, Winsock and PhysX names suggest API/library domains for triage. They do not establish that the indexed body implements that API, which module owns it, or whether the function is used at runtime.
- **Unknown:** semantic subsystem assignment for the 71,998 unknown-bucket rows; complete ownership for the 439 name candidates; indirect-call/vtable ownership; body review status across the corpus; runtime reachability.
- **Limit:** this is a full-denominator triage artifact, not a claim that all functions have been reversed. Address-derived names and graph roles are not semantic evidence. A bucket should be upgraded only with function-body, xref, vtable-owner, package/native, or other traceable evidence.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Function-index provenance/name baseline: [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md), [EXP-0059](EXP-0059-function-index-name-and-size-baseline.md)
- Callgraph denominator and role baseline: [EXP-0060](EXP-0060-function-callgraph-coverage-baseline.md)
- Raw data-xref pointer audit: [EXP-0061](EXP-0061-rdata-function-address-xref-audit.md)
- Triage bundle: [function-triage](../research/executable/evidence/function-triage/README.md)
- Reproducer: [function_subsystem_triage.py](../tools/function_subsystem_triage.py)
