---
id: EXP-0146
title: Shared state-exit callback native-exec handler
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the four exact class-table exports, class hierarchy rows, and body of the state-exit callback target at 0x009E47A0 establish?"
---

# EXP-0146 — Shared state-exit callback native-exec handler

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the four-edge EXP-0139 target `0x009E47A0`; compare exact function exports, read-only body/dataflow, and serialized class/function `Super` catalog rows.
- Exclusions: no identity assigned to vtable displacement `+0x1A8`; no semantic interpretation of callback suffixes; no runtime dispatch or gameplay claim; no function-override relation inferred where no exact `UFunction.Super` row exists.
- Inputs: EXP-0139 class-table/UELib join and target catalog; EXP-0071 all-install inheritance catalog; exact-build function index and read-only decompiler output.
- Durable outputs: [one-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0146.csv), [36-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0146.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0146.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Resolve all four EXP-0139 rows for `0x009E47A0`; compare exact export declarations, NativeFlag, NativeToken, script size, and source provenance.
3. Resolve the indexed body and inspect its read-only decompilation plus raw `.text` bytes. Trace the decoded argument to the indirect call without naming the receiver slot.
4. Resolve each class's `UClass.Super` chain through its first common parent. Separately query exact target methods for `UFunction.Super` rows; do not substitute a class relation for a method relation.
5. Add the address as an L1 static-role candidate and leave runtime status and subsystem unknown.

## Observations

- The exact-build function index identifies `FUN_009e47a0` at `0x009E47A0`, size 96 bytes, in `.text`. The read-only decompiler cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `845ED930CBE38B048952084345E2F2C9C7BB4557088622789BAB058395E61AEE`.
- Four EXP-0139 raw class-table edges from registration function `0x00A0DBF0` point to this target. Every matched export is `NativeFlag=true`, `NativeToken=0`, script size 7, and declares one `DishonoredNativeState` object parameter. The exact method names are `RequestStateExitCallback_GenericAction` (two edges), `RequestStateExitCallback_TakeActorPosition`, and `RequestStateExitCallback_TakePosition`.
- The four source JSONL rows are 210, 237, 240, and 914, all in the source file with SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`; package source/hash provenance is preserved in EXP-0139.
- The EXP-0071 UELib catalog records class Super chains for all four classes. `DisBehaviorMagicResponse`, `DisBehaviorRatStomp`, and `DisBehaviorReturnTravel` each point to `DisAIBehaviorWithDesires`, whose Super is `DishonoredAIBehavior`; `DisDLC06BehaviorSummonedAssassinIdle` points directly to `DishonoredAIBehavior`. The four class rows are catalog lines 254, 266, 268, and 1982. Catalog SHA-256: `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The EXP-0071 catalog contains no `UFunction.Super` row for any of the four exact target method paths. This is absence from the derived relation catalog, not proof that the methods have no superclass relation.
- The decompiler shows a frame opcode selecting a decoder through `DAT_014068F0`, writes the decoded dword to a local, conditionally handles the `A` marker through `DAT_014069F4`, then calls the receiver vtable displacement `+0x1A8` with that dword. Raw disassembly confirms the decoded local is pushed as the sole explicit call argument.
- The exact 96-byte raw `.text` range has SHA-256 `51463C62F1E938436D868F06CA5C3318D707EB5C6E8F2FFA0881718CAF0B784B`. The function ends with `ret 8` at `0x009E47FD`.
- The address was subsystem-unknown and absent from the EXP-0145 overlay. This addition creates one L1 review only; it adds no confirmed semantic claim, inter-function L3 edge, or runtime record.

## Interpretation and claim limits

- **Observed:** four exact class-table edges target one indexed body. Their exports share native/token-zero status, script size 7, and a one-object `DishonoredNativeState` declaration while using three callback suffixes.
- **Observed:** the four class Super chains converge on `DishonoredAIBehavior`; three pass through `DisAIBehaviorWithDesires`. No exact target-method `UFunction.Super` row is present for the four functions.
- **Observed:** the body decodes one value, conditionally processes an `A` marker, and passes that decoded value to the indirect call at `+0x1A8`.
- **Inferred, limited:** the target is a shared native-exec adapter candidate for the four class-table callback exports. The exact export joins, declared object argument, and body shape support this candidate role.
- **Unknown:** the virtual member at `+0x1A8`, which concrete behaviors implement it, the meaning of each callback suffix, runtime reachability, and gameplay effect.
- **Not established:** common class ancestry and a shared table target do not prove that the four exact methods override one shared UFunction or produce the same behavior. No exact UFunction.Super chain or runtime observation was found for these four methods.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select the four rows at `0x009E47A0`.
2. Resolve the address in the 10256413 function index and verify the decompiler cache build ID and executable SHA.
3. Rebuild EXP-0071's inheritance catalog; trace the four exact class paths through `UClass.Super`, then query the four exact function paths separately in `UFunction.Super` rows.
4. Map `0x009E47A0` into the exact executable's `.text` section using `RVA = VA - ImageBase`, read 96 bytes, verify the recorded SHA, and disassemble with Capstone 5.0.7.
5. Verify the cumulative manual overlay contains 36 unique indexed addresses and includes `009E47A0`.

Class and function Super rows derive from the same UELib corpus and are not an independent parser validation. Static table relations and code do not establish runtime use. No game launch or runtime test was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior target reviews: [EXP-0144](EXP-0144-navmesh-goal-recycle-thunk.md), [EXP-0145](EXP-0145-seqvar-getobjectvalue-thunk.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
