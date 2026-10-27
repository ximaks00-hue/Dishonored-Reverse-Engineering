# Native code analysis

**Status: early semantic coverage over a complete published index.** Indexing all functions provides a denominator; it does not mean all functions have been analyzed or understood.

## Current counts

- 72,437 exact-build internal functions in the published index (EXP-0041/0072).
- 47 cumulative manual body-review rows through EXP-0155.
- The portable EXP-0155 export contains 54 functions with analysis evidence: 47 overlay rows plus seven curated source-backed records. Four curated records have `confirmed` claim status; the others preserve their original statuses.
- Portable highest-known evidence levels are L0=72,383, L1=50, L2=4. The export does not publish L3/L4, and this is not a statement about ignored local SQLite contents.
- EXP-0139's separate class-table candidate catalog maps 329 edges to 254 indexed functions; 19 targets received body reviews, while all 254 remain subsystem-unknown in that catalog.

The machine-readable [CSV](../../research/executable/evidence/function-triage/function-coverage-EXP-0155.csv) provides one row per function. Its [manifest](../../research/executable/evidence/function-triage/function-coverage-EXP-0155.json) hashes source artifacts and states the export boundary. Reproduce with `python tools/export_function_coverage.py --check`.

## Method

Select functions that resolve a high-value ownership or dataflow gap, distinguish competing hypotheses, or characterize a reusable class/table/dispatcher cluster. Do not analyze the next address merely because it is next. Keep owner, semantic role, call relation, dataflow, and runtime evidence distinct.

## Priority gaps

1. Trace candidate native registrations to their owning class/table and verify dataflow or dispatch.
2. Expand body review in high-connectivity clusters where a single owner or adapter result can classify many records.
3. Preserve open hypotheses such as `FUN_00C0CA70` as open/weakened; do not relabel them rejected without discriminating evidence.
4. Add L4 only from a matching-build runtime record with a recorded baseline.

## Sources

[Function evidence model](../methodology/function-evidence-model.md) · [Function triage catalog](../../research/executable/evidence/function-triage/README.md) · [EXP-0072](../../experiments/EXP-0072-exact-build-internal-function-subsystem-triage.md) · [EXP-0155](../../experiments/EXP-0155-set-enabled-shared-native-adapter.md)
