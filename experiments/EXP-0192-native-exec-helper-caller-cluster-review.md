---
id: EXP-0192
title: Twenty helper anchors and native-exec callers receive raw-body review
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What raw-body evidence links a selected native-exec wrapper cluster to indexed helper functions 0x00430BF0 and 0x00433F40?"
---

# EXP-0192 — Twenty helper anchors and native-exec callers receive raw-body review

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: review 18 unreviewed EXP-0139 native-exec candidate targets selected for direct calls to `0x00430BF0` and, in a subset, `0x00433F40`; also review both helper bodies as anchors. Inspect every indexed byte in the 20 exact-build functions.
- Exclusions: no UELib class/method name, string type, helper structure type, native-table consumption, runtime reachability, subsystem, or high-level behavior is confirmed by these raw calls. Direct call edges prove only that the bytes contain calls to the recorded addresses.
- Inputs: exact-build executable, `research/executable/functions.csv`, EXP-0139 candidate catalog, EXP-0191 cumulative body-review overlay.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7. Raw code hashes are primary body identifiers.
- Durable outputs: [20-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0192.csv), [100-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0192.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0192.json). The summary records hashes of the executable, function index, candidate catalog, previous overlay, and output files.

## Procedure

1. Verify the registered build ID and executable SHA-256; resolve all selected addresses and sizes from the exact-build function index.
2. Select unreviewed EXP-0139 candidate callers that have direct callsites to `0x00430BF0`, including callers that also reference `0x00433F40`; include both helpers as separate function-body reviews.
3. Map every VA through PE32 image base `0x00400000`, hash the exact indexed range, and disassemble the complete range as x86-32.
4. Record direct callsite VAs/targets and the local argument, field, and copy operations visible in machine code. Keep the candidate export names and inferred helper roles distinct from those observations.
5. Add the 20 body reviews to the cumulative overlay. Preserve unknown subsystem and runtime status and add no semantic claims.

## Observations

- All 20 addresses are exact starts in the 72,437-row function index. All indexed sizes and complete byte ranges match the registered executable; all were absent from the EXP-0191 cumulative overlay. Eighteen addresses are one-edge EXP-0139 class-table candidates; `0x00430BF0` and `0x00433F40` are additional helper anchors outside that target catalog.
- The 18 selected wrappers contain 22 direct call instructions to `0x00430BF0`. Five wrapper bodies also call `0x00433F40`; some bodies call `0x00430BF0` twice. The full per-address direct-call-site list, raw body hash, candidate export path, and body summary are recorded in the evidence CSV.
- In `0x00430BF0`, raw x86 reads fields at `[this+8]` and `[this]`, conditionally calls `0x004246E0`, stores a returned pointer, zeros `[this+8]` and `[this+4]`, then calls `0x004244E0`. This establishes local memory effects; a cleanup/reset helper role and the object's layout remain inferences.
- In `0x00433F40`, raw x86 compares pointers, conditionally calls `0x004246E0`, copies size/capacity-like fields, conditionally calls `0x00EC3D14` with data pointers, and has a call to `0x00428B50`. These operations are consistent with copy/resize behavior, but the structure and helper semantics are not established here.
- Among the callers, `0x005E9C40`, `0x005EE1B0`, and `0x008191F0` share a visible tail containing a receiver virtual call, a direct call to `0x00433F40`, then a call to `0x00430BF0`. `0x00A00C90` calls `0x00B93BC0` instead of making a receiver virtual call before the same two helpers. Other wrappers vary in argument decodes and helper-call counts. This is an observed call-shape cluster, not proof that the wrappers marshal the same type or behavior.
- The cumulative manual body-review overlay rises from 80 to 100 unique functions, or 0.138051% of the internal index. The EXP-0139 subset rises from 51/254 to 69/254; 185 remain without body review. The two helper anchors are outside the EXP-0139 set. This pass adds zero confirmed semantic claims and zero runtime-verified functions.

## Interpretation and claim limits

- **Observed:** 22 indexed call instructions from the 18 selected candidate wrappers target `0x00430BF0`; five wrappers call `0x00433F40`. The anchor bodies contain the field reads/writes, conditional calls, pointer handling, and byte-copy call listed above.
- **Inferred, limited:** the helper bodies are consistent with reset/cleanup-like and copy/resize-like memory operations. The candidate wrappers form a useful comparison cohort because their raw call tails converge on these helpers.
- **Unknown:** the concrete structure types, helper contracts, buffer/string semantics, meanings of VM-decoded values, class ownership of the native-exec targets, and runtime reachability.
- **Not established:** helper callsites or a shared call tail do not confirm a string type, method identity, common owner, runtime native dispatch, or behavior suggested by EXP-0139 labels.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify `Dishonored RHCP/Binaries/Win32/Dishonored.exe` has the recorded SHA-256.
2. Resolve each evidence-row address and size in `research/executable/functions.csv`; map `RVA = VA - 0x00400000` through the PE section table and read exactly `size_bytes` from `file_offset`.
3. Verify each raw-body SHA-256 and disassemble the complete range with Capstone `CS_ARCH_X86` / `CS_MODE_32`.
4. For the 18 EXP-0139 targets, use the candidate catalog to recover the joined UELib export path. Treat the path as candidate metadata only.
5. Verify the cumulative output contains 100 unique addresses and that the 20 addresses in this experiment were absent from EXP-0191.

The Ghidra project was locked by another active process, so no Headless decompilation was attempted. The reviews used read-only raw PE bytes and did not change any Ghidra project, lock file, or game process. No runtime experiment was performed. This experiment does not validate the ignored local callgraph database's whole-program counts; its durable evidence is the raw body hashes and recorded direct callsites.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Candidate catalog: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior function batch: [EXP-0191](EXP-0191-native-state-and-gameplay-anchor-wrapper-review.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
