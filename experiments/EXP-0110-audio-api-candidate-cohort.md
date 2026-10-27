---
id: EXP-0110
title: Exact-build audio API candidate cohort decompilation
experiment_status: done
claim_status: observed
build: "10256413"
question: What exact-build decompiler signature and indexed direct-call evidence exists for the 181 audio middleware name candidates?
---

# EXP-0110 — Exact-build audio API candidate cohort decompilation

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; current executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: decompile all 181 functions assigned the EXP-0072 `audio_middleware_candidate` name-label bucket and join them to exact-build indexed direct-call edges; identify exact name matches in demangled AK namespace signatures, including nested AK namespaces.
- Exclusions: vendor provenance, whether the matched namespaces establish complete subsystem ownership, indirect call targets, runtime reachability/frequency, and sound behavior. These name candidates remain separate from the 72,437-function semantic-review denominator.
- Durable outputs: [per-function cohort](../research/executable/evidence/EXP-0110-audio-api-candidate-cohort.csv) and [summary](../research/executable/evidence/EXP-0110-audio-api-candidate-cohort.json).

## Procedure

1. Re-read the repository instructions, status, Blink activation graph, and build record; hash the current executable and compare it with the build record.
2. Select all 181 `audio_middleware_candidate` rows from the EXP-0072 triage CSV.
3. Run `DecompileAddressBatch.java` through Ghidra headless using `-noanalysis -readOnly`; write intermediate output under ignored `assets/extracted/`.
4. Join each body to its indexed name and exact-build direct-call edges in `knowledge/database/callgraph.sqlite`. Record a namespace only when the decompiled function signature carries it; count a match only when the decompiled function name equals the triage label, searching all nested AK namespaces in the function prototype.
5. Run `python tools/audio_api_candidate_cohort.py` to assert build/hash, 181 complete bodies, and reconcile signatures and the direct writer edge subset.

## Observations

- Current `Dishonored RHCP/Binaries/Win32/Dishonored.exe` SHA-256 matches the registry hash in the build record.
- All 181 candidate addresses had an indexed function and a completed read-only decompile; no requested address was missing and no body reported `DECOMPILE_FAILED`.
- All 181 decompiled signatures match the triage name and an explicit AK namespace. Counts are 105 `AK::SoundEngine`, 30 `AK::SoundEngine::Query`, 17 `AK::MemoryMgr`, 12 `AK::StreamMgr`, 6 `AK::SoundEngine::DynamicSequence`, 5 `AK::MotionEngine`, 3 `AK::SoundEngine::DynamicDialogue`, and 3 `AK::MusicEngine`. The initial pass missed nested namespaces; EXP-0110’s reproduction script searches the complete nested namespace path.
- The direct-call graph contains 43 callsite edges from 41 cohort functions into `FUN_00D21A00`. This is the subset of the 50 writer edges / 48 callers in EXP-0109: the remaining callers are not in the 181-name candidate bucket.
- The CSV records per-address decompile name/namespace, whether the signature exactly matches the candidate label, indexed internal/external direct-call counts, writer edges, and named callsites. Zero internal direct callees in this static index does not imply the function is a leaf at machine level; indirect calls and data-driven dispatch can be absent from the graph.

## Interpretation and claim limits

- **Observed:** decompiler metadata corroborates exact function names and AK namespaces for all 181 name candidates at their indexed addresses. This strengthens name-label classification for this candidate cohort only.
- **Observed:** 41 candidate functions have 43 exact indexed callsites into the shared record writer. EXP-0109 independently maps their producer discriminator values against visible dispatcher cases.
- **Unknown:** whether the labels/names derive from an authentic Wwise symbol set or another symbol source, who calls any candidate at runtime, whether each path is reachable, and whether the code affects audible output.
- **Limit:** decompiler output is static analysis metadata, not original source. This namespace/signature match does not prove vendor provenance, complete subsystem ownership, or runtime reachability. The generated batch text is ignored local analysis data and is not committed.

## Reproduction

From the repository root in PowerShell, after confirming the configured headless path and project are available:

```powershell
$addresses = @(Import-Csv 'research/executable/evidence/function-triage/internal-function-triage.csv' |
  Where-Object { $_.subsystem_candidate -eq 'audio_middleware_candidate' } |
  ForEach-Object { $_.address })
$out = (Resolve-Path 'assets/extracted').Path + '\audio-api-candidate-decompile.txt'
& 'E:\Dev\Tools\ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat' `
  (Resolve-Path 'research/executable/ghidra-project').Path 'Dishonored-RHCP-10256413' `
  -process 'Dishonored.exe' -noanalysis -readOnly `
  -scriptPath (Resolve-Path 'research/executable/scripts').Path `
  -postScript DecompileAddressBatch.java $out @addresses
python tools/audio_api_candidate_cohort.py
```

## Links

- [EXP-0072 exact-build function triage](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- [EXP-0073 selected exact-address probes](EXP-0073-exact-build-audio-api-function-probes.md)
- [EXP-0109 producer/case coverage](EXP-0109-audio-record-dispatch-case-coverage.md)
- [Batch decompiler script](../research/executable/scripts/DecompileAddressBatch.java)
- [Cohort summarizer](../tools/audio_api_candidate_cohort.py)
