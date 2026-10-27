---
id: EXP-0059
title: Name-pattern and size baseline for the internal function index
experiment_status: done
claim_status: observed
build: "10256413"
question: "What name-pattern and function-size distributions appear in the reconciled 72,437-row internal Ghidra function index?"
---

# EXP-0059 — Name-pattern and size baseline for the internal function index

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: compute exact name-pattern, duplicate-name, and byte-size distributions from `research/executable/functions.csv`, whose 72,437 internal addresses were reconciled to the exact-build Ghidra function set in EXP-0041.
- Exclusions: index labels and lengths do not establish subsystem ownership, semantic review, decompilation quality, or behavior. The 488 external functions are outside this CSV and were reconciled separately.
- Tools: Python 3 standard library; [function_index_coverage.py](../tools/function_index_coverage.py).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable hash.
2. Read the reconciled function CSV and require only the recorded columns `address`, `name`, `signature`, `size`, `body_start`, and `body_end`.
3. Classify names by exact regex: `^FUN_[0-9A-Fa-f]+$`, then `^thunk_FUN_[0-9A-Fa-f]+$`, otherwise `other_names`.
4. Count unique addresses, unique names, and repeated name values; bucket the integer `size` field into inclusive ranges `[0,16]`, `[17,32]`, `[33,64]`, `[65,128]`, `[129,256]`, `[257,512]`, `[513,1024]`, and `[1025,+∞)`.
5. Run `python tools/function_index_coverage.py` to reproduce the JSON summary.

## Observations

- The CSV has 72,437 rows and 72,437 unique addresses, consistent with the internal-function denominator reconciled in EXP-0041.
- Name-pattern counts:

| Exact pattern class | Rows |
|---|---:|
| `FUN_<hex-address>` | 56,618 |
| `thunk_FUN_<hex-address>` | 107 |
| Other labels | 15,712 |

- There are 72,228 unique name strings; 40 distinct name values are repeated, accounting for 209 rows beyond the unique-name count. The most repeated name is `` `scalar_deleting_destructor' `` (93 rows), followed by `Construct` (17) and `CreateObject` (16).
- The indexed size field ranges from 1 to 21,461 bytes; median 40 bytes; arithmetic mean approximately 143.02 bytes.

| Indexed function size | Rows |
|---|---:|
| 0–16 bytes | 18,668 |
| 17–32 bytes | 10,096 |
| 33–64 bytes | 12,458 |
| 65–128 bytes | 12,238 |
| 129–256 bytes | 9,695 |
| 257–512 bytes | 5,633 |
| 513–1,024 bytes | 2,285 |
| 1,025 bytes or more | 1,364 |

## Interpretation / claims

- **Observed:** the exact-build internal index is dominated by address-derived function names (56,725/72,437 across the two address-pattern classes); 15,712 rows use other labels.
- **Observed:** repeated labels are present and concentrated in generic/destructor/API-like names; a label string is not a unique function identity, so addresses remain the join key.
- **Unknown:** what proportion of the 15,712 other labels identify the correct source-level subsystem or ownership, and what proportion of all functions has been semantically reviewed.
- **Not established:** subsystem coverage, function behavior coverage, decompilation success, function complexity from byte length, or the completeness of vtable/callgraph recovery.

## Reproduction and limitations

- Run `python tools/function_index_coverage.py` from the repository root. The script prints a JSON report and writes no files.
- Function index provenance and exact address-set reconciliation are in [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md).
- The CSV covers internal functions only. Do not combine the 72,437 internal denominator with the 488 external entries as if they were equivalent code-body functions; see EXP-0041.
- Name/size groups are triage measures. Any subsystem grouping needs evidence such as exact function bodies, call relationships, vtable ownership, strings/data xrefs, or package/native joins.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Index provenance: [EXP-0041](EXP-0041-ghidra-function-count-reconciliation.md)
- Function CSV: [functions.csv](../research/executable/functions.csv)
- Reproducer: [function_index_coverage.py](../tools/function_index_coverage.py)
