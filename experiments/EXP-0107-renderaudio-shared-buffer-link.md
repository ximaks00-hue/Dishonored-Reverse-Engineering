---
id: EXP-0107
title: RenderAudio caller and shared audio buffer path
experiment_status: done
claim_status: observed
build: "10256413"
question: Does the indexed RenderAudio wrapper reach the same shared record-buffer helper observed for selected SoundEngine wrappers, and what bytes/notification are visible in that path?
---

# EXP-0107 — RenderAudio caller and shared audio buffer path

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the exact-build `RenderAudio` wrapper (`00D13670`), its sole indexed direct callee `FUN_00D21980`, the shared buffer helper `FUN_00D218F0`, the event helper `FUN_00D46400`, and static callgraph edges.
- Exclusions: no consumer-side record decode, worker identity, event semantics, runtime execution, actual audio rendering, or output is established. No game launch or binary modification.
- Tools: read-only `dishonored_static` decompiler and `dishonored_knowledge.function_dossier`; exact-build function/callgraph index.

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; verify the exact executable SHA-256.
2. Decompile `00D13670`, `00D21980`, `00D218F0`, and `00D46400`.
3. Retrieve the indexed callers/callees for `00D21980` and `00D218F0`; compare the observed body edges.
4. Record literal field values and synchronization calls without assigning a semantic name to the record code.

## Observations

- The indexed `RenderAudio` wrapper at `00D13670` directly calls `FUN_00D21980` at `00D13676` and returns its result. The function dossier lists this as the only static direct caller of `00D21980`.
- `FUN_00D21980` enters a critical section and compares three fields in the state object. If the displayed condition is false, it writes `local_38=8` and `local_36=0`, calls `FUN_00D218F0(&local_38, 8)`, increments one field, leaves the critical section, and calls `FUN_00D46400`. If the condition is true, the record write and event call are skipped. It returns `1` in either shown branch.
- `FUN_00D218F0` is also called from the shared wrapper path through `FUN_00D21A00` (EXP-0106). `FUN_00D46400` calls the imported `SetEvent` with its first argument as the event handle.
- The indexed direct-call graph therefore records `RenderAudio → FUN_00D21980 → FUN_00D218F0 → FUN_00D18670` on the conditional record-write path, plus `FUN_00D21980 → FUN_00D46400 → SetEvent` on that same branch.
- These observed bodies show a writer/helper and notification path. This experiment did not find a function that consumes or decodes the copied record bytes.

## Interpretation and claim limits

- **Observed:** in this exact-build static view, the function indexed as `AK::SoundEngine::RenderAudio` reaches the shared size-prefixed buffer-copy path conditionally and then signals an event. The literal local values are an 8-byte size argument and a zero 16-bit field at record offset `+2`.
- **Unknown in this pass:** the meaning of the zero field, whether the event wakes a record consumer, and whether this wrapper performs or merely coordinates audio rendering. EXP-0108 later identifies `FUN_00D20940` as a record reader with case `0` bookkeeping matching this marker path; event purpose and runtime behavior remain unknown.
- **Limit:** namespace and mangled name metadata identify the indexed wrapper; decompiler output is not original source. Static call edges do not establish runtime invocation. A SetEvent call does not establish the event's consumer or purpose.

## Links

- [EXP-0106 static audio API command-record queue handoff](EXP-0106-audio-api-command-record-queue.md)
- [EXP-0108 audio record consumer case matches](EXP-0108-audio-record-consumer-opcode-matches.md)
- [EXP-0073 exact-build Wwise wrapper probes](EXP-0073-exact-build-audio-api-function-probes.md)
- [Function index and graph artifacts](../research/executable/README.md)
