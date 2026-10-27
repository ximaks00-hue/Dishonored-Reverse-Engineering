---
id: EXP-0060
title: Exact-build direct-call and data-xref coverage over the internal function index
experiment_status: done
claim_status: observed
build: "10256413"
question: "How many exact-build internal functions appear as direct-call sources/targets or incoming non-call data-xref targets in the offline Ghidra callgraph export?"
---

# EXP-0060 — Exact-build direct-call and data-xref coverage over the internal function index

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: compare the reconciled 72,437-entry internal function CSV with the exact-build offline Ghidra call/data-reference export and its SQLite mirror.
- Exclusions: call/data references do not establish runtime execution, reachability, complete indirect-call coverage, or semantic review. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: Ghidra script [ExportCallGraph.java](../research/executable/scripts/ExportCallGraph.java) (`-noanalysis -readOnly`); `tools/import_callgraph_csv.py`; [callgraph_coverage.py](../tools/callgraph_coverage.py); SQLite.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256 and parse its PE image base/section ranges.
2. Verify `knowledge/database/callgraph.sqlite` metadata fields `build_id` and `exe_sha256` against the build record.
3. Compare the edge counts in the SQLite mirror with the recorded source CSV `.tmp/EXP-0037-callgraph.csv`; require exact total and per-kind row-count agreement.
4. Compare each edge endpoint to the address set in `research/executable/functions.csv`; calculate distinct internal-function sources, targets, union, and no-edge denominator separately for `call` and `data` kinds. Partition internal call graph nodes into both, caller-only, target-only, and neither; measure the index name-pattern and size fields for each group.
5. Reproduce with `python tools/callgraph_coverage.py`.

## Observations

- The function index contains 72,437 unique internal addresses (EXP-0041).
- Callgraph SQLite metadata: build ID `10256413`; EXE SHA-256 matches the build record; exported at `2026-10-26T19:34:50Z`.
- The source CSV exists and matches the SQLite mirror exactly: 517,589 rows total, 217,768 `call` edges, and 299,821 `data` edges.

| Direct `call` edge measure | Value |
|---|---:|
| Call edges | 217,768 |
| Distinct indexed internal functions as caller/source | 63,886 / 72,437 |
| Distinct indexed internal functions as target | 33,852 / 72,437 |
| Distinct indexed internal functions in either role | 68,571 / 72,437 |
| Indexed internal functions absent from both roles | 3,866 / 72,437 |
| Internal-to-internal call edges | 213,507 |
| Internal-to-non-index call edges | 4,261 |
| Non-index-to-internal call edges | 0 |

- The 4,261 non-index targets are outside the internal `functions.csv` address set; this count alone does not classify each as external, indirect, or otherwise unresolved.

| Direct-call role partition | Functions | `FUN_<address>` | `thunk_FUN_<address>` | Other labels | Median indexed size | Also target of data xref | No data xref to entry |
|---|---:|---:|---:|---:|---:|---:|---:|
| Both caller and target | 29,167 | 29,025 | 3 | 139 | 98 bytes | 1,283 | 27,884 |
| Caller only | 34,719 | 19,669 | 1 | 15,049 | 25 bytes | 31,160 | 3,559 |
| Target only | 4,685 | 4,449 | 94 | 142 | 47 bytes | 306 | 4,379 |
| Neither | 3,866 | 3,475 | 9 | 382 | 52 bytes | 3,598 | 268 |

| Incoming non-call `data` xref measure | Value |
|---|---:|
| Data-xref edges | 299,821 |
| Distinct indexed internal functions as source | 1,311 / 72,437 |
| Distinct indexed internal functions as target | 36,347 / 72,437 |
| Distinct indexed internal functions in either role | 37,040 / 72,437 |
| Indexed internal functions absent from both roles | 35,397 / 72,437 |
| Distinct non-index source addresses | 296,789 |

- ExportCallGraph records direct instruction call references as `call` edges and references to each function entry that are not call references as `data` edges. A data source can be a containing function entry or a raw source address, depending on whether Ghidra resolved a containing function.
- The reproducer validates build/hash metadata and, when the recorded source CSV is present, checks source-row and per-kind counts against SQLite.
- The role partition totals 72,437 and its name/size fields are copied from the internal index; these are candidate-sorting features only.
- Of 3,866 functions absent from both direct-call roles, 3,598 are still targets of a recorded non-call data reference to their entry address. This nominates data-xref provenance for follow-up; it does not identify the reference as a vtable slot, function pointer, or dynamic call.

The verified EXE has image base `0x00400000`; PE virtual address ranges from its section headers are:

| Section | VA start | VA end (exclusive) |
|---|---:|---:|
| `.text` | `0x00401000` | `0x00F93600` |
| `.rdata` | `0x00F94000` | `0x01268200` |
| `.data` | `0x01269000` | `0x014843BC` |
| `.rsrc` | `0x01485000` | `0x01489400` |
| `.reloc` | `0x0148A000` | `0x01606C00` |

Incoming non-call data-xref sites for the 3,866 no-direct-call functions partition as follows:

| Source-site PE section | Xref edges | Distinct no-call function targets* |
|---|---:|---:|
| `.rdata` | 20,309 | 2,315 |
| `.data` | 3,118 | 1,177 |
| `.text` | 344 | 262 |
| symbolic | 6 | 6 |

\* Target sets are non-exclusive: the same function entry can be referenced from more than one section.

## Interpretation / claims

- **Observed:** 68,571/72,437 internal function addresses occur at least once as a direct-call source or target in this export; 3,866 do not.
- **Observed:** 36,347/72,437 internal function addresses are targets of at least one recorded non-call data reference.
- **Unknown:** whether functions missing from a particular edge role are truly leaves/unreferenced or are affected by indirect calls, unresolved references, code/data recognition, or exporter limitations.
- **Not established:** runtime execution/reachability, completeness of the Ghidra reference database, or semantic review coverage.
- The direct call and incoming data-reference datasets have different semantics and denominators; do not combine their edge counts as if they represented one call graph.

## Reproduction and limitations

- Run `python tools/callgraph_coverage.py` from the repository root; it verifies the exact EXE hash, parses PE sections, validates callgraph build/hash metadata and source-CSV counts, and emits call/data coverage plus both partitions above.
- To regenerate source data, run `ExportCallGraph.java` on the matching workspace Ghidra program with `analyzeHeadless -noanalysis -readOnly`, then import it with `python tools/import_callgraph_csv.py`. See [tooling instructions](../docs/tooling/mcp.md).
- The current SQLite and source CSV are local ignored artifacts; the Ghidra exporter and importer plus this experiment are the portable record.
- Direct-call edges omit behavior that does not produce a resolved direct call reference; function presence in the index says nothing about body readability or correctness.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Internal function-index reconciliation: [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md)
- Function-name/size baseline: [EXP-0059](EXP-0059-function-index-name-and-size-baseline.md)
- Callgraph exporter: [ExportCallGraph.java](../research/executable/scripts/ExportCallGraph.java)
- Callgraph importer: [import_callgraph_csv.py](../tools/import_callgraph_csv.py)
- Coverage reproducer: [callgraph_coverage.py](../tools/callgraph_coverage.py)
