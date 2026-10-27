---
id: EXP-0195
title: Nineteen compact audio API caller bodies route through one indexed anchor
experiment_status: done
claim_status: observed
build: "10256413"
question: What body-level call structure is present in the low-cost unreviewed caller neighborhood around FUN_00D21A00?
---

# EXP-0195 — Nineteen compact audio API caller bodies route through one indexed anchor

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: raw-body review of the 44-byte indexed anchor `FUN_00D21A00` and 19 previously unreviewed exact-build direct callers selected from the EXP-0111 audio API/direct-callee neighborhood.
- Exclusions: EXP-0111 and EXP-0072 names/signatures are candidate labels from symbol matching, not independently established source identities. Direct calls are static call edges, not proof of argument meaning, dataflow, runtime reachability, or audio behavior. No L3/L4 claims are added.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping and exact-build `functions.csv`.
- Durable outputs: [20-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0195.csv), [157-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0195.csv), and [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0195.json). Per-function hashes, indexed sizes, file offsets, direct-call sites, and tool provenance are recorded in the evidence CSV.

## Procedure

1. Verify the executable hash against the registered build and load the exact-build function index and EXP-0194 cumulative overlay.
2. Select the anchor `00D21A00` and 19 small caller bodies from the EXP-0111 candidate caller set. Confirm all 20 function starts are absent from the prior manual body-review overlay.
3. Map each indexed VA and size through the PE32 image, hash the full byte range, and decode the full range in x86-32 mode.
4. Inspect direct immediate call operands and record all direct sites/targets. Record indirect-call operands as unresolved indirect calls.
5. Append the 20 body observations to the cumulative review overlay without assigning candidate API labels as semantic facts.

## Observations

- The executable SHA-256 matches build `10256413`; all selected addresses are exact starts in the 72,437-row internal function index and were absent from the EXP-0194 cumulative overlay.
- Capstone completely decodes each indexed body. The 20 bodies range from 44 to 82 bytes; each raw byte range has an individual SHA-256 in the evidence CSV.
- The anchor body at `00D21A00` is 44 bytes and contains a direct call `00D21A17 -> 00D218F0`, plus indirect calls through memory operands `[0x00F94164]` and `[0x00F9416C]`. The indirect targets and all three operations' roles remain unresolved.
- Each of the 19 selected caller bodies contains exactly one direct call to `00D21A00`. In the observed callers, additional direct calls include `00A70F70`, `00566120`, `0076C330`, `00D1E3D0`, and `00A1F950`; individual sites and targets are in the evidence CSV.
- The EXP-0111/EXP-0072 candidate labels attached to this bounded set are: `SetPanningRule` (`00D13F10`), `StopAll` (`00D14B40`), `UnregisterAllGameObj` (`00D14220`), `SetActiveListeners` (`00D13890`), `SetListenerPipeline` (`00D139A0`), `SetSwitch` (`00D13A80`), `PostTrigger` (`00D13AD0`), `SetGameObjectDryLevelValue` (`00D13CA0`), `BypassEnvironment` (`00D13D40`), `SetPlayerListener` (`00D14C90`), `SetListenerScalingFactor` (`00D13840`), `SetPlayerVolume` (`00D14CD0`), `UnregisterGameObj` (`00D141E0`), `SetEffect` (`00D149F0`), `StopPlayingID` (`00D14B80`), `SetListenerPosition` (`00D138D0`), `SetObjectObstructionAndOcclusion` (`00D13D80`), `RegisterGameObj` (`00D14190`), and `SetState` (`00D15040`). These labels remain name-match metadata.
- Cumulative manual body-review coverage rises from 137 to 157 unique functions, or 0.216740% of the internal index. This batch adds zero confirmed semantic claims and zero runtime-verified functions.

## Interpretation and claim limits

- **Observed:** 19 individually hashed, completely decoded caller bodies contain one direct call each to the indexed address `00D21A00`; the anchor body itself contains a direct call to `00D218F0` and two indirect calls through recorded global memory operands.
- **Observed:** several callers also reference the same helper addresses, but this does not identify those helpers or establish that the caller arguments share a semantic type.
- **Unknown:** the operation represented by `00D21A00`, identities/roles of global indirect targets, parameter meanings, status semantics, subsystem ownership, and runtime reachability.
- **Not established:** names such as `SetSwitch` or `RegisterGameObj` establish neither the implementation nor its runtime effects. A direct call edge does not qualify as a confirmed dataflow edge under the L0–L4 model.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify the executable hash against the build record.
2. Resolve every evidence-row VA and size in `research/executable/functions.csv`; map `RVA = VA - 0x00400000` through the PE section table.
3. Verify the per-body SHA-256 and that Capstone's decoded instruction sizes cover the full indexed range.
4. Compare each direct call site/target with the evidence CSV. The anchor must call `00D218F0`, and each of the 19 selected caller bodies must call `00D21A00` exactly once.
5. Verify the 20 rows are unique, were absent from EXP-0194, and the cumulative overlay contains 157 unique addresses.

This was read-only raw-byte analysis. No Ghidra project, game process, or runtime state was changed or used.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Candidate caller catalog: [EXP-0111](EXP-0111-audio-api-direct-callee-cohort.md)
- Broader static audio slice: [EXP-0110](EXP-0110-audio-api-candidate-cohort.md)
- Previous function batch: [EXP-0194](EXP-0194-seventeen-wwise-request-anchor-callers.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
