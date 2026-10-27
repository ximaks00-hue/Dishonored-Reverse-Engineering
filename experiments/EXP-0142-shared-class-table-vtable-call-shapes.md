---
id: EXP-0142
title: Two shared class-table targets with zero- and one-argument virtual-call shapes
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What repeated call shape is supported for the next two highest-connectivity indexed targets in the EXP-0139 candidate catalog?"
---

# EXP-0142 — Two shared class-table targets with zero- and one-argument virtual-call shapes

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the next two highest-connectivity indexed EXP-0139 targets after `0x005C1640`: `0x005C26E0` (8 export edges) and `0x009F5450` (8 export edges); compare their decompiler call shapes to all 16 exact UELib exports.
- Exclusions: no naming or semantic assignment to virtual slot `+0x3A0`, no concrete class ownership, no table extent/consumer proof, and no runtime execution. The shared target does not prove that the classes share behavior or implementation ownership.
- Inputs: EXP-0139 raw-name/export join and target catalog; exact-build function index and read-only decompiler output; UELib function-census records with source/package hashes recorded in EXP-0139.
- Durable outputs: [two-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0142.csv), [31-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0142.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0142.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; require the recorded build 10256413 and executable hash.
2. Select the next two addresses after `0x005C1640` with the highest EXP-0139 target-edge multiplicity. Resolve index rows and exact read-only decompiler output for both.
3. For all 16 EXP-0139 rows targeting those addresses, compare the class/method name, exact UELib object path, `NativeFlag`, token, script size, and declaration.
4. Inspect frame/code pointer operations, decode-callback calls, optional-parameter marker handling, and final indirect call in each body. Record slot displacement and supplied arguments as observed facts; leave slot/type/owner unknown.
5. Add both addresses to the manual body-review overlay as L1 static-role candidates only. Preserve the EXP-0072 baseline and runtime count.

## Observations

- `0x005C26E0` is an indexed 63-byte function (`FUN_005c26e0`) and has eight EXP-0139 target edges. All eight UELib exports are `NativeFlag=true`, `NativeToken=0`, script size 2, and declare zero explicit parameters. Export names are `SetShadowParentOnAllAttachedComponents`, `DoInitRBPhys` (six class paths), and `Term`.
- `0x009F5450` is an indexed 117-byte function (`FUN_009f5450`) and has eight EXP-0139 target edges. All eight UELib exports are `NativeFlag=true`, `NativeToken=0`, script size 7, and declare one object parameter. The exports include `OnToggle`, `OnToggle_Native`, `OnActivateRatSpawner`, and `AddAIGroupActor`; parameter classes differ (`SeqAct_Toggle`, `DisSeqAct_ActivateRatSpawner`, and `InterpGroupInstAI`).
- Both decompiler bodies advance the bytecode pointer and conditionally consume an `'A'` marker through `DAT_014069F4`.
- `FUN_005c26e0` then calls indirectly through the receiver vtable at byte displacement `+0x3A0` with no explicit decoded argument.
- `FUN_009f5450` first reads one opcode byte, advances the frame code pointer, calls a decoder from `DAT_014068F0` into a local dword, then invokes the receiver vtable at `+0x3A0` with that dword.
- Pseudocode SHA-256 values: `FUN_005c26e0` — `61103142D6341D75D3FF36A12DC17B7A2012329325F8B224ABE768F5CBBF3153`; `FUN_009f5450` — `C6BB66D4946FFE49DFBE44C2EE9DE45959C364DF1BB0AE9F03D4AD7C4CACAA8E`. Both decompile cache records name build 10256413 and the exact executable SHA above.
- Both addresses were in EXP-0072's unknown subsystem bucket and were absent from the prior EXP-0140 manual review. The new rows add two L1 body reviews, no confirmed semantic claims, no L3 edges, and no runtime records.

## Interpretation and claim limits

- **Observed:** the 16 exact class-table/export joins divide into two body shapes at these targets: zero explicit decoded values and one decoded dword, respectively. Both bodies end in a receiver virtual call at the same vtable byte displacement `+0x3A0`.
- **Inferred, limited:** the targets are shared native-exec adapter candidates that decode their declared script arguments and route to a class receiver virtual call. Exact table names, matching UELib declarations, common target addresses, and the code shape support this grouping.
- **Unknown:** which virtual methods occupy `+0x3A0` in any concrete receiver vtable, whether the same member signature exists across these classes, how the one decoded dword is interpreted for each declaration, and whether these static paths execute at runtime.
- **Not established:** the coincident vtable displacement does not prove that the classes share one method, common implementation, or subsystem. Do not infer helper semantics from method names alone.

## Reproduction and limitations

1. Rebuild EXP-0139 with its recorded UELib census inputs and select target addresses `0x005C26E0` and `0x009F5450`.
2. Decompile both exact-build addresses read-only and compare their pseudocode hashes and operation sequence with this record.
3. Verify the cumulative review overlay contains 31 unique indexed addresses, including these two.

Decompiler locals and source parameter names are not treated as original source. The function index and its 72,437-address denominator are unchanged. Static table relationships and vtable calls do not demonstrate runtime consumption or behavior.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table target join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Raw pointer evidence: [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- Prior shared-target review: [EXP-0140](EXP-0140-shared-native-takedamage-handler.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
