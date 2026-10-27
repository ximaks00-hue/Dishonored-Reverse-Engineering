---
id: EXP-0144
title: Shared no-argument native handler across NavMeshGoal recycle exports
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the next high-connectivity class-table target and serialized class/function Super relations establish for the NavMeshGoal recycle export cluster?"
---

# EXP-0144 — Shared no-argument native handler across NavMeshGoal recycle exports

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the next unreviewed EXP-0139 target by edge count, `0x00957C30`, and compare its six exact UELib exports with the structured `Super` relations recorded for their classes and functions.
- Exclusions: no meaning assigned to receiver vtable displacement `+0x140`; no proof that all exports call the same semantic method; no runtime dispatch or behavior claim; no promotion of UELib inheritance records to independent runtime evidence.
- Inputs: EXP-0139 class-table/UELib join and 254-address catalog; EXP-0071 all-install inheritance relation catalog; exact-build function index and read-only decompiler cache.
- Durable outputs: [one-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0144.csv), [34-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0144.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0144.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select the highest-edge-count unreviewed indexed address in EXP-0139. Resolve its exact target edges and UELib export records.
3. Inspect the function range read-only and record frame-pointer operations, optional-marker handling, and indirect call displacement without naming the slot.
4. Join the six exact class paths and function paths to EXP-0071's structured `UClass.Super` and `UFunction.Super` relation rows. Keep class and function relations separate, and distinguish missing function rows from negative proof.
5. Add the target as an L1 static-role candidate; do not assign subsystem, slot identity, or runtime status.

## Observations

- The exact-build index identifies `FUN_00957c30` at `0x00957C30`, size 53 bytes, in `.text`. The cached decompiler record names build `10256413` and the exact executable SHA above. Cached pseudocode SHA-256: `C51DF503EE0F3C8B15ED23BC7BB17A29EF6FDF6D0CAD3CE10E55DBEEAF0939C6`.
- Six EXP-0139 raw class-table edges point to this target, using registration functions `0x006067A0`, `0x0096DAB0`, and `0x00A0DBF0`. Every matched export is `NativeFlag=true`, `NativeToken=0`, script size 2, and has no declared parameters. The exported method names are `RecycleInternal` (two edges), `Recycle` (one), and `RecycleNative` (three).
- The edges resolve to `Engine.NavMeshGoal_At`, `Engine.NavMeshGoal_ClosestActorInList`, `Engine.NavMeshGoal_Null`, `GameFramework.NavMeshGoal_OutOfViewFrom`, `DishonoredGame.DisNavMeshGoal_BestFleePoint`, and `DishonoredGame.DisNavMeshGoal_ShootingPosition`.
- The UELib JSONL inputs and package hashes are preserved in EXP-0139. The three exact source JSONL SHA-256 values are `47760EFCB17CBDBFFBF76A58746EBDF20743135A85BC7A6B8BE0F09F0D13B56B` (Engine; rows 1956, 1959, 1964), `957A50E7D3A1A41AF5BC7CF6DF7A76420A3717E6710F0F5043EA9DA6835C4F42` (GameFramework; row 102), and `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4` (DishonoredGame; rows 821, 822).
- The EXP-0071 catalog contains six `UClass.Super` rows for these classes. Five point directly to `Engine.NavMeshPathGoalEvaluator`; `DishonoredGame.DisNavMeshGoal_BestFleePoint` points to `Engine.NavMeshGoal_ClosestActorInList`, which itself points to `Engine.NavMeshPathGoalEvaluator`. The catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`; the six rows are at compressed-CSV text lines 946, 950, 2994, 2996, 3001, and 3723.
- Two exact target-method paths have `UFunction.Super` rows in that catalog: `DisNavMeshGoal_BestFleePoint.RecycleInternal` points to `Engine.NavMeshGoal_ClosestActorInList.RecycleInternal` (line 945), and `DisNavMeshGoal_ShootingPosition.Recycle` points to `Engine.NavMeshPathGoalEvaluator.Recycle` (line 949). The catalog has no `UFunction.Super` row for the other four exact table-target function paths; this absence does not prove the functions have no superclass relation.
- The decompiler output shows the frame code pointer at object offset `+0x18` advancing by one, a conditional `A` marker handled through `DAT_014069F4`, then an indirect receiver-vtable call at displacement `+0x140` with no explicit arguments. The 53-byte raw `.text` range has SHA-256 `20ACB61AA11072081F99ABF6A7365AAF66A52FB48CAB64C1DEB6709779EA529F`; Capstone 5.0.7 decodes the range through `ret 8` at `0x00957C62`.
- This address was subsystem-unknown and absent from the EXP-0143 manual overlay. The new row adds L1 only; no confirmed semantic claim, L3 dataflow edge, or runtime record is added.

## Interpretation and claim limits

- **Observed:** six exact class-table/export edges target one indexed 53-byte function. All six exports are native, token-zero, zero-parameter functions with script size 2. The body conditionally processes the `A` marker and makes an indirect receiver call through `+0x140`.
- **Observed:** the EXP-0071 structured class relation rows place all six classes under `NavMeshPathGoalEvaluator`, directly for five classes and through `NavMeshGoal_ClosestActorInList` for one. Two exact target-method paths also have explicit UFunction.Super rows; four exact target methods have no such row in the catalog.
- **Inferred, limited:** `FUN_00957C30` is a shared no-argument native-exec adapter candidate for the six table/export edges. The matching native metadata and observed call shape support the candidate; the actual member behind `+0x140` remains unidentified.
- **Unknown:** whether `+0x140` is the `Recycle`, `RecycleInternal`, or another virtual member on any receiver; how the three method spellings relate; table consumption; and runtime reachability or effects.
- **Not established:** serialized Super links do not prove runtime vtable layout, that all six exports invoke one semantic method, or that the adapter's call executes in game.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and catalog from its recorded UELib JSONL inputs; select the six rows at target `0x00957C30`.
2. Resolve the address in the 10256413 function index and verify the decompiler cache build ID and executable SHA.
3. Rebuild the EXP-0071 gzip catalog. Compare the six listed class paths and six exact method paths against the `UClass` and `UFunction` relation rows separately.
4. Read the 53-byte function range from the PE `.text` section using `RVA = VA - ImageBase`; verify its SHA-256 and disassemble with Capstone 5.0.7.
5. Verify the cumulative overlay has 34 unique indexed addresses and includes `00957C30`.

The UELib inheritance catalog reports parsed serialized `Super` fields and is not independent validation of game-runtime behavior. The executable was read-only; no game launch or runtime trace was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior shared TakeDamage target review: [EXP-0143](EXP-0143-identical-native-takedamage-adapter-bodies.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
