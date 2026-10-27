---
id: EXP-0111
title: Direct internal callees of the audio API candidate cohort
experiment_status: done
claim_status: observed
build: "10256413"
question: What exact-build indexed functions are directly called by the 181 audio API name candidates, and what signatures or body operations can be directly recorded?
---

# EXP-0111 — Direct internal callees of the audio API candidate cohort

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: follow exact indexed direct calls leaving the 181-function EXP-0110 cohort, decompile each distinct indexed internal callee, and record exact qualified signatures plus a small number of manually reviewed visible operations.
- Exclusions: indirect calls, data/vtable dispatch, full semantics of 96 address-named unknown-bucket callees, runtime reachability, and audio output. A call from an audio API candidate does not by itself prove that a target belongs to the audio subsystem.
- Durable outputs: [callee and incoming caller catalog](../research/executable/evidence/EXP-0111-audio-api-direct-callee-cohort.csv) and [summary](../research/executable/evidence/EXP-0111-audio-api-direct-callee-cohort.json).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, EXP-0110, and the build record; confirm the current executable SHA matches.
2. Select the 181 EXP-0072 `audio_middleware_candidate` addresses, query exact-build indexed `kind='call'` edges from those functions, and retain non-external target addresses.
3. Batch-decompile every distinct internal target with `DecompileAddressBatch.java` using Ghidra `-noanalysis -readOnly`.
4. Reconcile the edges with EXP-0072 triage and count an exact qualified-signature match only where the function's own decompiler prototype includes a qualified owner and the final method name equals the index label.
5. Review visible operations in six directly called functions and run `python tools/audio_api_direct_callee_cohort.py` to regenerate the catalog and count checks.

## Observations

- The exact-build callgraph contains 401 direct internal call edges from the 181-function candidate cohort to 126 distinct indexed internal callees. All 126 addresses were present in the batch and all decompiles completed.
- The 126 targets' EXP-0072 triage buckets are: 96 `unknown`, 27 `audio_middleware_candidate`, 2 `runtime_library_candidate`, and 1 `runtime_or_object_lifecycle_candidate`. The call relation alone does not change those labels.
- 29 target signatures match both the indexed label and a qualified owner: 18 `AK::SoundEngine`, 6 `AK::MemoryMgr`, 4 `AK::SoundEngine::Query`, and 1 `CAkRegistryMgr`. The other targets do not have a matching qualified signature under this rule; this does not rule out audio-related behavior.
- The cohort directly calls `FUN_00D21A00` from 41 functions, consistent with EXP-0110/0109; its 43 callsite edges are a subset of EXP-0109's 50 edges from all 48 callers.
- Selected exact-body observations:
  - `FUN_00D16810` enters a critical section, indexes a bucket using the second argument modulo `0xC1`, walks linked nodes and compares against that argument, writes the node field derived from `CriticalSection->DebugInfo` plus one on a match, then exits the lock. Ghidra's recovered struct types are not treated as original source types.
  - `CAkRegistryMgr::GetObjAndAddref` at `00D2CB40` selects a bucket by `param_1 % 0xC1`, walks collision nodes comparing their stored key, and increments the returned object field at `+0x54` before returning it.
  - `FUN_00D13590` branches on its second argument. For value `1`, it waits indefinitely on the handle at `param_1[1]`; both branches close and clear that handle, then return either `*param_1` or the second argument.
  - `FUN_00D15260` bounds a local string copy to `0x104` bytes, truncates at the first period, passes the result to `AK::SoundEngine::GetIDFromString`, calls `FUN_00D27480`, and returns the ID.
  - `FUN_00D27810` locks `this+0x30`, calls state helpers, conditionally signals the handle at `this+0x28`, releases the lock, and returns an integer result.
  - `FUN_00A1F950` returns literal `0x18`.

## Interpretation and claim limits

- **Observed:** the indexed direct-call graph links 181 name candidates to a finite set of 126 exact-build internal callees. 29 callee signatures independently expose exact qualified owner/name pairs.
- **Observed:** the selected bodies expose lock, bucket/list, handle, string, and helper-call operations described above. This records pseudocode operations only; it does not settle class layouts or infer original source intent.
- **Unknown:** what the 96 unknown-bucket targets do as a complete group, unindexed/indirect targets, why particular API wrappers call them, whether any of these paths execute in a game session, and runtime sound behavior.
- **Limit:** the callgraph records indexed direct edges only; indirect calls and dataflow are outside this pass. Decompiler pseudocode and recovered types are analysis artifacts, not source. No game was launched.

## Reproduction

From repository-root PowerShell, derive the 126 addresses from the exact-build DB, decompile them with the same read-only batch script used in [EXP-0110](EXP-0110-audio-api-candidate-cohort.md), then run the summarizer:

```powershell
$addresses = @(python tools/audio_api_direct_callee_cohort.py --list-addresses)
$out = (Resolve-Path 'assets/extracted').Path + '\audio-api-callee-decompile.txt'
& 'E:\Dev\Tools\ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat' `
  (Resolve-Path 'research/executable/ghidra-project').Path 'Dishonored-RHCP-10256413' `
  -process 'Dishonored.exe' -noanalysis -readOnly `
  -scriptPath (Resolve-Path 'research/executable/scripts').Path `
  -postScript DecompileAddressBatch.java $out @addresses
python tools/audio_api_direct_callee_cohort.py
```

Or run just the summarizer after the local read-only batch dump already exists:

```powershell
python tools/audio_api_direct_callee_cohort.py
```

The local decompile dump is an ignored intermediate and is not committed.

## Links

- [EXP-0072 exact-build function triage](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- [EXP-0110 audio API candidate cohort](EXP-0110-audio-api-candidate-cohort.md)
- [EXP-0109 producer/dispatcher case map](EXP-0109-audio-record-dispatch-case-coverage.md)
- [Direct-callee summarizer](../tools/audio_api_direct_callee_cohort.py)
