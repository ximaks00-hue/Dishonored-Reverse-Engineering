# Function evidence model

Function coverage is recorded in independent evidence layers. A decompiler result is analysis coverage; it does not establish a semantic role, a dataflow relation, or runtime behavior.

## L0–L4 gates

| Gate | Requirement | What it does not imply |
| --- | --- | --- |
| L0 — Indexed | A function row is present in the exact-build inventory. | No body review or semantic claim. |
| L1 — Analyzed | At least one complete or partial analysis run is tied to the function and its build input hash. | No proven role or behavior. |
| L2 — Understood | A confirmed role claim has a traceable evidence reference for the same build. | No connection to another function or runtime execution. |
| L3 — Connected | A confirmed `dataflow` edge links the function to another indexed function. Direct calls and xrefs alone do not meet this gate. | No proof that the edge is reached in a game session. |
| L4 — Runtime verified | A replicated runtime record is confirmed and names the matching build and a preserved baseline/capture. | No generalization beyond the recorded conditions. |

The database exposes both the sequential gate and four separate axes: analysis, semantic claim, connectivity, and runtime evidence. This keeps useful partial progress visible when evidence does not satisfy every earlier gate. Only confirmed claims advance L2–L4; observed, inferred, rejected, unknown, and superseded claims remain separately searchable.

## Identity and provenance invariants

- Function identity is scoped by app/build, executable SHA-256, module, VA, RVA, and size.
- For the current x86 image, `RVA = VA - ImageBase`. The sync importer reads PE32 headers, verifies the configured executable SHA-256 and image base, and checks every indexed function range against `SizeOfImage`.
- Each imported index row records the SHA-256 of `research/executable/functions.csv`. Each analysis run records its input binary hash, tool/version, options hash when available, source reference, and deterministic cache key.
- Evidence edges record their relation kind. `direct_call`, `virtual_dispatch`, and `xref` cannot be treated as `dataflow` without a separate supported claim. Pointer-origin notes can record the source VA/RVA and how the pointer was obtained.
- EXP remains the source of truth for research claims. SQLite is a derived, queryable ledger; do not edit its ignored local DB by hand or promote generated candidates to claims.

## Current importer behavior

`python tools/knowledge/sync_from_experiments.py` imports all 72,437 exact-build internal function-index rows at L0. It imports the 37 cumulative manual body reviews as L1 analysis records only; candidate or unresolved roles in that overlay are not converted to semantic claims. The seven existing curated function records are imported as claims with their original claim statuses and EXP references. No L3 dataflow edge or L4 runtime verification is synthesized from a call graph, static address match, or decompilation.

The `function_research_progress` SQLite view provides per-function coverage, and the sync summary reports counts by L0–L4. Adding new analysis tools is a later step: their results must use the cache key and evidence fields before they can contribute to coverage.
