---
id: EXP-0191
title: Twenty native-state callbacks and gameplay anchors receive raw-body review
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What body-level patterns are visible in the next 20 unreviewed singleton targets from the EXP-0139 class-table candidate catalog?"
---

# EXP-0191 — Twenty native-state callbacks and gameplay anchors receive raw-body review

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect 20 previously unreviewed exact starts from the 254-address EXP-0139 catalog: 14 small AI-state callback candidates and six larger gameplay-anchor candidates. Review the complete indexed byte range for each using raw PE mapping and x86-32 disassembly.
- Exclusions: no method name, class owner, concrete vtable method, runtime dispatch, reachability, subsystem, or gameplay behavior is confirmed by class-table/name joins or wrapper shape. Virtual slot displacements are observations at the callsites only.
- Inputs: exact-build executable, `research/executable/functions.csv`, EXP-0139 candidate catalog, and the EXP-0190 cumulative manual-review overlay.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7. Raw code hashes are primary body identifiers.
- Durable outputs: [20-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0191.csv), [80-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0191.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0191.json). The summary records SHA-256 hashes for the executable, function index, EXP-0139 candidate catalog, previous cumulative overlay, and both outputs.

## Procedure

1. Require the registered build ID and executable SHA-256; confirm each address and size against the exact-build function index.
2. Select the next unreviewed singleton candidates for a coherent AI-state callback cohort, then add six higher-cost gameplay anchors to compare argument-decoding and call shapes.
3. Map each VA through PE32 image base `0x00400000`, hash the exact indexed byte range, and disassemble all indexed bytes in x86-32 mode.
4. Record frame cursor operations, parameter decode shapes, optional marker handling, receiver vtable slot displacement, output storage, and return behavior visible in machine code.
5. Compare argument counts/shapes with EXP-0139 UELib declarations as a plausibility check only. Add the body observations to the cumulative overlay without assigning semantic roles or runtime status.

## Observations

- All 20 addresses are exact starts in the 72,437-row index, their indexed sizes match EXP-0139, and their complete indexed byte-range hashes match the reviewed executable. Each has one EXP-0139 class-table/name/export candidate edge and was absent from the prior EXP-0190 body-review overlay.
- The 14 callback-sized functions range from 96 to 138 bytes. Raw x86 shows VM-frame value decoding, optional `0x41` marker handling through the helper pointer at `0x014069F4`, and a receiver virtual call. Several bodies decode one value; others decode two values or a value plus a float. The observed vtable displacements range from `+0x1AC` to `+0x1E8`.
- The six larger anchors range from 58 to 521 bytes. Their bodies also decode VM-frame arguments and dispatch through receiver virtual slots. `0x005D3AB0` stores a returned value through an output pointer; `0x005D9F90` stages five argument groups; `0x009EC3E0` contains multiple table-dispatched values, a seven-DWORD aggregate-copy path, and accesses to globals `0x0140A920` and `0x0140A940`–`0x0140A948`; `0x009ED140` stages five values including a three-DWORD vector-like group. These observations do not establish the semantics suggested by candidate names such as `IsDead`, `SetDesiredRotation`, `TakeDamage_Native`, `PreventDeath_Native`, or `OnNPCEnrage`.
- The evidence CSV records, for every address, its size, RVA, PE file offset, raw-body SHA-256, candidate UELib object path, observed argument/call shape, vtable displacement, and analysis toolchain. Same-slot observations (including `+0x1B4`, `+0x1E8`, and `+0x1CC`) are not sufficient to infer a shared method or owner.
- The cumulative manual body-review overlay rises from 60 to 80 unique functions, or 0.110441% of the full index. The EXP-0139 subset rises from 31/254 to 51/254 reviewed, leaving 203 without body review. All 254 remain subsystem-unassigned. This pass adds zero confirmed semantic claims and zero runtime-verified functions.

## Interpretation and claim limits

- **Observed:** the indexed bytes contain the VM-frame decoding, optional marker, output-storage, and virtual-call operations summarized in the evidence CSV. Each raw hash is tied to the registered executable and indexed range.
- **Inferred, limited:** the repeated frame-decoding patterns are consistent with native-exec adapter/wrapper code. Declaration arity and low-level argument shape can prioritize follow-up, but they cannot confirm that the candidate export owns the receiver or slot.
- **Unknown:** concrete class/vtable ownership, the meaning of each slot, argument semantics beyond directly visible width/register/stack flow, native-table consumption, runtime reachability, and higher-level gameplay effects.
- **Not established:** the method names in EXP-0139, data-pointer references, matching arity, or repeated slot displacement do not prove runtime dispatch or semantic equivalence.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify `Dishonored RHCP/Binaries/Win32/Dishonored.exe` has the SHA-256 above.
2. For each evidence row, resolve its address and size in `research/executable/functions.csv`; map `RVA = VA - 0x00400000` through the PE section table and read exactly the recorded number of bytes.
3. Verify the row's raw-body SHA-256 and disassemble its full range with Capstone `CS_ARCH_X86` / `CS_MODE_32`.
4. Filter the EXP-0139 candidate catalog by address to recover the linked export/declaration. Preserve it as a candidate association.
5. Verify the cumulative output contains 80 unique addresses and that the 20 reviewed addresses were absent from EXP-0190.

The Ghidra project was locked by another active process during these reviews. No Headless decompilation was attempted, and no Ghidra project, lock, or game process was changed. The recorded analysis used read-only raw PE bytes. No runtime experiment was performed. The EXP-0139 class-table/name associations are candidates and do not prove how or whether the game consumes those pointers.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Candidate catalog and limits: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior review batch: [EXP-0190](EXP-0190-multiplicity-two-class-table-wrapper-review.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
