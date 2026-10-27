---
id: EXP-0148
title: Paired one-argument state-exit adapters with adjacent virtual slots
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do the class-table targets at 0x009F6150 and 0x009F5750 form a byte-matched one-argument state-exit adapter pair, and what do their exact exports and class paths establish?"
---

# EXP-0148 — Paired one-argument state-exit adapters with adjacent virtual slots

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: compare two previously unreviewed exact class-table targets, `0x009F6150` and `0x009F5750`, against the EXP-0139 export join, UELib class Super catalog, exact-build function index, read-only decompilation cache, and raw executable bytes.
- Exclusions: no virtual slot names or callback semantics assigned; no exact UFunction override, runtime dispatch, or gameplay behavior inferred from class inheritance or static table joins.
- Inputs: EXP-0139 class-table/UELib join and target catalog; EXP-0071 UELib class inheritance catalog; exact-build function index and Ghidra read-only decompilation cache.
- Durable outputs: [two-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0148.csv), [39-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0148.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0148.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and the executable SHA-256.
2. Select raw EXP-0139 edges at the two target addresses; compare exact export declarations, native flags/tokens, script sizes, source rows, and package/source hashes.
3. Resolve each address and size in the exact-build function index; verify each read-only decompilation cache record names the same build and executable hash.
4. Map each VA to the `.text` section using the PE32 image base and section table; hash the 96-byte indexed ranges and compare them bytewise.
5. Resolve each exact export owner's `UClass.Super` chain from EXP-0071. Treat class ancestry only as class metadata, not proof of callback method override or shared runtime behavior.
6. Add both addresses as inferred L1 adapter candidates; leave semantic, dataflow, and runtime evidence unchanged.

## Observations

- The executable hash is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; PE32 image base is `0x00400000`. Both indexed ranges are in `.text` and have size 96 bytes.
- The read-only decompilation records for `0x009F6150` and `0x009F5750` both name build `10256413` and the exact executable SHA above. Their pseudocode SHA-256 values are `BB2D946D4837F2C05FE3D5CDCA4FCFCF262FDA3DE79F8CF298D7C306C6738A21` and `3B4B6A92D97AEA9959F8FB1356F94EE4449F8142B98201DB000E81824BD3E06B`.
- Three raw EXP-0139 edges target `0x009F6150`: `DisBehaviorEscapeExplosion.RequestStateExitCallback_GenericAction`, `DisBehaviorInteract.OnExitCallback_Stand`, and `DisBehaviorCombatRatSwarm.RequestStateExitCallback_TakeActorPosition`.
- Three raw EXP-0139 edges target `0x009F5750`: `DisBehaviorGoHome.RequestStateExitCallback_GenericAction`, `DisBehaviorEnemyUnreachable.RequestStateExitCallback_GenericAction`, and `DisDLC07BehaviorAssassinVsRiverKrustCombat.RequestStateExitCallback_TakePosition`.
- All six exports are `NativeFlag=true`, `NativeToken=0`, script size 7, and declare one `DishonoredNativeState` object argument. Their source JSONL rows are 189, 209, 173, 200, 184, and 950 in that target order; all use source SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`.
- The six exact class paths each have a UELib `UClass.Super` chain through `Class'DishonoredGame.DisAIBehaviorWithDesires'` to `Class'DishonoredGame.DishonoredAIBehavior'` in the EXP-0071 catalog (SHA-256 `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`).
- Raw `.text` SHA-256 values are `2A54F35B96306FDB92E2F9816488BDFCE8C84DBD5419574354C8263B9C934B06` for `0x009F6150` and `464E6F35F5BB310B4996782961924082B7E85F1F7F08B2E45D1C44205F371258` for `0x009F5750`. Their 96-byte bodies differ at one offset only: offset `0x4F` is `0xB8` in the first and `0xBC` in the second; the remaining 95 bytes are equal.
- The decompiler identifies the changed receiver vtable displacement as `+0x1B8` for `0x009F6150` and `+0x1BC` for `0x009F5750`. Both bodies select a decoder from the frame byte, decode one dword, conditionally process an `A` marker, and pass that dword as the explicit argument to the indirect receiver call.
- Neither target appeared in the EXP-0147 cumulative overlay. This addition records two L1 reviews only. It adds no confirmed semantic claim, L3 dataflow edge, or runtime record.

## Interpretation and claim limits

- **Observed:** six exact class-table edges, three per target, map to indexed 96-byte native/token-zero targets. Their declarations share a one-object `DishonoredNativeState` parameter.
- **Observed:** all six class Super chains in the UELib catalog converge through `DisAIBehaviorWithDesires` on `DishonoredAIBehavior`.
- **Observed:** the two exact-build machine-code bodies are equal at 95 of 96 bytes; the single differing byte changes the indirect receiver displacement from `+0x1B8` to `+0x1BC`. Both pass one decoded dword to the selected call.
- **Inferred, limited:** the targets are adjacent-slot one-argument native-exec adapter candidates for the six table edges. Exact class-table joins, matching declarations, and byte-level body comparison support this grouping.
- **Unknown:** the virtual members behind either displacement, callback suffix meaning, exact UFunction override relations, runtime reachability, and gameplay effects.
- **Not established:** common class ancestry and shared adapter code do not prove identical callbacks, one common UFunction, or shared runtime behavior.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select its six raw rows for target addresses `0x009F6150` and `0x009F5750`.
2. Resolve both 96-byte functions in `research/executable/functions.csv`; check the corresponding cache JSON build ID and executable SHA.
3. Read both ranges from the exact EXE `.text` section using `RVA = VA - 0x00400000`; verify the two recorded SHA-256 values and the single-byte difference at relative offset `0x4F`.
4. Trace the six class paths in EXP-0071's UClass inheritance catalog. Do not substitute these class relations for UFunction override relations.
5. Verify the cumulative manual overlay contains 39 unique addresses and includes both new target addresses.

The class relations and export records derive from the same UELib corpus. Static table and code evidence does not demonstrate runtime use. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior state-exit slot comparison: [EXP-0147](EXP-0147-state-exit-adapter-slot-variants.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
