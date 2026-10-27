---
id: EXP-0157
title: Raw-byte rechecks correct shared-handler sizes in the EXP-0142 overlay
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do build-matched raw-byte rechecks support the 63-byte and 117-byte sizes previously recorded for 0x005C26E0 and 0x009F5450, and what body boundaries and local call facts are reproducible?"
---

# EXP-0157 — Raw-byte rechecks correct shared-handler sizes in the EXP-0142 overlay

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: recheck the already-reviewed EXP-0142 targets `0x005C26E0` and `0x009F5450` against the exact-build function index and raw bytes; correct both body sizes in derivative overlays and verify their local return/call boundaries.
- Exclusions: no semantic assignment to vtable displacement `+0x3A0`, no declaration-type decoding, concrete owner, runtime dispatch, reachability, or gameplay claim. Shared target/name joins do not prove a common implementation owner.
- Inputs: EXP-0139 raw name/target/UELib join; exact-build index and executable; UELib JSONL source snapshots; local decompilation cache; prior EXP-0142 review overlay.
- Durable outputs: corrected [EXP-0142 manual review row](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0142.csv) and corrected cumulative overlays from EXP-0142 through EXP-0156. This is a correction and stronger body evidence, not an additional unique function review.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build ID and EXE SHA-256.
2. Select all EXP-0139 join rows whose raw handler targets are `0x005C26E0` and `0x009F5450`; compare object path, owner, exec name, declaration, NativeFlag, NativeToken, script size, and JSONL provenance.
3. Verify both function starts and sizes in the exact-build index, map VAs through the PE section table, hash the indexed byte ranges, and disassemble as x86-32.
4. Compare the call boundary of `0x009F5450` with `0x009F53F0` from EXP-0156. Record raw register/stack effects and slot displacement, but do not infer a shared virtual method or decoded type.
5. Correct the two previously transcribed sizes and preserve the existing L1 review count, unknown subsystem and zero runtime count.

## Observations

- Eight EXP-0139 edges target indexed start `0x009F5450` (`FUN_009f5450`, 96 bytes). Five declarations use `SeqAct_Toggle`, one uses `DisSeqAct_ActivateRatSpawner`, one uses `InterpGroupInstAI`, and one uses `SeqAct_Toggle` on `NavMeshBlockToggleable`. Export paths are across `DishonoredGame.upk` and `Engine.upk`; all eight have NativeFlag=true, NativeToken=0, and script size 7.
- EXP-0142 and the prior overlay transcribed this function as 117 bytes. The exact-build function index and raw code end at `0x009F54AF`, inclusive, giving a 96-byte body; this experiment corrects that size in the original addition and all cumulative overlays through EXP-0156. The function was already among the 48 unique reviewed addresses, so the review denominator does not increase.
- EXP-0142 and the prior overlay transcribed `0x005C26E0` as 63 bytes. Its exact-build indexed range is 53 bytes, from `0x005C26E0` through the final byte at `0x005C2714`; raw x86 ends with `ret 8` at `0x005C2712`, followed by ten `0xCC` bytes at `0x005C2715`–`0x005C271E` in the larger 63-byte range. The indexed 53-byte body SHA-256 is `B6618C4AF627DC63CC07B08946B3C7DE00213C9AF341BA89CD1059EBE851E888`. The correction applies to its EXP-0142 addition and cumulative overlays through EXP-0156.
- The exact local EXE SHA-256 matches the registered build. PE mapping gives VA `0x009F5450`, RVA `0x005F5450`, file offset `0x005F4850`, section `.text`. The 96-byte range SHA-256 is `ED310C758C4C276CFBB200AFB430E5D8ECBD796416E7405F58C445B3751B0C2F`.
- Raw x86 initializes a local dword to zero, reads a byte through the frame cursor at `[frame+0x18]`, advances the cursor and indexes a function-pointer table based at `0x014068F0`. That helper receives the frame and address of the local dword. The body then advances the cursor by one byte; if the next byte is `0x41` (`'A'`), it consumes it and calls the pointer at `0x014069F4` with the frame and zero.
- At the final call, raw x86 loads a pointer from the incoming receiver's vtable at byte displacement `+0x3A0`, places the local dword on the stack, restores the receiver to ECX, and calls indirectly. The function returns with `ret 8`.
- The EXP-0139 join has eight exact raw `.data` name/adjacent handler-pointer rows, each linked to one UELib function export. The join itself records dispatch as unproved. The two relevant JSONL source hashes are `47760EFCB17CBDBFFBF76A58746EBDF20743135A85BC7A6B8BE0F09F0D13B56B` for `Engine.upk` and `09F41841F403B8A1CAE11E11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4` for `DishonoredGame.upk`; package source hashes are preserved per EXP-0139 row.
- Relative to `0x009F53F0` (EXP-0156), the observed local frame decoding sequence is similar, but the final receiver vtable displacement differs: `+0x3A0` here versus `+0x3AC` at `0x009F53F0`. This comparison does not identify either slot's method.
- The build-scoped cache entry records build ID and executable SHA but not Ghidra version/options or analysis-project revision. The body hash and raw machine-code inspection are primary; pseudocode is secondary.
- The EXP-0156 cumulative overlay already contains `009F5450`; this recheck corrects its recorded size and does not add a new unique address.
- The EXP-0156 cumulative overlay already contains `005C26E0`; this recheck corrects its recorded size and does not add a new unique address.

