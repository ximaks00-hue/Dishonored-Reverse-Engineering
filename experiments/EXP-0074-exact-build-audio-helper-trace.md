---
id: EXP-0074
title: Exact-build audio API helper trace
experiment_status: done
claim_status: observed
build: "10256413"
question: "What do selected internal direct callees of exact-build AK::SoundEngine wrappers show in static decompilation and callgraph data?"
---

# EXP-0074 — Exact-build audio API helper trace

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md). The executable is at `Dishonored RHCP/Binaries/Win32/Dishonored.exe` in this workspace.
- Scope: static callgraph and read-only decompiler follow-up for selected direct callees of the four exact-address API probes in [EXP-0073](EXP-0073-exact-build-audio-api-function-probes.md).
- Exclusions: no runtime reachability or frequency, engine ownership for unnamed helpers, or complete audio subsystem classification is established. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: exact-build `knowledge/database/callgraph.sqlite` and read-only `dishonored_static` decompiler. Graph metadata reports build `10256413` and the same executable hash.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256.
2. Inspect incoming and outgoing static call/data edges for `PostEvent` (`00D16CD0`), `LoadBank` (`00D15300`), `RenderAudio` (`00D13670`), and `SetState` (`00D15090`).
3. Decompile the direct callees `00D16BE0`, `00D15260`, and `00D21980` at their exact addresses. Treat Ghidra pseudocode as analysis output, not source.

## Observations

- The graph records `PostEvent` → `FUN_00D16BE0` at call site `00D16D3A`. The decompiler body for `00D16BE0` accepts seven stack-like parameters in its recovered prototype, copies four words from an optional pointer, calls `FUN_00D16810` and `FUN_00D24100`, increments global `DAT_01472B9C` on the non-null path, and can call through a function pointer. These operations are visible; the helper's semantic identity is unknown.
- The graph records `LoadBank` → `FUN_00D15260` at `00D15330`. That body copies a narrow string into a 260-byte local buffer (bounded to 259 bytes), truncates it at the first period if present, calls `AK::SoundEngine::GetIDFromString`, then calls `FUN_00D27480` with the ID and local string. This supports an observed name-to-ID/helper handoff in this call path, without naming the recipient helper's wider responsibility.
- `LoadBank` also has direct calls to `CreateEventW`, `FUN_00D27810`, and `FUN_00D13590`; those helpers were not probed here.
- The graph records `RenderAudio` → `FUN_00D21980` at `00D13676`. The helper body enters/leaves a critical section, compares fields, conditionally calls `FUN_00D218F0` and increments a field, then conditionally calls `FUN_00D46400`. This is synchronization-shaped code in the decompiler view; its relationship to audio rendering is not independently established.
- Static incoming call edges include two callers for `LoadBank` (`FUN_009B1780`, `FUN_009B2B80`), three for `RenderAudio` (`FUN_00D275B0`, `FUN_00D27940`, `FUN_00D5E780`), and one for `SetState` (`FUN_009AEDD0`). The `PostEvent` graph has no internal direct caller in this export. These are static references only, not runtime reachability.
- The tested `callgraph.sqlite` contains six edge rows per wrapper in this query, including two data-reference rows (a global pointer and the entry-point marker); these data rows are not additional call sites.

## Interpretation and claim limits

- **Observed:** three exact helper bodies and direct edges expose the operations above in this build's static index/decompiler output.
- **Inferred, narrow:** the `LoadBank` helper path includes a string normalization and AK ID conversion before a two-argument helper handoff, based on the body at `00D15260` and its direct call from `00D15300`.
- **Unknown:** semantic identities of `FUN_00D16BE0`, `FUN_00D27480`, `FUN_00D21980`'s callees, full helper ownership, execution conditions, and runtime use.
- **Limit:** callgraph records represent static references. Decompiled pseudocode is not original source. Findings apply only to the inspected addresses and exact build.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0073 API probes](EXP-0073-exact-build-audio-api-function-probes.md)
- [Function triage](EXP-0072-exact-build-internal-function-subsystem-triage.md)
