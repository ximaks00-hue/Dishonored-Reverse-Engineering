---
id: EXP-0153
title: Shared two-argument native executor across AnimNode and AI exports
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What does the three-edge target 0x005DC290 establish when its exports belong to distinct AnimNode and AI class branches and declare different argument types?"
---

# EXP-0153 — Shared two-argument native executor across AnimNode and AI exports

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the three EXP-0139 exact class-table edges to `0x005DC290`, reconcile the declarations and class branches, and trace the two decoded values to the indirect receiver call.
- Exclusions: no shared gameplay/animation semantics inferred across the exports; no identity assigned to receiver displacement `+0x1DC`; no runtime reachability or method override inferred.
- Inputs: EXP-0139 class-table/UELib join; EXP-0071 UELib class inheritance catalog; exact-build function index; read-only decompilation cache; exact-build executable.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0153.csv), [45-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0153.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0153.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select the exact EXP-0139 rows targeting `0x005DC290`; compare declarations, native flags/tokens, script sizes, and source provenance.
3. Resolve the target in the function index and verify the decompilation cache build and executable identity.
4. Map and hash its indexed `.text` range; trace both decoder outputs to the indirect call.
5. Trace each exact export owner's `UClass.Super` path in EXP-0071. Keep the Engine AnimNode and Dishonored AI class branches separate and do not infer shared semantics from the common handler address.
6. Add one inferred L1 adapter candidate only.

## Observations

- The executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; PE32 image base is `0x00400000`. The exact-build function index identifies `FUN_005dc290` at `0x005DC290`, size 138 bytes in `.text`.
- The read-only decompilation cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `DDDF63C321B5008574AB1F61A3591AAA652F68A4CFA7B4A004FEA5CA3BF61C16`. Raw `.text` range SHA-256: `1F11F4696A2DFB586773CDDC340CA21DF8D5A50AD974EA7132E350AB07DBC728`.
- Three exact EXP-0139 rows target this body: `Engine.AnimNodeBlendList.SetActiveChild`, `Engine.ArkAnimNodeBlendPose.SetActiveChild`, and `DishonoredGame.DisBehaviorSearch.TickCallback_StareAtUnreachable`.
- The two Engine exports declare `native function SetActiveChild(int ChildIndex, float BlendTime);`. The DishonoredGame export declares `native function TickCallback_StareAtUnreachable(DishonoredNativeState _pThisState, float _fDeltaSeconds);`. All three are `NativeFlag=true`, `NativeToken=0`, and script size 12.
- The three source JSONL rows are 279 and 342 from Engine source SHA-256 `47760EFCB17CBDBFFBF76A58746EBDF20743135A85BC7A6B8BE0F09F0D13B56B`, plus row 254 from DishonoredGame source SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`.
- The two Engine class Super paths converge on `Class'Engine.AnimNodeBlendBase'`, then `Class'Engine.AnimNode'`. The DishonoredGame path runs through `Class'DishonoredGame.DisBehaviorAttentionBase'`, `DisAIBehaviorWithDesires`, and `DishonoredAIBehavior`. The branches meet only at `Class'Core.Object'` in the catalog. The relation catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The body decodes two frame values to separate 32-bit locals, handles the optional `A` marker, and passes both values as explicit arguments to receiver displacement `+0x1DC`.
- EXP-0151 independently records displacement `+0x1DC` in a different two-argument adapter target whose declarations are two floats. The targets have different indexed sizes and different raw code hashes; the shared displacement alone does not establish a common receiver member.
- The target was absent from the EXP-0152 overlay. This addition creates one L1 review only; it adds no confirmed semantic claim, L3 edge, or runtime record.

## Interpretation and claim limits

- **Observed:** three exact class-table edges with two distinct declarations and class hierarchies resolve to one indexed 138-byte body. All declarations have two parameters and all exports share native/token-zero metadata and script size 12.
- **Observed:** the body decodes two values and passes them to the indirect call at displacement `+0x1DC`.
- **Inferred, limited:** this target is a reusable two-argument native-exec adapter candidate for the three table entries. The exact table/export joins, matching parameter count, and body dataflow support the candidate.
- **Unknown:** the slot's receiver-side owner and behavior, the semantic relationship (if any) between the SetActiveChild declarations and the AI callback, and runtime reachability.
- **Not established:** shared handler address, two-argument shape, or equal receiver displacement does not prove common method semantics, common vtable ownership, or shared gameplay behavior.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select all three rows targeting `0x005DC290`.
2. Resolve the 138-byte function in `research/executable/functions.csv`; verify the decompilation cache build ID and executable SHA.
3. Map `0x005DC290` into the exact executable `.text` section using `RVA = VA - 0x00400000`; verify the code SHA and inspect the two decoded values and indirect call.
4. Trace both Engine class paths and the DishonoredGame class path separately in EXP-0071's UClass inheritance catalog.
5. Verify the cumulative manual overlay contains 45 unique addresses and includes `005DC290`.

The class relations and export declarations derive from the same UELib corpus. Static code and class-table evidence does not establish runtime behavior. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Same-offset animation adapter comparison: [EXP-0151](EXP-0151-animnode-set-blend-target-adapter.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
