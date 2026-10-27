---
id: EXP-0198
title: Eighteen additional EXP-0139 targets repeat indexed-table adapter patterns
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do eighteen further unreviewed EXP-0139 indexed targets exhibit the same exact-build indexed-read and indirect-call motifs, and do their catalogued .data pointer cells contain the corresponding function starts?
---

# EXP-0198 — Eighteen additional EXP-0139 targets repeat indexed-table adapter patterns

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: fully decode 18 previously unreviewed exact-build function bodies from the EXP-0139 candidate set. Check indexed memory operands, indirect calls, repeated normalized byte shapes, and raw `.data` pointer-cell values.
- Exclusions: EXP-0139 class/export labels and raw pointer edges are candidate metadata. Neither they nor shared instruction patterns establish concrete implementation names, table ownership, NativeToken identity, runtime reachability, or game behavior. No function is promoted above L1 body analysis.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping and the exact-build function index.
- Prior cumulative snapshot: the 188-row EXP-0197 body-review overlay.

## Procedure

1. Verify the local executable SHA-256 against the build record and resolve all selected addresses through `functions.csv`.
2. Confirm each address is an exact indexed start and absent from the EXP-0197 cumulative review overlay.
3. Hash each indexed body and fully decode it as x86-32; check that decoded instruction sizes cover the inclusive indexed range (`body_end - body_start + 1`). Record indexed reads from absolute base `0x014068F0`, indirect calls through `[0x014069F4]`, and other call forms.
4. Join each target to the existing EXP-0139 row by `raw_handler_target_va`; independently read the DWORD at `handler_pointer_slot_va` from the exact executable and compare it with the target VA.
5. Compare normalized body shapes only after masking Capstone-marked immediate and displacement bytes. Keep body review at L1 and preserve unknown ownership/runtime fields.

## Observations

- The executable hash matches the registered build. All 18 addresses are exact indexed starts, absent from the EXP-0197 overlay, and fully decoded with Capstone x86-32. Body sizes range from 88 to 101 bytes. Each body contains one indexed DWORD read with base `0x014068F0` and scale 4, plus one indirect call through `[0x014069F4]`; each also contains register-indirect call(s). The per-function hashes and call sites are recorded below and in the new raw-body overlay.
- Eighteen raw `.data` pointer cells associated with these EXP-0139 rows were independently read as little-endian DWORDs; every value equals its target function VA. Cell addresses and values are preserved in the evidence CSV. These are static pointer-value observations only.
- Seven 96-byte bodies (`005C9C60`, `005D9C70`, `009E5590`, `009ECC30`, `009F5C10`, `009F80B0`, `009F9560`) share a normalized instruction sequence. Five 91-byte bodies (`005CAA80`, `005D5060`, `005D9B00`, `005D9DA0`, `00748D50`) share another sequence. Four 101-byte bodies (`005C8F00`, `005CF4B0`, `005D4C40`, `009EC090`) form a third group. Normalization zeros only Capstone-marked immediate/displacement encoding bytes; raw hashes remain distinct. `005D3FD0` (93 bytes) and `005C71B0` (88 bytes) are unique under this normalization.
- The EXP-0139 set rises from 109 to 127 of 254 body-reviewed targets, leaving 127 unreviewed. The cumulative manual overlay rises from 188 to 206 unique bodies, or 0.284385% of the 72,437-function index. All 18 additions are L1 body reviews; no L2–L4 claims are added.

## Interpretation and claim limits

- **Observed:** all 18 exact-build indexed bodies fully decode; every body has the specified indexed read and indirect global-cell call motifs.
- **Observed:** sixteen raw `.data` DWORD cells equal their corresponding function start addresses.
- **Observed:** normalized byte-shape groups include seven 96-byte bodies, five 91-byte bodies, and four 101-byte bodies in this batch.
- **Inferred, limited:** these recurring shapes are consistent with generated adapter/wrapper families. EXP-0197/EXP-0160/EXP-0161 provide a reason to investigate the shared indexed base, but these observations do not establish that the selected byte is a NativeToken or identify the table's owner.
- **Unknown:** table entry semantics, ownership/purpose of the indirect cell, concrete native method names, receiver-slot meanings, caller/runtime dispatch, and behavior.
- **Not established:** candidate labels, pointer-cell values, or normalized shape equality prove source-level method identity, class ownership, or runtime execution.

## Reproduction and limitations

With Python, pefile, and Capstone installed:

1. Verify the executable hash and map each indexed VA through the PE image base and section table.
2. Decode the inclusive indexed byte ranges and verify decoded instruction sizes equal each recorded body size.
3. Recompute raw hashes, call operands, indexed memory operands, and normalized hashes from the recorded Capstone version.
4. Join EXP-0139 rows by raw target VA, map each handler pointer cell, and compare its four raw bytes with the target's little-endian VA.
5. Confirm the 18 addresses are absent from the EXP-0197 overlay and present once in the cumulative EXP-0198 overlay.

Analysis was read-only. No Ghidra project or game process was used.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Candidate set: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior body batch: [EXP-0197](EXP-0197-exp0139-indexed-table-adapter-cluster.md)
- Evidence: [18-row body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0198.csv), [206-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0198.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0198.json)
- Related table studies: [EXP-0160](EXP-0160-native-selector-table-static-registration-census.md), [EXP-0161](EXP-0161-core-native-selector-consumer-samples.md)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
