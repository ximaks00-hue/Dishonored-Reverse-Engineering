---
id: EXP-0073
title: Exact-build Wwise SoundEngine function probes
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do selected audio-API-like function labels in the exact-build executable decompile with AK::SoundEngine namespace and body shapes consistent with their indexed names?"
---

# EXP-0073 — Exact-build Wwise SoundEngine function probes

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect four selected indexed function addresses whose names are distinctive Wwise-like API labels, using the build-matched offline Ghidra decompiler and function index.
- Exclusions: these probes do not classify all 181 Wwise-like names in EXP-0072; do not establish full library provenance, runtime call frequency/reachability, or behavior outside these four functions. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: read-only `dishonored_static` MCP decompiler, `research/executable/functions.csv`, build-matched offline function/callgraph indexes, and output catalog [EXP-0073-wwise-function-probes.csv](../research/executable/evidence/EXP-0073-wwise-function-probes.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the local executable SHA-256.
2. Select the address-indexed `PostEvent`, `LoadBank`, `RenderAudio`, and `SetState` rows from the EXP-0072 full-denominator triage output.
3. Request read-only decompilation for each exact address. Record Ghidra's decompiler signature, namespace/mangled symbol comment, and visible direct callees; compare the static call-role label in the triage output.
4. Save the selected observations in a compact CSV. The generated decompiler text cache is local analysis data; the experiment records the evidence needed to repeat each address query.

## Observations

- `00D16CD0` (`PostEvent`) decompiles with `AK::SoundEngine::PostEvent` and mangled name `?PostEvent@SoundEngine@AK@@...`. The body obtains an event ID with `GetIDFromString`, calls `FUN_00D16BE0` with the resulting ID and parameters, and has helper calls for its external-source argument path. The function-index/callgraph record marks it `caller_only`.
- `00D15300` (`LoadBank`) decompiles with `AK::SoundEngine::LoadBank` and mangled name `?LoadBank@SoundEngine@AK@@...`. Its body calls `CreateEventW`, `FUN_00D15260`, `FUN_00D27810`, and `FUN_00D13590`; the static callgraph role is `caller_and_target`.
- `00D13670` (`RenderAudio`) decompiles with `AK::SoundEngine::RenderAudio` and mangled name `?RenderAudio@SoundEngine@AK@@...`. Its body returns the result of `FUN_00D21980`; the static callgraph role is `caller_and_target`.
- `00D15090` (`SetState`) decompiles with `AK::SoundEngine::SetState` and mangled name `?SetState@SoundEngine@AK@@...`. Its body calls `GetIDFromString` for each string argument, then calls the numeric `SetState` overload if both IDs are nonzero, otherwise returns `0xF`; the static callgraph role is `caller_and_target`.

## Interpretation and claim limits

- **Observed for these four exact addresses:** Ghidra's exact-build decompiler result includes the `AK::SoundEngine` namespace and matching mangled names, and the displayed bodies have API-wrapper/helper-call shapes consistent with the indexed function labels.
- **Inferred, narrow:** these four functions belong to an AK/Wwise SoundEngine API surface in the executable's symbol/decompiler model. The inference rests on exact-address namespace and mangled-name metadata, not solely the bare labels `PostEvent`, `LoadBank`, `RenderAudio`, and `SetState`.
- **Unknown:** who calls these functions at runtime, whether this exact code path executes in a game session, how their internal helpers behave, and whether other matching names share the same owner.
- **Limit:** Ghidra decompiler output is a static analysis view, not original source. The probes do not independently verify the build vendor's symbol provenance and do not justify promoting the remaining Wwise-like name matches in EXP-0072 to the same status.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Full-denominator label/graph triage: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- Probe catalog: [EXP-0073-wwise-function-probes.csv](../research/executable/evidence/EXP-0073-wwise-function-probes.csv)
- Static analysis artifacts: [research/executable](../research/executable/README.md)
