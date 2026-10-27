# Native reverse engineering: high-leverage, evidence-safe review

## Why not analyze 72,437 bodies sequentially?
The exact-build index covers 72,437 internal functions, while EXP-0155 reports 47 manual static body reviews. Reviewing a function can reveal direct callers, callees, shared wrappers, class associations and candidate dataflow **for several functions**. These are lead discoveries, **not automatic body reviews**. L1 advances only for a body actually inspected and recorded. Claims about ownership need type/receiver provenance and alternatives; L3 demands confirmed dataflow and L4 demands replicated build-matched runtime evidence.

## Research unit: a neighborhood, not an isolated function
1. Start with one question (e.g. which receiver reaches a Blink slot, or what native-exec wrapper consumes an argument).
2. Pull 1-hop callers/callees, local xrefs, class-table joins, vtable slot contexts, import/export paths and function body metadata from the same build. Do **not** recursively traverse the entire graph without budget.
3. Group by patterns: identical raw bytes modulo relocations, common callee, shared argument decode, constant/string references, common UELib super chain and adjacent vtable slots. Identical-looking code is still a *candidate family*.
4. Review one high-information representative and compare its siblings using short disassembly/byte differences. Record exact differences, not blanket semantic equivalence.
5. Save separate outcomes per function: `indexed`, `candidate neighbor`, `body reviewed`, `role inferred`, `role confirmed`, `dataflow confirmed`, `runtime replicated`.
6. Record rejected joins and stop conditions. Expand to another hop only if it can distinguish alternatives or reveal a missing boundary.

## Queue and scoring
Generate a reproducible first-pass queue from the published EXP-0139 candidate table and EXP-0155 cumulative review overlay:

```bash
python tools/native_review_queue.py --limit 50 --output reports/native-review-queue.csv
python -m unittest discover -s tests -v
```

The generator ranks unreviewed class-table target candidates by capped incoming edge count, tractable body size and multiple method associations. This is a **heuristic**, not an estimated probability of correctness; it never updates EXP, SQLite, L0–L4, or confirmation status. The current candidate subset contains 254 addresses, 19 reported as reviewed and 235 unreviewed at EXP-0155. The queue covers **only this cohort**, not all 72,437 functions. Recompute with newer overlay/candidate sources when available.

## Focused review packet (one per selected target)
- Build + executable SHA and module RVA, raw range hash, tool/version, analysis options and project revision.
- Question, why selected, 1-hop graph (bounded) and method/class joins with source IDs.
- Input/source arguments, calling convention, stack/frame use, side effects, branches, outputs, indirect targets.
- Neighbor comparison: examined directly / candidate only / ruled out, with exact reasons.
- Alternative interpretations and cheapest distinguishing next experiment.
- Independent reviewer and commands, if reproduced.

[Function template](../../templates/function.md) is a minimal starting point. Never paste copyrighted function dumps.

## Data quality and automation roadmap
**P0:** expand decompile cache key to executable/module hash, normalized RVA, Ghidra version, scripts/options hash, analysis-project revision and language/compiler spec. Missing provenance must be a miss, not a hit. Keep invalidation tests for changed options/project revision and cross-build collision.

**P0:** enforce exact input build_sha256 and module identity for L4 before promotion. Negative cross-build test is mandatory.

**P1:** add a read-only bounded neighborhood extractor from verified callgraph indices: depth<=2, node budget, edge kinds preserved, provenance by source hash; never auto-promote edges to dataflow.

**P1:** export candidate families, seen/reviewed coverage, issue-ready review packets, and immutable source digests. Allow manual prioritization for hypotheses over high-fan-in generic helpers.

**P2:** use batch decompilation only for selected candidate batches with resource limits; cache and deduplicate by body/analysis provenance; track bytes and diagnostics. Keep separate counts for analyzed outputs and manually reviewed bodies.

## Productivity metrics
Track: reviewed bodies per investigator-hour; distinct hypotheses resolved; useful reviewed-neighbor leads per anchor; evidence links independently replicated; candidate→confirmed conversion; re-review due to cache changes. Do not use total index coverage as the only success signal. Measure a baseline and pilot (e.g. 20 selected targets) before claiming a speedup.

## Prevent common false inferences
- Static direct-call does not establish runtime reachability.
- Two classes pointing to one native target do not necessarily share runtime behavior.
- A vtable displacement is not a method name.
- Body similarity does not establish receiver identity.
- One reviewed body does not turn its caller/callee into L1.
- Candidate class/method joins are not confirmed semantic roles.

See [function evidence model](function-evidence-model.md), [native triage](function-triage.md), [EXP-0139](../../experiments/EXP-0139-native-class-table-zero-token-handler-join.md), and [EXP-0155](../../experiments/EXP-0155-set-enabled-shared-native-adapter.md).
