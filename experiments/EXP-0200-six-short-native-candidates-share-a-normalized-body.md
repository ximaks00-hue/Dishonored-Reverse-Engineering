---
id: EXP-0200
title: Six short EXP-0139 candidate bodies share one normalized byte sequence
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do six compact, unreviewed EXP-0139 candidate bodies share the same normalized byte sequence while retaining distinct direct-call targets?
---

# EXP-0200 — Six short EXP-0139 candidate bodies share one normalized byte sequence

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: six 48-byte exact-build function bodies selected from one previously unreviewed EXP-0139 normalized-shape group.
- Exclusions: EXP-0139 owner/method labels are candidates. A shared normalized body, direct call, or `.data` pointer does not prove implementation semantics, ownership, or runtime reachability. These remain L1 body reviews.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE bytes and the exact-build function index.
- Baseline: all six starts were absent from the EXP-0199 cumulative overlay.

## Procedure

1. Verify the registered executable hash and map each selected VA to its exact indexed range.
2. Confirm all six starts are absent from the EXP-0199 cumulative overlay.
3. Hash and fully decode each inclusive byte range as x86-32. Record direct and indirect calls, plus absolute-memory operands.
4. Join EXP-0139 pointer rows by target VA, map the handler pointer slot through the PE image, and compare its raw little-endian DWORD with the function start.
5. Normalize each body by zeroing only Capstone-reported immediate and displacement encoding bytes, then compare SHA-256 values. Do not infer semantics from the shared shape.

## Observations

- All six addresses are exact indexed starts, absent from EXP-0199, and fully decoded as 20 instructions / 48 bytes each. Each body has one call through `[0x014069F4]` and one direct immediate call to a different target:
  - `005CF910`: `005CF936 → 00577ED0`
  - `005CFD70`: `005CFD96 → 00783110`
  - `005D0330`: `005D0356 → 007A4370`
  - `005D0440`: `005D0466 → 00786280`
  - `005D2760`: `005D2786 → 007AD960`
  - `005D5410`: `005D5436 → 004DBA00`
- All six produce the same normalized SHA-256: `613E0B4D0AD41377CE9FD3EAC3EE413E604B5C99B8D74CC8916430C9852D1D52`. Their raw SHA-256 hashes differ; the direct-call target encoding accounts for part of the byte difference, while normalization is limited to the recorded immediate/displacement fields.
- None of the six bodies references indexed table base `0x014068F0`; the only observed absolute memory operand in each body is the indirect call through `[0x014069F4]`.
- Six EXP-0139 `.data` pointer slots were independently read and each DWORD equals its respective target VA. The per-target hashes, slots, and candidate export labels are in the evidence CSV.
- The EXP-0139 set rises from 133 to 139 of 254 body-reviewed targets, leaving 115 unreviewed. The cumulative manual overlay rises from 212 to 218 unique bodies, or 0.300951% of the 72,437-function index. No semantic or runtime claims are added.

## Interpretation and claim limits

- **Observed:** six compact function bodies have exact equal normalized-byte hashes under the specified Capstone-field masking, with six distinct immediate direct-call targets and six calls through the same absolute cell.
- **Observed:** six raw `.data` pointer cells contain their corresponding indexed function starts.
- **Inferred, limited:** the shared shape supports a compact generated-wrapper family hypothesis and suggests the direct call target is a useful discriminator for the next comparison. The particular operation and object relationship remain unknown.
- **Unknown:** the role of `[0x014069F4]`, class/function ownership, argument and receiver semantics, and runtime reachability.
- **Not established:** EXP-0139 candidate names, normalized-byte equality, or pointer equality proves source-level method identity or behavior.

## Reproduction and limitations

With Python, pefile, and Capstone installed:

1. Verify the exact executable hash and inclusive function bounds.
2. Decode each 48-byte body and check that instruction sizes sum to 48.
3. Zero only Capstone `imm_offset/imm_size` and `disp_offset/disp_size` ranges; recompute raw and normalized hashes.
4. Read the four bytes at each EXP-0139 `handler_pointer_slot_va` and compare with the indexed target VA.
5. Verify all six addresses are absent from EXP-0199 and unique in the cumulative EXP-0200 overlay.

This was read-only static analysis; no Ghidra project or game process was used.

## Links

- Candidate provenance: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior overlay: [EXP-0199](EXP-0199-exp0139-high-information-adapter-comparison.md)
- Evidence: [six-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0200.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0200.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0200.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
