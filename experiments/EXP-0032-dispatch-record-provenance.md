# EXP-0032 — Provenance of UsePower dispatcher records and callback registry

**Status:** planned, read-only. Date: 2026-10-26. The primary local EXP-0029/0030/0031 are not accessible; observations are user-report-derived.

## Questions to resolve

1. Does `FUN_00C0CA70` actually dispatch an instance of `DisItemContext_UsePower` via slots `+0x184` and `+0x134`?
2. Who allocates, fills or copies the `0x30`-stride collection traversed by the dispatcher, and what object pointer does its `+0x1E0` read reference?
3. Is the generic keyed manager `FUN_00B36CA0` causally connected to UsePower, or merely a different subsystem with callbacks?
4. Which direct or indirect event invokes the path to `FUN_00BFC990` and under what circumstances does mode 1 succeed versus mode 3 fallback?

## Concrete read-only procedure

1. Verify binary SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, Ghidra program SHA, image base `0x400000`, x86 architecture.
2. At `FUN_00C0CA70`, export assembly at loop header and dispatch, registers holding each base, index scaling, record stride, effective address leading to receiver, and instruction addresses for calls through slots `+0x184/+0x134`.
3. Perform *backward dataflow* on the pointer dereferenced at `+0x1E0`; locate writes or constructors to the same object and bulk copy/memcpy/deserialize paths. Draw different symbols for array-entry base, nested-object base, and enclosing manager base.
4. For alleged producers `FUN_00C2CCD0`, `FUN_00C2CD40`, `FUN_00C2DF50`, `FUN_00C2E170`, record exact assembly effective-address expressions involving `*(this+0x60)+0x1D4` or `+0x1F0`. Reject linkage by matching offsets alone.
5. Independently identify UsePower vtable, constructor, and object creation; test whether a proven pointer to this instance can populate the dispatch receiver and whether conditional method targets actually match `FUN_00C4B800`/`FUN_00C44D30`.
6. Isolate callback registration: `FUN_00C2F750 → FUN_00C105F0` (install/remove `FUN_00C128B0` through `FUN_00B36CA0/FUN_00AEDF80`) and `FUN_00C12A80` changing 20 DWORDs from `+0x50`. Determine descriptor/event keys, record owner, actual consumer and caller types. Do not assume generic registry is an input dispatcher.
7. Record direct CALL and indirect CALLIND separately around `FUN_00CF34E0`, `FUN_00BE7580`, `FUN_00BFC990`; reconcile reported single direct caller with virtual Blink slot `+0x1AC`.
8. In Blink mode setter, annotate branch guards and compare with package numeric enum: failure path via `FUN_00BFAB80(1)` → mode 3 must not be labeled until independently supported.
9. If a safe clean installation is available, runtime observe actual Use event, receiver vptr and pawns before/after; do not run unidentified injected DLLs.

## Deliverables

- Precise record-layout diagram with pointer-chain and VA/RVA for accesses.
- Producer/consumer table: base object, write site, read site, data value, type proof, unresolved aliasing.
- Owner of `DisItemContext_UsePower +0x134` runtime receiver or explicit failure to establish it.
- Registries and callbacks classified as generic or event-specific by evidence.
- Reconciled static direct/virtual call graphs and exact mode-set success/failure predicates.

## Acceptance gates

Cannot close without showing exact pointer identity between a dispatch record and a concrete UsePower object, and eventually a verified event from user action to successful BlinkMove/position write. Maintain the source limits and retain negative findings.
