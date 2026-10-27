---
id: EXP-0201
title: Four EXP-0139 candidates call one additional indexed function
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do four unreviewed EXP-0139 candidates directly call the same indexed function, and what direct call structure is visible in that target body?
---

# EXP-0201 — Four EXP-0139 candidates call one additional indexed function

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: four unreviewed exact-build EXP-0139 candidate bodies that directly call `0x0078DCB0`, plus the exact-build body at `0x0078DCB0` itself.
- Exclusions: EXP-0139 labels are candidate cross-source metadata. A direct call proves a static code edge, not semantic ownership or runtime invocation. No behavior or source name is assigned to the target.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping, exact-build function index, and the offline callgraph index.
- Baseline: the EXP-0200 cumulative overlay contained 218 unique body reviews; all five selected starts were absent.

## Procedure

1. Verify the registered executable SHA-256, resolve each address and inclusive size through `functions.csv`, and confirm absence from the EXP-0200 overlay.
2. Hash and fully decode all five bodies as x86-32. Record direct and indirect calls, table reads, and absolute memory operands.
3. For the four EXP-0139 catalog targets, read each registered `.data` handler pointer slot directly from the exact executable and compare its DWORD with the target VA.
4. Query the offline callgraph for callers of `0x0078DCB0`; compare returned indexed call edges with the four raw caller-body call instructions. Treat the endpoint's returned row count as bounded output, not a complete caller census.
5. Record all five as L1 body analysis. Do not promote a direct static edge to L3 dataflow or runtime evidence.

## Observations

- All five bodies are exact indexed starts, absent from EXP-0200, and fully decoded. Four candidate bodies have raw direct calls to `0x0078DCB0` at:
  - `005F9D00`: `005F9DBA → 0078DCB0` (also `005F9DAB → 005CB0C0`)
  - `005FB5D0`: `005FB68F → 0078DCB0`
  - `005FA520`: `005FA608 → 0078DCB0`
  - `00984040`: `00984133 → 0078DCB0`
- Each of those four bodies also has a call through `[0x014069F4]` and at least one indexed read from `[EDX*4 + 0x014068F0]`. Their raw body hashes and exact table-read/call sites are recorded in the evidence CSV.
- The target body `0078DCB0` is 141 bytes / 49 instructions. It has two direct calls, `0078DCF7 → 004246E0` and `0078DD1F → 00423D70`, and one absolute memory read at `[0x013B49A8]`; it contains no observed read from `0x014068F0` and no call through `[0x014069F4]`.
- The offline caller query requested up to 500 rows and returned 200 call-edge rows (136 distinct caller addresses in those returned rows). Three of the four selected candidates appear in that bounded response; the fourth edge is confirmed by the raw caller body at `00984133`. The query result therefore does not establish the total number of callers.
- The four EXP-0139 `.data` handler pointer slots were independently read and each DWORD equals the corresponding indexed function VA. The anchor is outside the EXP-0139 set and has no pointer slot asserted by this experiment.
- The EXP-0139 subset rises from 139 to 143 of 254 body-reviewed targets, leaving 111 unreviewed. The cumulative manual overlay rises from 218 to 223 unique bodies, or 0.307854% of the 72,437-function index. No semantic or runtime claims are added.

## Interpretation and claim limits

- **Observed:** four exact-build candidate bodies contain direct call instructions to the same indexed start `0x0078DCB0`; the anchor body itself contains two further direct calls.
- **Observed:** the four candidate callers contain both indexed table reads through `0x014068F0` and indirect calls through `[0x014069F4]`; four exact `.data` slots contain the caller target VAs.
- **Inferred, limited:** the common target is a useful high-connectivity point for function triage. Its role and whether those call paths are related at the subsystem or behavior level remain unknown.
- **Unknown:** implementation names, argument/dataflow relationships between callers and target, global/table ownership, runtime reachability, and gameplay effect.
- **Not established:** caller count beyond the bounded callgraph response, candidate names, static edges, or pointer equality prove semantics or runtime execution.

## Reproduction and limitations

With Python, pefile, Capstone, and the local offline callgraph index available:

1. Verify the exact executable hash and inclusive indexed bounds.
2. Fully decode each body and check that decoded instruction sizes cover its recorded size; recompute raw hashes and call targets.
3. Map the four EXP-0139 pointer slots to raw executable bytes and compare each little-endian DWORD with its target VA.
4. Query callers of `0078DCB0`. The endpoint may cap results; raw body checks are the authoritative confirmation for the four selected call instructions.
5. Verify the five addresses are absent from EXP-0200 and unique in the cumulative EXP-0201 overlay.

This was read-only static analysis; no Ghidra project or game process was used.

## Links

- Candidate provenance: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior body batch: [EXP-0200](EXP-0200-six-short-native-candidates-share-a-normalized-body.md)
- Evidence: [five-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0201.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0201.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0201.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
