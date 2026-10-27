---
id: EXP-0151
title: Shared AnimNode SetBlendTarget native adapter
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the three exact AnimNode class-table exports and the body at 0x005DB9A0 establish about SetBlendTarget dispatch?"
---

# EXP-0151 — Shared AnimNode SetBlendTarget native adapter

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the three EXP-0139 class-table edges to `0x005DB9A0`, compare exact native declarations and class Super paths, and trace body-decoded values to its indirect receiver call.
- Exclusions: no receiver slot name assigned to `+0x1DC`; no claim about animation blending effect, temporal behavior, or runtime use; no UFunction override inferred from class inheritance.
- Inputs: EXP-0139 class-table/UELib join; EXP-0071 UELib class inheritance catalog; exact-build function index; read-only decompilation cache; exact-build executable.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0151.csv), [43-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0151.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0151.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select all raw EXP-0139 edges at `0x005DB9A0`; compare exact function paths, declarations, NativeFlag, NativeToken, script size, source line, and source hash.
3. Resolve the target in the exact-build function index and verify its read-only decompilation cache build/hash identity.
4. Map the 144-byte range from VA to `.text` via the PE32 image base and section table; hash the range and trace both decoded values to the indirect call.
5. Trace each exact export owner's `UClass.Super` path in EXP-0071, keeping class inheritance distinct from function override evidence.
6. Add one inferred L1 adapter candidate; leave semantic, connectivity, and runtime claims unchanged.

## Observations

- The executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; PE32 image base is `0x00400000`. The exact-build function index records `FUN_005db9a0` at `0x005DB9A0`, size 144 bytes in `.text`.
- The read-only decompilation cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `E6692B5C83B085FCDF752795029F4938DB3689BAE5EEC81DBFC952F25EFC2A9C`. Raw `.text` range SHA-256: `4B109D8C699F66B796BA1377E96E060FC0ADAD9CB2741C2F9CBDDE15B1363633`.
- Three exact EXP-0139 edges target the body: `AnimNodeBlend.SetBlendTarget`, `AnimNodeAdditiveBlending.SetBlendTarget`, and `AnimNodeBlendPerBone.SetBlendTarget`.
- All three exports are `NativeFlag=true`, `NativeToken=0`, script size 12, and declare `native function SetBlendTarget(float BlendTarget, float BlendTime);`. Their source JSONL rows are 275, 276, and 281, all from source SHA-256 `47760EFCB17CBDBFFBF76A58746EBDF20743135A85BC7A6B8BE0F09F0D13B56B`.
- The three class `UClass.Super` paths all pass through `Class'Engine.AnimNodeBlendBase'`. `AnimNodeAdditiveBlending` and `AnimNodeBlendPerBone` pass through `Class'Engine.AnimNodeBlend'`; the latter then reaches `AnimNodeBlendBase`. The relation catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The body reads two frame bytes, invokes the decoder selected by each, stores two 32-bit values, conditionally handles the `A` marker, then loads receiver displacement `+0x1DC` and passes both values as explicit call arguments. The matching declarations type the two exported parameters as floats; the concrete receiver method and behavior remain unidentified.
- The address was not present in the EXP-0150 manual overlay. This addition creates one L1 body review only; no confirmed semantic claim, inter-function L3 edge, or runtime record is added.

## Interpretation and claim limits

- **Observed:** three exact class-table edges share one indexed body. Their exports share the same two-float declaration and native/token-zero metadata.
- **Observed:** all three class Super paths converge at `AnimNodeBlendBase`.
- **Observed:** the body decodes two 32-bit values and passes them to the receiver's indirect call at displacement `+0x1DC`.
- **Inferred, limited:** `0x005DB9A0` is a shared native-exec adapter candidate for the three `SetBlendTarget` exports. Exact table/name/export joins and matching declarations support that role.
- **Unknown:** the virtual member at `+0x1DC`, the receiver-side implementation, animation-state effect, runtime reachability, and timing behavior.
- **Not established:** class ancestry and export declarations do not establish an exact UFunction override relation or runtime animation effect.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select the three rows at `0x005DB9A0`.
2. Resolve the 144-byte function in `research/executable/functions.csv`; verify the cache build ID and executable SHA.
3. Map `0x005DB9A0` into the exact executable `.text` section using `RVA = VA - 0x00400000`; verify the recorded code SHA and trace both values into the indirect call.
4. Trace the three class paths in EXP-0071's UClass inheritance catalog. Do not use class ancestry as function override evidence.
5. Verify the cumulative manual overlay contains 43 unique addresses and includes `005DB9A0`.

The class relations and export declarations derive from the same UELib corpus. Static table and code evidence does not demonstrate runtime use or animation results. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior target cluster review: [EXP-0144](EXP-0144-navmesh-goal-recycle-thunk.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
