---
id: EXP-0155
title: "Shared SetEnabled(bool) native adapter and receiver bit update"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the three Engine SetEnabled(bool) exports targeting 0x005C8530 establish about the receiver update, and what remains unknown about the changed bit?"
---

# EXP-0155 — Shared SetEnabled(bool) native adapter and receiver bit update

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: review all EXP-0139 class-table edges to `0x005C8530`, verify the x86 calling convention and receiver update in raw code, and record parsed class Super relations.
- Exclusions: do not name the receiver field or bit as an enabled/visible state; do not infer class-table runtime dispatch, downstream `0x00569890` behavior, subsystem ownership, or runtime reachability.
- Inputs: EXP-0139 exact-build class-table/UELib join; exact-build function index and executable; build-scoped decompilation cache; EXP-0071 UELib inheritance catalog; persisted call/data graph.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0155.csv), [47-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0155.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0155.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select the exact EXP-0139 rows targeting `0x005C8530`; compare export names, declarations, NativeFlag/NativeToken metadata, and package/class paths.
3. Verify the indexed function range and decompilation-cache identity, then disassemble the exact bytes to resolve the receiver and argument registers at the call to `0x00781520`.
4. Trace `0x00781520` through its return and call to `0x00569890`; record only direct data/control effects visible in the indexed bytes.
5. Check parsed UELib Super rows for the three classes; do not treat parsed inheritance as runtime dispatch evidence.
6. Add one inferred L1 native-exec adapter candidate; retain unknown semantic ownership and runtime status.

## Observations

- The exact-build EXP-0139 join has three rows targeting the indexed start `0x005C8530` (102 bytes): `Engine.DisFogComponent.SetEnabled(bool)`, `Engine.SceneCaptureComponent.SetEnabled(bool)`, and `Engine.WorldRainComponent.SetEnabled(bool)`. Each is NativeFlag=true and NativeToken=0. The decoded native names match their class keys and `execSetEnabled` export names. The declarations are not byte-identical in wording: the SceneCapture declaration is `native final simulated function`; the other two are `native final function`.
- The EXP-0139 join records the exact-build build ID and executable SHA above. Its three raw `.data` name-pointer/adjacent handler-pointer observations resolve to an exact function-index start. The join itself states that runtime dispatch is unproved.
- The read-only decompilation cache for `005c8530` and `00781520` records build `10256413` and the same executable SHA. The exact target byte range at VA `0x005C8530` is in `.text`; its 102-byte raw range SHA-256 is `13A495D5FE024A89D65B41BEC1F60FFD4DAC9351F7901940AC2AF88D0F37F973`. The 43-byte range at `0x00781520` has SHA-256 `6CFF969DD53C74CC0A378F83D420B33138CE89E7F6DAEE3DC959884D9875500F`.
- Raw x86 at `0x005C8530` saves incoming `ECX`, reads/decodes the VM-frame argument, normalizes the decoded dword to 0/1, handles a conditional `A` marker, pushes the normalized value, restores saved `ECX`, and calls `0x00781520`. The call therefore passes the saved receiver in `ECX` and the Boolean as a stack argument; the function returns with `ret 8`.
- Raw x86 at `0x00781520` reads dword `[ECX+0x54]`, compares its low bit to the Boolean argument, and returns without a write when they match. Otherwise it replaces only bit 0 at `[ECX+0x54]` with the argument's low bit, calls `0x00569890` with one zero stack argument, and returns with `ret 4`. This establishes the direct field/bit update and conditional call, but does not establish the field's semantic name or the callee's effect.
- The parsed UELib catalog places each of `DisFogComponent`, `SceneCaptureComponent`, and `WorldRainComponent` under `ActorComponent`, which is under `Core.Component`. The catalog explicitly labels these as parsed `Super` relations, not runtime inheritance behavior. No exact UFunction Super rows for these three `SetEnabled` methods were present in the inspected relation rows.
- The persisted exact-build call graph contains the edge `005C8530 -> 00781520` at `005C8589` and `00781520 -> 00569890` at `00781541`. It has no additional incoming call edge to `00781520` in the queried graph snapshot. The snapshot metadata identifies build `10256413` and the same executable SHA.

## Interpretation and claim limits

- **Observed:** three exact class-table name/target joins for `SetEnabled(bool)` exports resolve to the same indexed body, and raw code passes the saved `ECX` receiver plus a normalized Boolean to `0x00781520`.
- **Observed:** `0x00781520` conditionally writes only bit 0 of `[ECX+0x54]` to match the argument's low bit, then calls `0x00569890(0)` only when the bit changes.
- **Inferred, limited:** `0x005C8530` is a shared native-exec argument adapter for these three exports. Exact export joins and the raw call shape support this role candidate; runtime table dispatch is not demonstrated.
- **Unknown:** the semantic identity of `[this+0x54]` bit 0, whether it denotes enabled state, the behavior of `0x00569890`, concrete subsystem ownership, runtime reachability, and any visible/gameplay effect.
- **Not established:** matching method names or common parsed superclass do not prove that the bit is an enabled flag or that the three exports execute this path at runtime.

## Reproduction and limitations

1. Select the three rows for target `0x005C8530` from `research/executable/evidence/EXP-0139-native-class-table-uelib-zero-token-join.csv` and verify their declaration metadata.
2. Resolve `0x005C8530` and `0x00781520` in `research/executable/functions.csv`; verify their cache build ID and executable SHA.
3. Map each VA through PE image base `0x00400000` and the `.text` section; verify the recorded raw-range SHA-256 values and inspect the receiver/argument setup, conditional write, and call.
4. Check the exact class-path rows in the EXP-0071 compressed UELib inheritance catalog and preserve its parser/runtime limitation.
5. Verify the cumulative manual overlay contains 47 unique addresses including `005C8530`.

The native export join, package declarations, and parsed inheritance rows are static evidence. Decompiled pseudocode is an analysis representation, not original source. Raw machine code establishes the local x86 effects only. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior overlay review: [EXP-0154](EXP-0154-emitter-pool-mesh-attachment-adapter.md)
