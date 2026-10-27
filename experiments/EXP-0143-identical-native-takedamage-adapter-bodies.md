---
id: EXP-0143
title: Shared native TakeDamage adapter bytes with adjacent virtual slots
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do the remaining high-connectivity TakeDamage_Native class-table targets share a body shape, and which byte-level distinctions are established?"
---

# EXP-0143 — Shared native TakeDamage adapter bytes with adjacent virtual slots

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the next highest-connectivity unreviewed EXP-0139 class-table target, `0x009F63A0`, plus the related three-edge `0x009ED230` target; compare exact exports, indexed ranges, cached pseudocode, and raw `.text` bytes.
- Exclusions: no identity assigned to virtual slots `+0x3A0` or `+0x3A8`, no concrete receiver/vtable ownership, no runtime dispatch claim, and no assertion that all classes have the same implementation semantics.
- Inputs: EXP-0139 class-table/UELib join and 254-address catalog; exact-build function index; read-only decompiler cache records for both targets.
- Durable outputs: [two-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0143.csv), [33-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0143.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0143.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select the highest-connectivity unreviewed indexed target in EXP-0139 and inspect its exact class/table edges. Include the smaller target only where the join exposes a discriminating comparison.
3. Resolve both target ranges in the exact-build function index. Read cached decompiler output and verify each cache record's build ID and executable SHA.
4. Compare each raw UELib export's class/method path, NativeFlag, NativeToken, script size, and declaration. Preserve the source JSONL hash and line references in the EXP-0139 join.
5. Map each indexed VA to its `.text` raw-file offset using the PE image base and section table. Compare the full indexed byte ranges and disassemble the differing instruction neighborhood with Capstone 5.0.7.
6. Add both addresses as L1 static native-exec role candidates. Leave slot identity, class ownership, runtime reachability, and subsystem assignment unresolved.

## Observations

- The exact-build index identifies `FUN_009f63a0` at `0x009F63A0`, size 445 bytes, and `FUN_009ed230` at `0x009ED230`, size 445 bytes. Both are indexed starts in `.text`.
- Seven EXP-0139 edges point to `0x009F63A0` and three point to `0x009ED230`; all ten are registered through `0x00A0DBF0`. Every matching UELib export is `NativeFlag=true`, `NativeToken=0`, script size 39, and declares `TakeDamage_Native(int, Controller, Vector, Vector, Class<DamageType>, optional TraceHitInfo, optional Actor)`.
- The source UELib JSONL SHA-256 is `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`. The seven first-target rows are lines 282, 284, 400, 826, 828, 866, and 942; the three second-target rows are lines 3, 863, and 939. All are in the EXP-0139 join output.
- Both read-only decompiler cache records state build `10256413` and the exact executable SHA above. Their pseudocode hashes are `BC04CC68761978A930D0D6C06E8F386BC53264E7B22753E1EB0FDF6B02C70E86` (`0x009F63A0`) and `29E766B6079D4DB06F6A30D9A49B2B34320879A29EEF9618355754A680B6C98D` (`0x009ED230`). After replacing function-specific PC literals with function-relative offsets and normalizing generated function labels, the only pseudocode difference is the final virtual-call displacement `+0x3A0` versus `+0x3A8`.
- Both decompiler bodies read and advance the frame code pointer, dispatch multiple parameter decoders through `DAT_014068F0`, handle the optional `A` marker through `DAT_014069F4`, and end in a receiver vtable call. The decompiler shows displacement `+0x3A0` for `0x009F63A0` and `+0x3A8` for `0x009ED230`.
- Raw `.text` byte ranges of 445 bytes each have SHA-256 `E0DAB5069EBDFA6921E3964520DB30A84A4806F6BC7AE4A8675370440F6223B8` (`0x009F63A0`) and `302692AC7CD45AF3703B0ED85455445DFAED6F048AC45545F01C734A86F0C1EF` (`0x009ED230`). The ranges are equal at 444 of 445 byte offsets; the only difference is byte offset `0x167`, `A0` versus `A8`.
- Capstone decodes that differing instruction as `mov edx, dword ptr [edx + 0x3a0]` at `0x009F6505` and `mov edx, dword ptr [edx + 0x3a8]` at `0x009ED395`. The adjacent instruction bytes are identical.
- Both addresses were subsystem-unknown and absent from the previous manual overlay. The two new rows add L1 body reviews only; there are no confirmed semantic claims, L3 dataflow edges, or runtime records.

## Interpretation and claim limits

- **Observed:** ten exact class-table/export edges point to two indexed 445-byte targets. Their declarations agree exactly; their decompiler pseudocode agrees after normalizing address-specific values except for the final virtual-call displacement, and raw machine code differs at exactly one byte inside the indexed ranges.
- **Observed:** the single differing byte changes the receiver-vtable displacement from `+0x3A0` to `+0x3A8` in the decoded instruction. This is a static code distinction, not a recovered slot name or owner.
- **Inferred, limited:** the targets are native-exec argument-decoding adapter candidates for the matched `TakeDamage_Native` declarations. Exact class-table joins, export metadata, and body shape support the candidate role.
- **Unknown:** the concrete virtual members, vtable owners/layouts, meaning and runtime use of decoded arguments, and whether any class-table edge is executed in a game session.
- **Not established:** shared native-exec call shape does not prove shared gameplay behavior, class inheritance, virtual override ownership, or identical downstream effects.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and target catalog from its recorded UELib JSONL inputs.
2. Resolve `0x009F63A0` and `0x009ED230` in the 10256413 function index and retrieve read-only decompiler cache records. Verify each record's build ID and EXE SHA before comparing.
3. For each VA, compute `RVA = VA - ImageBase`, map the RVA into the containing PE section using its section virtual address and raw-file pointer, then read the indexed 445-byte range. Compare the ranges bytewise and hash each byte sequence with SHA-256.
4. Disassemble from offsets `0x15B` through `0x17B` in each range using Capstone 5.0.7. The differing byte is at range offset `0x167`, inside the six-byte displacement operand shown above.
5. Verify the cumulative review overlay has 33 unique indexed addresses and includes both targets.

The executable remains unmodified. Decompiler pseudocode is not original source. EXP-0139 table relations and raw code establish static properties only; no runtime test was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior TakeDamage executor review: [EXP-0140](EXP-0140-shared-native-takedamage-handler.md)
- Prior repeated target call shapes: [EXP-0142](EXP-0142-shared-class-table-vtable-call-shapes.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