## Interpretation and claim limits

- **Observed:** eight exact class-table name/target joins resolve to this indexed function, and their UELib exports are NativeFlag=true, token-zero declarations with one declared parameter each.
- **Observed:** `0x005C26E0` is a 53-byte indexed function ending with `ret 8` at `0x005C2712`–`0x005C2714`; the ten following `0xCC` bytes are outside that function body.
- **Observed:** raw x86 reads one bytecode value through a table-driven helper, optionally consumes an `A` marker through a separate helper, then passes a local dword to the receiver's vtable entry at byte displacement `+0x3A0`.
- **Inferred, limited:** this remains the shared one-value native-exec frame-handler candidate recorded in EXP-0142 for the eight joined exports; this experiment verifies its body range and raw call shape. Runtime dispatch and concrete receiver semantics are not demonstrated.
- **Observed comparison:** `0x009F5450` and `0x009F53F0` have a similar local decoder/marker/call shape but use different receiver vtable displacements (`+0x3A0` and `+0x3AC`).
- **Unknown:** the decoded value's type and meaning; decoder-table semantics; marker semantics; the meaning of either vtable slot; concrete owner/method implementations; whether any edge executes; and any higher-level behavior.
- **Not established:** shared call shape does not prove identical method signatures, class ownership, behavioral equivalence, or runtime reachability.

## Reproduction and limitations

1. Filter `research/executable/evidence/EXP-0139-native-class-table-uelib-zero-token-join.csv` by raw handler targets `0x005C26E0` and `0x009F5450`; compare their 8+8 rows and source hashes/JSONL lines.
2. Verify executable SHA, find both function index rows, map their VAs to RVAs/raw offsets, and hash 53 bytes from `0x005C26E0` and 96 bytes from `0x009F5450`.
3. Disassemble both ranges as x86-32; verify the `ret 8` at the indexed end of `0x005C26E0`, its following ten `0xCC` bytes, and the frame decoding/marker/vtable/receiver/argument sequence of `0x009F5450`.
4. Compare only the raw final-call displacement with EXP-0156. Verify all cumulative overlays from EXP-0142 through EXP-0156 report 53 bytes for `005C26E0`, 96 bytes for `009F5450`, and preserve 48 unique addresses.

UELib JSONL inputs and decompilation cache are local/ignored. Their provenance is partially recorded in EXP-0139 and the build identity; cache analyzer/project provenance remains incomplete. No game launch or runtime experiment was performed. Raw body inspection establishes only local machine-code effects.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Related body shape: [EXP-0156](EXP-0156-three-exports-shared-frame-adapter.md)
- Earlier handler shape comparison: [EXP-0142](EXP-0142-shared-class-table-vtable-call-shapes.md)
