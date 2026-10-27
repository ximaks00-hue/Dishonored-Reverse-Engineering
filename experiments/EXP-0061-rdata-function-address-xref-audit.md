---
id: EXP-0061
title: Raw .rdata address audit for functions absent from direct-call edges
experiment_status: done
claim_status: observed
build: "10256413"
question: "At .rdata source sites with incoming non-call xrefs to functions absent from direct-call edges, do raw PE DWORDs match the indexed target VA or RVA?"
---

# EXP-0061 — Raw `.rdata` address audit for functions absent from direct-call edges

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: for the 3,866 internal functions absent from both direct-call source and target roles in EXP-0060, inspect `.rdata` sites of non-call data xrefs to their entries and compare raw DWORD values with the target VA/RVA.
- Exclusions: address-valued entries and consecutive pointer-like runs do not establish a vtable or any specific structure. No game launch or modification; `_excluded_coop_project/` was not accessed.
- Tools: Python 3 standard library; [rdata_function_pointer_audit.py](../tools/rdata_function_pointer_audit.py); exact-build `Dishonored.exe`; callgraph SQLite from EXP-0060.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify EXE SHA-256 and x86 PE format.
2. Build the `neither` set from the internal `functions.csv` addresses not present as direct-call source or target in the callgraph.
3. Select `data` edges whose target is in `neither` and whose `site_addr` falls within PE `.rdata`; map each site VA to a file offset using the section RVA and raw pointer.
4. Read the little-endian DWORD at each source site. Classify a match as target VA, target RVA (`target VA - image base`), or other.
5. Count contiguous source-site runs at 4-byte stride among VA-matching sites; report runs with at least 3 entries.
6. Reproduce with `python tools/rdata_function_pointer_audit.py`. The script checks the exact EXE hash and callgraph build metadata before reading bytes.

## Observations

- The EXE hash matches the build record; image base is `0x00400000`, PE32 x86.
- There are 3,866 `neither` functions and 20,309 `data` xref edges at 20,309 unique `.rdata` sites targeting them. No single `.rdata` site in this subset has multiple distinct no-call function targets.
- At 20,303 sites, the raw DWORD equals the indexed target function VA.
- At the remaining 6 sites, the raw DWORD equals the target function RVA (`target VA - 0x00400000`); the six target labels are `GetMaxPools`, `GetNumPools`, `GetPanningRule`, `GetPoolID`, `RegisterMotionDevice`, and `SetMaxNumVoicesLimit`.
- No remaining site had a raw DWORD that matched neither target VA nor target RVA.
- The VA-matching sites form 668 contiguous runs of at least three 4-byte entries. The longest run has 191 entries beginning at `0x00FDA7FC`.
- Example: source site `0x00FB9350` stores DWORD `0x00401580`, matching indexed target `FUN_00401580`.

## Interpretation / claims

- **Observed:** every audited `.rdata` xref site stores either the exact target function VA (20,303) or its image-relative RVA (6) in the raw EXE bytes.
- **Observed:** the VA-matching sites include long contiguous groups of 4-byte address-valued entries; the longest measured group has 191 entries.
- **Inferred, limited:** these entries are function-address tables or arrays worth inspecting as possible vtable/registration structures. The current measurement does not identify their owner or use.
- **Unknown:** which contiguous groups are vtables, delegates, callback registries, or other structures; whether any of the 3,866 functions is invoked indirectly at runtime.
- **Not established:** vtable ownership, virtual-call behavior, execution reachability, or function semantics.

## Reproduction and limitations

- Run `python tools/rdata_function_pointer_audit.py` from the repository root. It emits JSON with matching counts, six RVA matches, other mismatches, and contiguous run totals.
- Callgraph edge generation and role coverage are documented in [EXP-0060](EXP-0060-function-callgraph-coverage-baseline.md); exact internal function addresses are reconciled in [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md).
- The script reads the exact EXE and ignored local callgraph/index data; it writes no files.
- An address stored in `.rdata` can be referenced for reasons other than vtable dispatch. Follow-up must inspect adjacent words, table references, constructors, and callsites before assigning a structure type.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Direct call/data graph baseline: [EXP-0060](EXP-0060-function-callgraph-coverage-baseline.md)
- Function index reconciliation: [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md)
- Reproducer: [rdata_function_pointer_audit.py](../tools/rdata_function_pointer_audit.py)
