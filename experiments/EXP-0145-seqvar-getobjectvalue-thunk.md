---
id: EXP-0145
title: Shared SeqVar GetObjectValue native-exec handler
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the shared class-table target and UELib class/function Super relations establish for four Dishonored GetObjectValue exports?"
---

# EXP-0145 — Shared SeqVar GetObjectValue native-exec handler

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the four-edge EXP-0139 target `0x009F6270`; compare exact native exports, read-only body/dataflow, and UELib class/function `Super` relations.
- Exclusions: no semantic name assigned to vtable displacement `+0x184`, no runtime call or returned-object behavior claim, and no elevation of the UELib catalog beyond its serialized parser evidence.
- Inputs: EXP-0139 class-table/UELib join and target catalog; EXP-0071 all-install inheritance catalog; exact-build function index and read-only decompiler output.
- Durable outputs: [one-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0145.csv), [35-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0145.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0145.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Resolve the highest-priority four-edge `GetObjectValue` target in the EXP-0139 catalog and compare all exact UELib declarations and source records.
3. Resolve the indexed function range and inspect read-only decompiler output plus raw `.text` disassembly. Trace the indirect return value through the wrapper's output write without assigning a vtable member name.
4. Join each exact class and function object path to the structured EXP-0071 `UClass.Super` and `UFunction.Super` rows.
5. Add the target as an L1 static-role candidate; leave subsystem, slot identity, and runtime behavior unresolved.

## Observations

- The exact-build function index identifies `FUN_009f6270` at `0x009F6270`, size 58 bytes, in `.text`. The read-only decompiler cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `2FD6FA78F4BB22C8443C231F0AE6F977DE19A884C115D630EC77C759417BC72E`.
- Four EXP-0139 class-table edges from registration function `0x00A0DBF0` point to `0x009F6270`. Every matched export is `NativeFlag=true`, `NativeToken=0`, script size 2, and declares `native function Object GetObjectValue();` with no explicit parameters. The four source JSONL rows are 843–846, with SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`; the package source/hash provenance is preserved in EXP-0139.
- The four UELib class paths are `DisSeqVar_PlayerCamera`, `DisSeqVar_PlayerPawn`, `DisSeqVar_SpawnerPawn`, and `DisSeqVar_Task`. The EXP-0071 catalog records a `UClass.Super` relation from each one directly to `Class'Engine.SeqVar_Object'` (rows 1268, 1271, 1275, and 1277 in the decompressed CSV).
- The same catalog records a `UFunction.Super` relation from each exact `GetObjectValue` export to `Function'Engine.SeqVar_Object.GetObjectValue'` (rows 1267, 1270, 1274, and 1276). Catalog SHA-256: `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The decompiler shows the frame code pointer at offset `+0x18` advancing, a conditional `A` marker routed through `DAT_014069F4`, a receiver-vtable lookup at displacement `+0x184`, then a store of the indirect call's returned dword through the third decompiler parameter. Raw disassembly confirms `mov edx, [eax+0x184]`, `call edx`, and then `mov [ecx], eax`.
- The exact 58-byte raw `.text` range has SHA-256 `6D8B42E09A8746E4C4D67F83694CD691A32466938B79098EA6F5A1B18B0A6808`. The instruction sequence ends with `ret 8` at `0x009F62A7`.
- The address was subsystem-unknown and absent from the EXP-0144 manual overlay. This addition creates one L1 review only; it does not add a confirmed semantic claim, an inter-function L3 edge, or a runtime record.

## Interpretation and claim limits

- **Observed:** four exact class-table edges target the same indexed body; the exports share the same zero-parameter object-returning declaration, native flag, token-zero value, and script size.
- **Observed:** the UELib catalog has direct class Super and function Super rows for all four exact paths, each pointing to the corresponding `SeqVar_Object` class or function path. These are parsed serialized relations from one corpus.
- **Observed:** the body retrieves a receiver vtable entry at `+0x184`, calls it without explicit arguments, and stores the returned register value through an output pointer.
- **Inferred, limited:** the target is a shared native-exec adapter candidate for these `GetObjectValue` exports. Export metadata, exact class/function Super paths, and the observed return-value flow support the candidate role.
- **Unknown:** which virtual member occupies `+0x184`, the concrete receiver vtable layout, which object values the implementations return, runtime reachability, and game behavior.
- **Not established:** the export name and Super path do not identify the virtual slot or show that this handler executes at runtime. The decompiler's parameter labels are not source-level names.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select its four raw target rows at `0x009F6270`.
2. Resolve the address in the 10256413 function index; verify the cached build and executable SHA before reading its decompilation.
3. Rebuild EXP-0071's inheritance catalog and compare the four exact `UClass` paths and four exact `UFunction` paths separately.
4. Map `0x009F6270` into the exact executable's `.text` section with `RVA = VA - ImageBase`, read 58 bytes, verify the recorded SHA, and disassemble with Capstone 5.0.7.
5. Verify the cumulative manual overlay contains 35 unique indexed addresses and includes `009F6270`.

The class and function Super relations derive from the same UELib catalog and are not an independent parser validation. Static code and table joins do not prove runtime use. No game launch or runtime test was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior four-edge target comparison: [EXP-0144](EXP-0144-navmesh-goal-recycle-thunk.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
