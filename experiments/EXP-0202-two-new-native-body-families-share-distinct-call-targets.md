---
id: EXP-0202
title: Two new native candidate body families expose five distinct direct-call edges
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do five unreviewed EXP-0139 candidates form two repeated normalized body families, and which exact-build functions do they directly call?
---

# EXP-0202 — Two new native candidate body families expose five distinct direct-call edges

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: three 96-byte and two 109-byte exact-build bodies from two unreviewed EXP-0139 shape groups.
- Exclusions: EXP-0139 owner/method labels are cross-source candidates. A normalized body match or static call edge does not establish semantic role, class ownership, NativeToken identity, runtime reachability, or gameplay behavior. All five are L1 body reviews.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping, exact-build function index, and offline callgraph queries.
- Baseline: all five starts were absent from cumulative EXP-0201.

## Procedure

1. Verify the registered executable hash; resolve each address and inclusive size through `functions.csv` and ensure it is absent from EXP-0201.
2. Hash and fully decode each body as x86-32. Record table reads, direct calls, indirect calls, and absolute memory operands.
3. For each target, join the EXP-0139 row by raw handler target VA; independently read the candidate `.data` slot as a little-endian DWORD and compare it with the function VA.
4. Normalize each body by zeroing only Capstone-marked immediate and displacement bytes and compare the resulting hashes.
5. Query the offline callgraph for each direct-call target to estimate indexed caller connectivity. Treat the returned edge counts as static index data, not semantic or runtime evidence.

## Observations

- All five addresses are exact indexed starts, absent from EXP-0201, and fully decoded. Each has one indexed read through `[EDX*4 + 0x014068F0]`, one register-indirect call through the loaded `EDX`, one indirect call through `[0x014069F4]`, and one direct call:

  | Function | Size | Direct call site → target | Candidate `.data` slot → target |
  | --- | ---: | --- | --- |
  | `005C5D00` | 96 | `005C5D4E → 007D7620` | `0128F834 → 005C5D00` |
  | `005C7150` | 96 | `005C719E → 0069FB10` | `0128DC34 → 005C7150` |
  | `005CFD10` | 96 | `005CFD5E → 007BDE20` | `0128EE84 → 005CFD10` |
  | `005D1270` | 109 | `005D12CB → 007C3BC0` | `0128EF6C → 005D1270` |
  | `005DD150` | 109 | `005DD1AB → 00594DE0` | `0128F664 → 005DD150` |

- The three 96-byte bodies share normalized SHA-256 `64DEAA171C4A6BEA6167BA010D63501781690D08D5B91F3733EA0EAF4B3B27F5`; the two 109-byte bodies share normalized SHA-256 `035F72E8C5E56A07F5E4B7AD774EDFE91E63F8D3D122AB769E5C5E1854B159E2`. All five raw body hashes differ. The two groups' direct-call targets are distinct.
- The offline callgraph currently returns 3 call-edge rows to `007D7620`, 1 to `0069FB10`, 7 to `007BDE20`, 11 to `007C3BC0`, and 14 to `00594DE0` (13 distinct caller addresses for the last target). These are recorded graph counts, not evidence that all callers were manually reviewed.
- Five candidate `.data` handler slots were read directly from the exact executable; each DWORD equals the corresponding indexed target VA. Their class/export names remain catalog metadata.
- The EXP-0139 set rises from 143 to 148 of 254 body-reviewed targets, leaving 106 unreviewed. The cumulative manual overlay rises from 223 to 228 unique bodies, or 0.314756% of the 72,437-function index. No semantic or runtime claims are added.

## Interpretation and claim limits

- **Observed:** two normalized body families contain five bodies and expose five direct call edges to five distinct indexed addresses.
- **Observed:** each selected body also reads from indexed base `0x014068F0`, calls through `[0x014069F4]`, and has a candidate `.data` handler cell containing its own VA.
- **Inferred, limited:** the 96-byte and 109-byte shapes are useful separate candidate adapter families. The callgraph's returned target counts can guide which callees to inspect next, but do not explain call arguments or behavior.
- **Unknown:** meanings and owners of all five implementations and five callees, selector/table semantics, arguments/dataflow, and runtime reachability.
- **Not established:** shared normalized bytes or static call relationships prove a shared source method, subsystem, or gameplay behavior.

## Reproduction and limitations

With Python, pefile, Capstone, and the offline callgraph index available:

1. Verify the exact executable hash and indexed inclusive ranges.
2. Decode every complete body and recompute its raw and normalized SHA-256 using Capstone immediate/displacement offsets.
3. Read each EXP-0139 handler pointer cell from raw PE bytes and compare the little-endian DWORD with the function VA.
4. Query the offline callgraph for the five target addresses; counts describe that index snapshot only.
5. Verify all five starts are absent from EXP-0201 and appear once in the cumulative EXP-0202 overlay.

This was read-only static analysis; no Ghidra project or game process was used.

## Links

- Candidate provenance: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior overlay: [EXP-0201](EXP-0201-four-candidate-functions-share-a-direct-call-target.md)
- Evidence: [five-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0202.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0202.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0202.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
