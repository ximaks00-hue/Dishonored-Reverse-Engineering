---
id: EXP-0149
title: Two-argument native state transition callback adapter
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the three exact class-table exports and the indexed body at 0x009E4DE0 establish about this two-argument state callback target?"
---

# EXP-0149 — Two-argument native state transition callback adapter

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the three-edge class-table target `0x009E4DE0`, compare exact export declarations and class Super paths, and trace the body-decoded values to its indirect receiver call.
- Exclusions: no name assigned to the receiver slot `+0x1B0`; no semantics assigned to callback suffixes or argument order; no UFunction override, runtime dispatch, or gameplay result inferred.
- Inputs: EXP-0139 class-table/UELib join; EXP-0071 UELib class inheritance catalog; exact-build function index; read-only decompilation cache; exact-build executable.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0149.csv), [40-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0149.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0149.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and the executable SHA-256.
2. Select exact EXP-0139 target rows at `0x009E4DE0`; compare NativeFlag, NativeToken, script size, declarations, and source provenance.
3. Resolve the address in the exact-build function index and verify read-only cache build/hash identity.
4. Read the indexed raw `.text` range using PE32 VA-to-RVA mapping, hash it, and trace both decode results into the indirect call in decompilation/disassembly.
5. Trace each class `UClass.Super` path in the EXP-0071 catalog; do not treat class ancestry as a UFunction override relation.
6. Add one inferred L1 adapter candidate; do not create semantic, L3, or runtime evidence.

## Observations

- The executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; its PE32 image base is `0x00400000`. The exact-build index identifies `FUN_009e4de0` at `0x009E4DE0`, size 134 bytes in `.text`.
- The read-only decompilation cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `F7DA60EB6E7128FFD2DFF5B995CC9C10CD81E4724AA2FD9BD2CA18B1EE566532`. The raw 134-byte `.text` range SHA-256 is `307847FE4A9AF0EA945931003FD5A63C3F7B88EA001793D1D0B0827F2745630B`.
- Three raw EXP-0139 edges target this function: `DisBehaviorSummonWolfHound.OnExitCallback_GenericAction`, `DisBehaviorPatrolSearch.OnEnterCallback_Stand`, and `DisDLC06BehaviorAssassinSalute.OnExitCallback_GenericAction`.
- All three exports are `NativeFlag=true`, `NativeToken=0`, script size 12, and declare two `DishonoredNativeState` object parameters. Their exact names distinguish `pThisState` with `pNextState` or `pLastState`; the two GenericAction exports share the former signature.
- The source JSONL lines are 259, 236, and 913. All three derive from source SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`.
- The three class `UClass.Super` paths in EXP-0071 converge on `Class'DishonoredGame.DishonoredAIBehavior'`. `DisBehaviorSummonWolfHound` is a direct child; `DisBehaviorPatrolSearch` passes through `DisBehaviorPatrol` and `DisAIBehaviorWithDesires`; `DisDLC06BehaviorAssassinSalute` passes through `DisAIBehaviorWithDesires`. The relation catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The body reads two frame bytes, selects and invokes a decoder for each, and stores each decoded dword separately. It conditionally processes an `A` marker, then loads receiver displacement `+0x1B0` and passes both dwords as explicit call arguments. The order follows the decompiled local flow; their semantic meanings are not established.
- The target was absent from the EXP-0148 overlay. The addition creates one L1 review only, with no confirmed semantic claim, inter-function L3 edge, or runtime record.

## Interpretation and claim limits

- **Observed:** three exact class-table edges share an indexed body; their exports have native/token-zero status, a 12-byte script size, and two `DishonoredNativeState` parameters.
- **Observed:** all three class Super paths converge at `DishonoredAIBehavior`, with the intermediary paths recorded above.
- **Observed:** the body separately decodes two dwords and passes both to an indirect receiver call at displacement `+0x1B0`.
- **Inferred, limited:** this target is a shared two-argument native-exec adapter candidate for the three table edges. Exact table/name joins, matching declarations, and body shape support this role candidate.
- **Unknown:** the virtual member at `+0x1B0`, argument meanings/order at the semantic level, exact UFunction override relations, runtime reachability, and behavior.
- **Not established:** shared target and class ancestry do not prove identical callback behavior or a common UFunction override.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select the three rows targeting `0x009E4DE0`.
2. Resolve the 134-byte function in `research/executable/functions.csv`; verify the cache build ID and executable SHA.
3. Map `0x009E4DE0` into the exact executable `.text` section using `RVA = VA - 0x00400000`; verify the recorded code SHA and inspect the two decoder outputs and indirect call.
4. Trace the three class paths in EXP-0071's UClass inheritance catalog. Do not substitute class Super evidence for UFunction override evidence.
5. Verify the cumulative manual overlay contains 40 unique addresses and includes `009E4DE0`.

The class relations and export declarations derive from the same UELib corpus. Static table and code evidence does not demonstrate runtime use. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior one-argument adapter comparisons: [EXP-0147](EXP-0147-state-exit-adapter-slot-variants.md) and [EXP-0148](EXP-0148-state-exit-single-argument-adapter-pair.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
