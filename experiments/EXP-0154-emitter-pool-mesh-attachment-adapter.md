---
id: EXP-0154
title: "EmitterPool mesh-attachment native executor adapter"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What does target 0x005C2BA0 establish about the shared SpawnEmitterMeshAttachment exports, and what remains unknown about the receiver call?"
---

# EXP-0154 — EmitterPool mesh-attachment native executor adapter

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the two EXP-0139 exact class-table edges to `0x005C2BA0`, compare their UELib declarations and Super relations, and trace decoded values through the indirect receiver call and return storage.
- Exclusions: no name or behavior assigned to receiver slot `+0x3A8`; no claim that a particle effect is spawned or attached at runtime; no runtime reachability or successful result inferred.
- Inputs: EXP-0139 class-table/UELib join; EXP-0071 UELib class/function inheritance catalog; exact-build function index; read-only decompilation cache; exact-build executable; persisted call/data graph.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0154.csv), [46-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0154.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0154.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select the exact EXP-0139 target edges to `0x005C2BA0`; compare both declarations, NativeFlag/NativeToken metadata, and source package paths.
3. Resolve the target in the exact-build function index and verify the decompilation cache build and executable identity.
4. Map and hash the indexed `.text` range; trace the VM-frame decoder results, optional marker handling, receiver slot, and return output.
5. Check the UELib `Super` rows for both classes and functions. Keep the parsed inheritance evidence distinct from native runtime dispatch.
6. Add one inferred L1 adapter candidate; leave the baseline subsystem and receiver behavior unknown.

## Observations

- The exact-build index identifies `FUN_005c2ba0` at `0x005C2BA0`, size 422 bytes. Its read-only decompilation cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `886328C58E60D5784EDBAE37C9043C991282A1299C0B352D9EAF3028A6D41F24`.
- The indexed range is in `.text` at VA `0x00401000`; the range begins at file offset `0x001C1FA0`. Raw range SHA-256: `30B3D91C2A1FE0D9FBFEEE26EF073CC289708BF1B71647CCF751CD6102DE1093`.
- Two exact EXP-0139 class-table edges target this body: `DishonoredGame.DishonoredEmitterPool.SpawnEmitterMeshAttachment` and `Engine.EmitterPool.SpawnEmitterMeshAttachment`. Both declarations return `ParticleSystemComponent` and take `ParticleSystem`, `SkeletalMeshComponent`, `name`, optional `bool`, optional `Vector`, and optional `Rotator`; their parameter names differ by package convention.
- Both exports are NativeFlag=true and NativeToken=0 in the joined UELib catalog. The associated class paths are `DishonoredEmitterPool -> EmitterPool -> Actor` and `EmitterPool -> Actor`. The exact UFunction.Super relation for the DishonoredGame declaration points to the Engine declaration. These are parser-derived package relations, not proof of runtime class dispatch.
- The EXP-0071 compressed UELib inheritance catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`; the EXP-0139 target-candidate catalog SHA-256 is `93DC45C9FD4FB4F64A75C95222C5E44E633757D1BB7ADFB1FDC1FD1D0590D705`.
- The target has four persisted data references from class-table/vtable entries. The reference catalog and exact EXP-0139 joins support the two export edges; repeated pointer occurrences do not add distinct export declarations.
- The body advances the VM-frame cursor and decodes three initial argument values, a fourth value normalized to a Boolean, and two three-word argument groups. It clears/tests the shared decoder flag around the vector and rotator groups and zeroes a group when the flag indicates a decode problem.
- After the optional-argument marker handling, the body calls receiver displacement `+0x3A8` with the decoded values and stores the call's return through the output pointer. It does not itself contain a named particle-spawn routine or a visible attach operation.
- The target was absent from the EXP-0153 manual overlay. This addition creates one inferred L1 adapter candidate; subsystem ownership, receiver-slot identity, L2 semantics, L3 connectivity, and runtime status remain unknown.

## Interpretation and claim limits

- **Observed:** two exact class-table export edges with matching six-parameter declarations resolve to one indexed 422-byte body; the UELib class and function Super rows place the DishonoredGame entries beneath their Engine counterparts.
- **Observed:** the body decodes the declared argument groups, normalizes the Boolean, handles vector/rotator decode flags, calls receiver displacement `+0x3A8`, and stores the indirect result through an output pointer.
- **Inferred, limited:** `FUN_005c2ba0` is a shared native-exec argument-adapter candidate for the two `SpawnEmitterMeshAttachment` exports. The exact export join, matching declarations, and argument-shaped body support the role candidate.
- **Unknown:** the slot's receiver-side owner and implementation, how the return is produced, whether the call creates or attaches an effect, runtime reachability, and whether the call succeeds for any particular mesh or template.
- **Not established:** method and class Super relations, the function label, and the slot displacement do not prove the native routine's gameplay effect or runtime dispatch.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select the two rows targeting `0x005C2BA0`.
2. Resolve the 422-byte function in `research/executable/functions.csv`; verify the decompilation cache build ID and executable SHA.
3. Map VA `0x005C2BA0` to the `.text` raw range using the recorded image base `0x00400000`; verify the raw range SHA and inspect the decoder, indirect call, and output store.
4. Check the two class and UFunction.Super rows in EXP-0071's UELib inheritance catalog.
5. Verify that the cumulative manual overlay contains 46 unique addresses and includes `005C2BA0`.

The class relations and export declarations derive from the same UELib corpus. Decompiled pseudocode is an analysis representation, not original source. Static code does not establish runtime behavior. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)

