---
id: EXP-0190
title: Eleven multiplicity-two class-table targets receive raw-body review
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What body-level evidence is available for the 11 unreviewed EXP-0139 targets with two class/method name edges each?"
---

# EXP-0190 — Eleven multiplicity-two class-table targets receive raw-body review

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: review the 11 still-unreviewed exact function starts in the EXP-0139 class-table target catalog that each have two name/target edges; map their indexed byte ranges to the registered PE and inspect every indexed byte as x86-32.
- Exclusions: no class ownership, method identity, native dispatch, semantic role, subsystem, dataflow, or runtime claim is confirmed by this review. EXP-0139 name/export joins remain candidates. Vtable byte displacements are recorded as call-site observations only.
- Inputs: exact-build executable, `research/executable/functions.csv`, EXP-0139 candidate catalog, prior 49-row cumulative manual review overlay.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7. Raw code hashes are primary body identifiers.
- Durable outputs: [11-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0190.csv), [60-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0190.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0190.json). The summary records SHA-256 hashes for the prior cumulative overlay and both outputs.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the local executable's SHA-256 against build 10256413.
2. Select the 11 addresses from EXP-0139 that have two pointer/name edges and are absent from the EXP-0159 cumulative body-review overlay.
3. Resolve each exact start and size in the function index, map VA to RVA and raw PE file offset, hash the indexed byte range, then disassemble all bytes as 32-bit x86.
4. Record only directly visible frame-cursor, direct-call, virtual-call, output-storage, and return behavior. Keep linked class/method names explicitly candidate-only.
5. Add the 11 observations to the manual body-review overlay. Preserve unknown subsystem and runtime status, and do not increase semantic-claim counts.

## Observations

- The local executable hash matches the registered build. All 11 addresses are exact starts in the 72,437-row internal function index; their indexed sizes range from 53 to 168 bytes. Each corresponding EXP-0139 catalog row has two class/method name edges.
- Raw x86 shows VM-frame cursor use at `[frame+0x18]` in all 11 bodies. All 11 conditionally consume byte `0x41` and call the helper pointer at `0x014069F4`; four additionally read a byte-indexed helper from the table based at `0x014068F0` to decode a local dword. Ten finish with a receiver virtual call, while `0x005D9980` makes a direct call to `FUN_00781340`; `0x00434270` also calls `FUN_00430BF0` for cleanup. These are local instruction facts, not proof of a particular UnrealScript dispatch path.
- The class/method names joined in EXP-0139 remain unresolved candidate labels. In particular, `0x00434270` has a substantially different body from the small wrappers, and `0x009E5240` joins the unrelated-looking labels `DisDLC06Gadget_ArcMinePlaced.BaseChange` and `GameCrowdDestinationQueuePoint.ActuallyAdvance`; neither association is resolved here.
- The 11 raw indexed-body SHA-256 values, PE offsets, linked candidate paths, and observed call shapes are recorded row by row in the body-review CSV. The current EXP-0139 candidate set contains 254 unique indexed targets. Its body-reviewed count rises from 20 to 31; 223 remain without body review in that candidate set.
- The inherited EXP-0159 cumulative CSV contains one row (`0046E5C0`) with unquoted commas that shift fields for a standard CSV reader. The EXP-0190 cumulative derivative repairs that row's `static_role_candidate` and `relevant_callsites` field boundaries from the serialized content; it preserves the address, size, review status, and claim status. EXP-0159's source file is unchanged. The prior file hash is recorded in the EXP-0190 summary.
- The cumulative manual body-review overlay rises from 49 to 60 unique internal function addresses, or 0.082831% of the 72,437-function index. This is a body-analysis count, not a count of functions semantically understood. This experiment adds zero confirmed semantic claims and zero runtime-verified functions; the reviewed targets remain subsystem-unknown.

## Interpretation and claim limits

- **Observed:** each indexed byte range contains the x86 operations summarized in its evidence row, tied to the exact executable hash and function-index size.
- **Inferred, limited:** many of these bodies are consistent with a shared VM-frame adapter/wrapper family. Their different decode paths, output handling, direct/virtual call forms, and vtable displacements require per-function review; family resemblance does not prove interchangeable behavior.
- **Unknown:** whether the EXP-0139 class-table/name associations are runtime dispatch entries; the concrete receiver owners and virtual methods; decoded-value types; higher-level behavior; subsystem; and runtime reachability.
- **Not established:** shared frame handling, a repeated slot displacement, or a two-row name/address join does not confirm a method name, ownership, common implementation, or semantic equivalence.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify `Dishonored RHCP/Binaries/Win32/Dishonored.exe` has the SHA-256 above.
2. For each evidence row, resolve `address` and `size_bytes` in `research/executable/functions.csv`; with PE image base `0x00400000`, map `RVA = VA - ImageBase` through the PE section table and read exactly `size_bytes` from `file_offset`.
3. Verify each raw range SHA-256 and disassemble the full range with Capstone `CS_ARCH_X86` / `CS_MODE_32`; compare the direct and indirect call shapes with `observed_raw_shape`.
4. Filter `native-class-table-handler-candidates-EXP-0139.csv` by address to recover the original candidate class/method joins. Do not treat those joins as confirmed ownership.
5. Verify the cumulative output contains 60 unique addresses and that the 11 addresses in this experiment were absent from the EXP-0159 cumulative input. Check the input hash in the EXP-0190 summary. The inherited `0046E5C0` row is normalized in the new derivative as described above; the original is retained unchanged.

The Ghidra project was locked by an active process during this pass, so no Headless decompilation was attempted. Raw bytes were read from the exact registered executable; no project, lock, or game state was changed. The local SQLite callgraph mirror was not used as a durable input to this experiment. No runtime experiment was performed. The EXP-0139 census and UELib export joins remain candidate evidence as described in that experiment.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent candidate catalog: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Previous reviewed shared-call shapes: [EXP-0142](EXP-0142-shared-class-table-vtable-call-shapes.md), [EXP-0156](EXP-0156-three-exports-shared-frame-adapter.md), [EXP-0157](EXP-0157-eight-exports-single-value-handler-slot-3a0.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
