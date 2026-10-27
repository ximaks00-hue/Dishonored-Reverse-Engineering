---
id: EXP-0197
title: Nineteen class-table candidates index one shared table; twenty share an indirect call cell
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do a selected set of unreviewed EXP-0139 targets share exact indexed-table and indirect-call body patterns, and do their candidate .data cells contain pointers to the indexed starts?
---

# EXP-0197 — Nineteen class-table candidates index one shared table; twenty share an indirect call cell

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: fully decode 20 previously unreviewed exact-build function targets from the EXP-0139 class-table candidate set. Record instruction bodies, indexed global memory reads, indirect calls, normalized-byte families, and eight raw `.data` DWORD cells whose values equal selected indexed starts.
- Exclusions: candidate class/method names, registration labels, and incoming `.data` references do not prove class ownership, vtable ownership, native dispatch, or runtime reachability. Shared address `0x014068F0` is also discussed in EXP-0160/0161; same-address usage alone does not identify its owner or prove that every selected function consumes a NativeToken. No semantic or runtime claims are added.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping, exact-build `functions.csv`, and raw little-endian reads from the registered executable.
- Durable outputs: [20-row raw-body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0197.csv), [188-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0197.csv), and [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0197.json).

## Procedure

1. Verify the executable SHA-256 against the build record; load the exact-build function index, EXP-0139 candidate catalog, and EXP-0196 cumulative review overlay.
2. Resolve each of the 20 selected candidate VAs to an exact indexed start and size; confirm each was absent from the EXP-0196 body-review overlay.
3. Map, SHA-256 hash, and fully decode every indexed body as x86-32. Record direct and indirect call operands separately and record absolute/static memory operands with read/write access.
4. Normalize raw byte ranges by zeroing only Capstone-marked immediate and displacement encoding bytes. Preserve instruction order, opcodes, register encodings, and exact unnormalized per-function hashes.
5. Read eight selected DWORD cells from their exact PE file offsets as little-endian values; verify each value equals its expected indexed function start and that each source cell lies in `.data`.
6. Add body-review records as L1 analysis only; do not infer a source name or runtime dispatch from candidate metadata or instruction-shape similarity.

## Observations

- The executable hash matches build `10256413`. All 20 selected VAs are exact indexed starts and were absent from the 168-row EXP-0196 cumulative overlay. All 20 body ranges decode completely; sizes range from 53 to 310 bytes. The per-address raw SHA-256 values and memory/call instructions are in the evidence CSV.
- None of the 20 bodies contains an immediate direct `call` target. All 20 contain an indirect call through memory cell `0x014069F4`. Nineteen also read a DWORD from an indexed memory expression with base `0x014068F0` and scale 4, e.g. `[EDX*4 + 0x014068F0]`; `009F1A00` is the exception and has no observed read from that indexed table base.
- In the 19 table-reading bodies, the raw instructions load a value from the indexed table and later issue register-indirect calls; these are visible intra-body operations. This EXP does not establish what the table entries represent. The absolute cell `0x014069F4` is itself used as an indirect call operand in every selected body.
- With only immediate/displacement encoding bytes zeroed, three normalized-byte groups repeat: eight 96-byte bodies (`005D0360`, `009ED500`, `009EC020`, `009ECD70`, `009F8290`, `009EF8A0`, `00957B40`, `009F7300`); two 109-byte bodies (`005DBAC0`, `009EF960`); and two 107-byte bodies (`009EDB10`, `009EED20`). The other eight bodies have unique normalized-byte sequences. Exact raw hashes differ for all selected starts; normalization is a shape comparison, not body identity.
- Eight `.data` cells were independently read from the executable and each contained the exact expected indexed function VA: `012E3124→009ECD70`, `012E3194→009EC6A0`, `012E31A8→005C66B0`, `012E31B0→009ED500`, `012E31B4→009F1A00`, `012E31C4→005D0360`, `012E31F8→005DBAC0`, and `012E31FC→009EC020`. These are confirmed pointer values in `.data`; the ownership and purpose of the cells remain unknown.
- The indexed base `0x014068F0` is the same exact address examined as a guarded dispatch-table candidate in EXP-0160 and read by sampled consumers in EXP-0161. This is a cross-experiment address match. The current body evidence does not by itself prove that all 19 table reads use the same logical table or that their preceding index value is a NativeToken.
- The EXP-0139 subset rises from 89 to 109 of 254 targets body-reviewed, leaving 145 still unreviewed; all 254 remain subsystem-unassigned. The cumulative manual body-review overlay rises from 168 to 188 unique functions, or 0.259536% of the internal index. No semantic claims or runtime-verified functions are added.

## Interpretation and claim limits

- **Observed:** 20 exact-build bodies are fully decoded and individually hashed. Each contains an indirect call through `[0x014069F4]`; 19 contain an indexed read from the absolute base `0x014068F0`; none contains an immediate direct call.
- **Observed:** three normalized-byte families repeat across 12 bodies after a narrowly specified encoding-byte normalization. The exact raw bodies remain distinct.
- **Observed:** eight `.data` DWORD cells contain exact pointer values to eight selected indexed function starts.
- **Inferred, limited:** the repeated indexed read and indirect call shapes are consistent with a family of generated dispatch adapters. The same absolute base in EXP-0160/0161 makes a shared dispatch-table relationship worth discriminating next, but does not prove NativeToken meaning or class-table ownership.
- **Unknown:** the owner and entry format of `0x014068F0`, the role of `0x014069F4`, each function's argument and vtable-slot semantics, why `009F1A00` lacks the observed indexed read, cell owners, and runtime reachability.
- **Not established:** normalized-byte equality, `.data` pointer equality, or membership in EXP-0139 proves no concrete class, method name, runtime registration, or game behavior.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify the registered executable SHA-256; resolve each address and size through `research/executable/functions.csv` and map its RVA through PE32 sections.
2. Hash each full indexed body and verify Capstone x86-32 instruction sizes cover every byte. Compare direct and indirect calls and static memory operands with the evidence CSV.
3. Recreate normalization by zeroing only Capstone-reported `disp_offset/disp_size` and `imm_offset/imm_size` bytes in each instruction encoding; hash the normalized bodies and compare their groups.
4. For each listed `.data` cell, map its VA through the PE section table, read one little-endian DWORD, and compare with the recorded target VA.
5. Verify all 20 starts are absent from EXP-0196 and that the cumulative overlay contains 188 unique addresses.

This was read-only raw-byte and static-data analysis. No Ghidra project, game process, or runtime state was changed or used.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent candidate set: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Related shared-table observations: [EXP-0160](EXP-0160-native-selector-table-static-registration-census.md), [EXP-0161](EXP-0161-core-native-selector-consumer-samples.md)
- Prior body-review batch: [EXP-0196](EXP-0196-eleven-window-dispatcher-callees.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
