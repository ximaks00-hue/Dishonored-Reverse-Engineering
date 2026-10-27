---
id: EXP-0199
title: A high-fanout candidate and two repeated adapter families expand the body review
experiment_status: done
claim_status: mixed
build: "10256413"
question: What directly observable body and call-pattern differences distinguish a high-fanout EXP-0139 candidate from two repeated indexed-table body families?
---

# EXP-0199 — A high-fanout candidate and two repeated adapter families expand the body review

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [the registered build](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: six unreviewed exact-build starts from the EXP-0139 candidate set, selected for one high direct-call outlier and two repeated normalized-body families.
- Exclusions: EXP-0139 class/method names are cross-source candidates. Neither these labels, repeated body shapes, absolute pointer cells, nor call edges establish source-level method identity, owner, runtime reachability, or behavior. All six records remain L1 body reviews.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE bytes and exact-build function index.
- Baseline: the EXP-0198 cumulative overlay held 206 unique reviewed bodies; all six selected addresses were absent.

## Procedure

1. Recompute the executable SHA-256 and compare it with the build record.
2. Resolve each address to an exact start and inclusive size in `functions.csv`; reject any address already in the EXP-0198 cumulative overlay.
3. Hash and fully decode each indexed byte range as x86-32. Record direct calls, indirect calls, absolute-memory operands, and reads from indexed base `0x014068F0`.
4. For each target, join the EXP-0139 pointer catalog by raw handler target VA; independently read the candidate `.data` slot as a little-endian DWORD and compare it with the function VA.
5. Normalize only Capstone-marked immediate and displacement encoding bytes and compare the resulting hashes. Record all results as L1 analysis with unknown subsystem and runtime status.

## Observations

- All six addresses are exact indexed starts, absent from EXP-0198, and fully decoded; indexed body sizes range from 138 to 472 bytes. Every body uses an indirect call through `[0x014069F4]`. Six raw `.data` handler slots were read independently and each DWORD equals its target VA.
- `00512A80` is 472 bytes and contains nine immediate direct calls to five distinct target addresses, plus one call through `[0x014069F4]`. It has no indexed read from `0x014068F0`. The absolute-memory operands include reads from `[0x013B49A8]` and `[0x014417E8]`, as well as accesses to `fs:[0]`; their roles are not identified here.
- `005CE3F0`, `005D0680`, and `009E4710` are 138-byte bodies with the same normalized SHA-256 `73E33D1370CA638B6F118877B4424438567B2E60D76289E9F425C1CAF6E570B`. Each has two indexed reads from `[EDX*4 + 0x014068F0]`, register-indirect calls at the corresponding points, one indirect call through `[0x014069F4]`, and no immediate direct call. Their raw body hashes differ.
- `005C4000` and `005D1430` are 223-byte bodies with the same normalized SHA-256 `7AC0CA0F36688B7A8E236BD54D392F6F6B443620F3EEBC2D444AC61695CA1081`; their raw hashes differ. Each has two indexed reads from `[EDX*4 + 0x014068F0]`, an indirect call through `[0x014069F4]`, and other register-indirect calls. Both write and read `0x0140A940`, read `0x0140A944` and `0x0140A920`; target displacements differ between the bodies.
- The EXP-0139 set rises from 127 to 133 of 254 body-reviewed targets, leaving 121 unreviewed. The cumulative manual overlay rises from 206 to 212 unique bodies, or 0.292668% of the 72,437-function index. No semantic or runtime claims are added.

## Interpretation and claim limits

- **Observed:** six exact-build bodies were fully decoded and hashed; all six call indirectly through `[0x014069F4]` and all six candidate `.data` slots contain their corresponding function VA.
- **Observed:** the three 138-byte bodies share one normalized byte sequence, and the two 223-byte bodies share another. The normalization masks only Capstone immediate/displacement encoding bytes; it does not make raw bodies identical.
- **Observed:** `00512A80` has nine direct call instructions, a higher count than the other five selected bodies, which have no immediate direct-call targets.
- **Inferred, limited:** the repeated sequences are useful structural clusters for future comparison. The 223-byte pair's repeated absolute-address accesses and differing call displacements may help discriminate its internal dataflow, but object/member meanings remain unknown.
- **Unknown:** names/owners of the six implementations, meaning of the indexed selector and table, semantics of `0x014069F4`, globals, vtable-like calls, and runtime reachability.
- **Not established:** a cross-source candidate name, direct call, matching data pointer, or normalized sequence proves a method's semantics or game behavior.

## Reproduction and limitations

With Python, pefile, and Capstone installed:

1. Verify the registered executable SHA-256 and inclusive function ranges.
2. Recompute raw body hashes and verify decoded instruction sizes cover each complete range.
3. Recreate normalized hashes by zeroing only Capstone-marked immediate and displacement bytes.
4. Map each EXP-0139 `handler_pointer_slot_va` through the PE image and compare its raw DWORD with the target VA.
5. Verify the addresses are absent from EXP-0198 and present once in the cumulative EXP-0199 overlay.

This was read-only static analysis; no Ghidra project or game process was used.

## Links

- Candidate provenance: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior overlay: [EXP-0198](EXP-0198-exp0139-indexed-table-adapter-family-expansion.md)
- Body evidence: [EXP-0199 overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0199.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0199.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0199.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
