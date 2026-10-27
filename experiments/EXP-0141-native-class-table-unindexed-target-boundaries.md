---
id: EXP-0141
title: Static boundary recovery for three unindexed native class-table targets
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can the three EXP-0138 `.text` targets missing from the function index be separated as complete x86 functions and associated with their exact UELib native declarations?"
---

# EXP-0141 — Static boundary recovery for three unindexed native class-table targets

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: validate all three `.text` targets from EXP-0138 that had no exact function-index start and lay outside indexed body ranges; inspect entry bytes and x86 instructions to the first `ret 8`; compare each raw name/address relation with its EXP-0139 UELib export and the next indexed function entry.
- Exclusions: no additions or edits to the 72,437-row function index or Ghidra database; no runtime dispatch, concrete native owner, table extent, or behavior claim beyond the inspected static code. These are recovered boundary candidates, not Ghidra function definitions.
- Tools and inputs: exact-build PE, EXP-0138/0139 catalogs, function index, read-only decompiles of indexed helpers `FUN_007A4950` and `FUN_00810460`, Python `pefile`, Capstone 5.0.7; [boundary audit and disassembly tool](../tools/recover_native_class_table_unindexed_targets.py).
- Durable outputs: [three boundary records](../research/executable/evidence/EXP-0141-native-class-table-unindexed-target-boundaries.csv), [instruction listing](../research/executable/evidence/EXP-0141-native-class-table-unindexed-target-disassembly.csv), and [summary with input hashes](../research/executable/evidence/EXP-0141-native-class-table-unindexed-target-boundaries-summary.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record. Require Steam build 10256413 and the recorded executable SHA-256; independently check the local EXE against the manifest.
2. Require the three EXP-0138 non-indexed target addresses, require zero indexed function ranges containing them, and join each address/name to the corresponding EXP-0139 UELib record with `NativeFlag=true`, `NativeToken=0`.
3. Map each VA to raw `.text` bytes and check the shared 16-byte x86 function-entry prologue `53 8B DC 83 EC 08 83 E4 F0 83 C4 04 55 8B 6B 04`.
4. Disassemble linearly from each target to the next indexed function entry. Require contiguous Capstone decoding through the first `ret 8`, all conditional branches before the return to remain inside the candidate range, and only `int3` (`0xCC`) bytes between the return and next indexed entry.
5. Record exact end/padding/next-entry addresses, disassembly, class/method names, UELib declarations, tool/input hashes, and limits. Do not edit the source function index.

## Observations

| Target VA | Joined export/declaration | Code end | Padding | Next indexed entry |
| --- | --- | --- | ---: | --- |
| `0x005D0B60` | `URB_HandleexecGetOrientation` — `native function Quat GetOrientation();` | `ret 8` at `0x005D0BCA` | 3 bytes | `0x005D0BD0` (`FUN_005d0bd0`) |
| `0x005D3120` | `URB_ConstraintInstanceexecMoveKinActorTransform` — `native final function MoveKinActorTransform(out Matrix NewTM);` | `ret 8` at `0x005D31BB` | 2 bytes | `0x005D31C0` (`FUN_005d31c0`) |
| `0x005C64F0` | `UUISceneClientexecGetInverseCanvasToScreen` — `native final function Matrix GetInverseCanvasToScreen();` | `ret 8` at `0x005C654A` | 3 bytes | `0x005C6550` (`FUN_005c6550`) |

- All three raw targets equal EXP-0138 `.text` pointer values and unique EXP-0139 UELib object-path/name matches; all three exports are NativeFlag=true and NativeToken=0.
- Each entry begins with the same 16-byte x86 prologue. Contiguous instruction decoding reaches `ret 8` at the listed address; the following two or three bytes are `int3` padding up to the next indexed function entry. The disassembly output contains all decoded instructions through the return.
- At `0x005D0B60`, the body consumes an optional `A` byte when present, calls a method through the `this` vtable at displacement `+0x178`, then copies four DWORDs (16 bytes) to the output pointer. The exact table/export name is `GetOrientation`, whose UELib declaration returns `Quat`; the copied width agrees with that declaration's storage size.
- At `0x005D3120`, the body decodes a frame value, consumes an optional `A` byte when present, and passes `this` and the output-matrix pointer to indexed helper `FUN_007A4950`. The helper body is indexed and decompiled separately; its concrete vtable method/type and runtime effects are not named here.
- At `0x005C64F0`, the body consumes an optional `A` byte when present and calls `FUN_00810460`; that helper copies sixteen DWORDs (64 bytes) from `this+0x90` to the supplied output buffer. The width agrees with the UELib `Matrix` return declaration, but the meaning of the stored matrix and whether it is the inverse described by the export name are not independently established.
- The exact-build helper pseudocode hashes are `D2E8F08B8822F407DA05B44DBCD81BD41E23C9ADE8325BED1FB3D7902AC095B2` for `FUN_007A4950` and `D29E36A3DD33190841280E7CFA0E651FF1429952A5FC4DA77E9B8DF6A8F9F7E2` for `FUN_00810460`; both decompile caches record build 10256413 and the executable SHA above.
- The 72,437-row function index remains unchanged. These three recovered boundary candidates remain outside its function inventory.

## Interpretation and claim limits

- **Observed:** three raw class-table target addresses begin with identical function-entry bytes, linearly decode without a gap through `ret 8`, and end with only `int3` padding before the next indexed entry. Exact class-table export names and UELib declaration paths match each target address.
- **Confirmed, static boundary candidate:** the byte layout strongly supports treating each target as a distinct x86 function body with the recorded start and return boundary. The independent `int3` padding and next indexed entry provide an adjacent boundary check.
- **Observed static role:** the `GetOrientation` candidate uses a `+0x178` virtual call and copies 16 output bytes; `MoveKinActorTransform` delegates to `FUN_007A4950` with an output pointer; `GetInverseCanvasToScreen` copies 64 bytes from `this+0x90` through `FUN_00810460`.
- **Inferred, limited:** the three functions implement native-exec paths corresponding to their exact table/export names and UELib declarations. These names do not establish their concrete class owner or runtime use.
- **Unknown:** concrete vtable owners and method identities, the complete semantics of the delegated constraint helper, runtime dispatch/reachability, and whether the returned matrix field has inverse-transform semantics.
- The 72,437 indexed denominator, EXP-0072 classifier, and EXP-0139 historical candidate catalog are not rewritten. No runtime evidence was collected.

## Reproduction and limitations

From the repository root:

```powershell
python tools\recover_native_class_table_unindexed_targets.py
```

The script validates build/manifest identity, exact EXP-0138/0139 target/name joins, the function-index exclusion, entry prologues, contiguous x86 decoding, `ret 8`, adjacent `int3` padding, and next indexed entry points. It writes compact CSV and JSON evidence, including hashes of the executable-manifest source catalogs and function index.

Linear disassembly is not a runtime trace and does not modify the Ghidra database. Function boundaries are high-confidence static candidates due to the independent pointer, entry, return, padding, and adjacent-index evidence; they are deliberately not inserted into the existing function index.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Raw target audit: [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- UELib and indexed-target join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Shared indexed target review: [EXP-0140](EXP-0140-shared-native-takedamage-handler.md)
- Function triage: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)

