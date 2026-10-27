---
id: EXP-0193
title: Twenty short native wrapper bodies share one normalized instruction shape
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What low-level body shape is shared by the next 20 short, unreviewed EXP-0139 class-table targets?"
---

# EXP-0193 — Twenty short native wrapper bodies share one normalized instruction shape

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: review 20 unreviewed singleton targets from EXP-0139 selected because their indexed bodies are short and share a normalized x86 instruction/operand shape. Each individual 53-byte range was hashed and fully disassembled.
- Exclusions: no class ownership, method identity, runtime table dispatch, vtable method meaning, subsystem, or gameplay behavior is confirmed. The EXP-0139 export names remain candidate metadata; the vtable displacements are raw call-site observations.
- Inputs: exact-build executable, `research/executable/functions.csv`, EXP-0139 candidate catalog, EXP-0192 cumulative manual-review overlay.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7. Raw body hashes are primary identifiers.
- Durable outputs: [20-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0193.csv), [120-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0193.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0193.json). The summary hashes the executable, index, candidate catalog, previous cumulative overlay, and outputs.

## Procedure

1. Verify the registered executable hash and build ID; resolve every candidate address and size from the exact-build function index.
2. Select 20 unreviewed EXP-0139 targets with a common 53-byte VM-frame wrapper shape. Confirm each is absent from the EXP-0192 cumulative review overlay.
3. Map each VA through PE32 image base `0x00400000`, hash its 53 indexed bytes, and decode all 53 bytes independently as x86-32.
4. Compare the normalized instruction/operand shapes while preserving each exact raw body hash and its individual vtable displacement.
5. Record the class-table join as candidate-only evidence; add the 20 body observations without assigning confirmed semantic or runtime claims.

## Observations

- All 20 addresses are exact starts in the 72,437-row internal function index, have indexed size 53 bytes, map into `.text`, and were absent from EXP-0192. Each has one EXP-0139 class-table/name/export candidate edge.
- Each complete body decodes to 53/53 bytes. After masking numeric immediate/displacement values, all 20 have the same normalized instruction/operand shape: advance/read the VM frame cursor at `+0x18`; test the next byte against `0x41`; conditionally advance the cursor and call through pointer cell `0x014069F4`; load a receiver vtable entry and call indirectly; return with `ret 8`.
- The exact byte sequences are not identical. Their final indirect-call displacements range from `+0x128` to `+0x564`. The per-address evidence CSV records each exact raw SHA-256, vtable displacement, and EXP-0139 candidate export path. A repeated call shape does not identify the slot owner or meaning.
- The cumulative manual body-review overlay rises from 100 to 120 unique functions, or 0.165661% of the internal index. The EXP-0139 subset rises from 69/254 to 89/254; 165 remain without body review. This experiment adds zero confirmed semantic claims and zero runtime-verified functions; the class-table candidate set remains subsystem-unassigned.

## Interpretation and claim limits

- **Observed:** all 20 bodies contain the same normalized 53-byte instruction shape, with individually recorded raw bytes and different vtable displacements.
- **Inferred, limited:** the shape is consistent with a generated or templated VM-frame adapter family. The selected bodies are low-cost to compare because the same control-flow skeleton is reused.
- **Unknown:** whether the class-table pointers are consumed as runtime dispatch entries; which concrete class owns each receiver; the meaning of each slot and marker; and the semantics/reachability of the named methods.
- **Not established:** normalized shape, matching size, or matching export names do not establish identical implementation, shared ownership, method identity, or runtime behavior.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify the registered executable SHA-256.
2. For each evidence row, resolve the indexed address and size, map `RVA = VA - 0x00400000` through the PE section table, read 53 bytes, and verify the raw-body SHA-256.
3. Decode each full range using Capstone `CS_ARCH_X86` / `CS_MODE_32`; compare instructions after normalizing numeric values while retaining the recorded slot displacement.
4. Filter the EXP-0139 catalog by address to recover the source export path; keep it labeled as a candidate join.
5. Verify the cumulative overlay has 120 unique addresses and that the 20 new addresses were absent from EXP-0192.

No Ghidra Headless session, game launch, or runtime experiment was used. Raw PE bytes were read without changing the Ghidra project or process. The EXP-0139 catalog and its UELib name joins remain candidate evidence; this experiment establishes body shape only.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent candidate catalog: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior batch: [EXP-0192](EXP-0192-native-exec-helper-caller-cluster-review.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
