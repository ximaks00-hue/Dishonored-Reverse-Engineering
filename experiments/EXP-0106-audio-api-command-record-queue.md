---
id: EXP-0106
title: Static audio API command-record queue handoff
experiment_status: done
claim_status: observed
build: "10256413"
question: Do selected AK::SoundEngine wrappers visibly package fixed-size records and pass them through a shared synchronized buffer path?
---

# EXP-0106 — Static audio API command-record queue handoff

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: read-only exact-address decompilation of selected `AK::SoundEngine` wrappers and their shared helper path. Wrapper pseudocode, function-index direct-call graph, and helper pseudocode are the static evidence.
- Exclusions: no command-code semantics beyond observed caller field assignments; no consumer-side decode, runtime execution, event ordering, audio output, thread identity, or frequency is established. No game launch or binary modification.
- Tools: read-only `dishonored_static` decompiler and `dishonored_knowledge.function_dossier`; exact-build function index and callgraph artifacts.
- Durable output: [curated wrapper record catalog](../research/executable/evidence/EXP-0106-audio-command-records.csv).

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; verify the exact executable SHA-256.
2. Decompile selected exact-address wrappers: `SetRTPCValue` (`00D139F0`), `SetSwitch` (`00D13A80`), `PostTrigger` (`00D13AD0`), `RegisterGameObj` (`00D14190`), `UnregisterGameObj` (`00D141E0`), `UnregisterAllGameObj` (`00D14220`), `SetObjectObstructionAndOcclusion` (`00D13D80`), and `ResetRTPCValue` (`00D13B70`).
3. Decompile shared helpers `00D21A00`, `00D218F0`, `00D18670`, their size-return helpers, and the separate bank helper `00D27810`.
4. Compare direct-call edges and callees for the shared helpers against the exact-build callgraph index. Record only concrete pseudocode assignments, bounds, copies, synchronization calls, and helper edges.

## Observations

- All eight selected wrappers visibly write a 16-bit value at local record offset `+2`; the values and conditional branches are listed in the CSV. A few wrappers call constant-return helpers that supply apparent record byte lengths to the common call; one `SetRTPCValue` branch uses `FUN_00B42F50`, which was not inspected and therefore has unknown length here.
- `FUN_00D21A00` has 30 static direct callers in the function dossier. Its decompiled body enters a critical section, calls `FUN_00D218F0`, leaves the critical section, and returns that result.
- `FUN_00D218F0` writes its size argument as a 16-bit value at the beginning of the supplied record buffer, then calls `FUN_00D18670` with that buffer and size. When that helper returns `0x34`, the body checks available capacity, resets an event, releases the critical section, calls `FUN_00D46400`, waits on the event, reacquires the critical section, and retries. It can return `0x51` after the capacity check path.
- `FUN_00D18670` copies the passed bytes with `memcpy` into an indexed/chunked buffer region. Its pseudocode can allocate a chunk through `AK::MemoryMgr::Malloc`, records the used byte count, and returns `1` on its successful paths or `0x34` on the shown capacity/allocation failure paths.
- The static callgraph confirms `FUN_00D21A00 → FUN_00D218F0 → FUN_00D18670`. This is a static call relation; no runtime consumer was identified in this pass.
- The separately inspected `FUN_00D27810` is also called by multiple bank-related wrappers, including `LoadBank`; its body takes a different critical section and event path. It is not treated as the same record-buffer route as `00D21A00`.

## Interpretation and claim limits

- **Observed:** selected `AK::SoundEngine` wrapper bodies construct records with branch-specific field values and pass them into a shared critical-section-protected path that copies a size-bounded byte range into a chunked buffer. The exact written discriminator values and visible caller argument fields are preserved in the CSV.
- **Inferred, limited:** this is consistent with an enqueue/buffer-handoff interface for the selected wrappers. The inference is limited to the observed wrapper-to-buffer path and does not establish the queue's consumer or its audio-engine role beyond the exact caller namespace metadata.
- **Unknown at the scope of this pass:** record-code meanings at the consumer, the size helper for one branch, payload field type correctness, queue head/tail synchronization outside the inspected bodies, worker ownership, runtime reachability, and resulting audio behavior. EXP-0108 later matches selected producer codes to visible consumer cases; unmatched codes and runtime behavior remain open.
- **Limit:** Ghidra output is decompiler pseudocode, not original source. Static edge presence is not runtime execution. The curated catalog covers eight selected wrapper addresses and is not a classification of the 181 Wwise-like name candidates in EXP-0072.

## Reproduction

Issue read-only `decompile_function` requests for the procedure addresses and retrieve dossiers for `00D21A00`, `00D218F0`, and `00D18670`; compare the returned static edges and bodies with the catalog. Results may use the local decompile cache.

## Links

- [EXP-0072 exact-build function triage](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- [EXP-0073 Wwise API wrapper probes](EXP-0073-exact-build-audio-api-function-probes.md)
- [EXP-0074 audio helper trace](EXP-0074-exact-build-audio-helper-trace.md)
- [EXP-0108 audio record consumer case matches](EXP-0108-audio-record-consumer-opcode-matches.md)
- [EXP-0106 wrapper record catalog](../research/executable/evidence/EXP-0106-audio-command-records.csv)
- [Exact-build function index](../research/executable/functions.csv)
