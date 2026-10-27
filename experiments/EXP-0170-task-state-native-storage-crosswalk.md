---
id: EXP-0170
title: Task-state native storage and setter crosswalk
experiment_status: done
claim_status: inferred
build: "10256413"
question: "What does the exact-build native code at candidate SetTaskState addresses do, and how strongly do donor symbols map to those functions?"
---

# EXP-0170 — Task-state native storage and setter crosswalk

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: three exact-build indexed functions at `0x00B86840`, `0x00AC17B0`, and `0x00AC17A0`; donor symbol rows from a local Dishonored Recompiled 2013 export and 2012→2013 matcher.
- Exclusions: no Ghidra renaming or project mutation; no claims about Kismet reachability, runtime execution, exact enum meanings, task completion semantics, or helper behavior.
- Tools: exact-build function index; read-only `mcp__dishonored_static__decompile_function`; Python CSV inspection of `match_2012_2013.csv` and `functions_2013.csv`; local donor snapshot under `D:\Dishonored\10_EDITOR_RESTORATION\history\attempt-2_EditorWork_2026-10-08\dishonoredrecompiled\resources\docs\symbols`.
- Durable decompile outputs: exact-build, SHA-bound cache entries [00B86840](../knowledge/cache/decompiles/00B86840.json), [00AC17B0](../knowledge/cache/decompiles/00AC17B0.json), and [00AC17A0](../knowledge/cache/decompiles/00AC17A0.json). These are generated local evidence and are not included in the public Git source of truth.

## Procedure

1. Verify the registered build identity and resolve the three VAs in `research/executable/functions.csv`.
2. Inspect the donor match rows for `HandleTaskInstance`, `GetTaskState`, and `SetTaskState`, preserving method, ratio, and function sizes.
3. Decompile the three indexed retail functions through the read-only static-analysis gateway and preserve its returned pseudocode and SHA/build-bound cache records.
4. Compare the observed retail call/data flow with the donor names without renaming functions.

## Observations

- The exact-build index contains `0x00B86840` size 23, `0x00AC17B0` size 51, and `0x00AC17A0` size 5. Each size equals the corresponding 2013 export size.
- The donor matcher maps 2012 RVA `0x7CBB60` to 2013 RVA `0x786840` for `UDisSeqAct_SetTaskState::HandleTaskInstance`, method `bytes`, ratio `1.000`, sizes `23/23`.
- It maps `UDishonoredTask_Base::SetTaskState` from 2012 RVA `0x721F90` to 2013 RVA `0x6C17B0`, method `bytes`, ratio `1.000`, sizes `51/51`. `GetTaskState` at 2013 RVA `0x6C17A0` is mapped by method `callee`, ratio `1.000`, sizes `5/5`.
- Retail pseudocode at `0x00B86840` reads one byte at action-object offset `+0xFC` and passes it to `FUN_00AC17B0` with the action receiver as the other argument.
- Retail pseudocode at `0x00AC17B0` compares its second argument with a byte at task-object offset `+0x5D`; if different, it writes that byte. When the new value is `1`, it calls `FUN_00BBE6A0(3, task)`, then calls `FUN_00BBE6A0(5, task)` for every changed value.
- Retail pseudocode at `0x00AC17A0` returns the byte at the same task-object offset `+0x5D`.
- All three decompile cache records bind to the registered executable SHA-256 and build ID `10256413`.

## Interpretation

- **Observed:** the indexed retail functions implement a byte-valued task field read/write path. The setter only writes and dispatches helper calls when the value changes; helper code `3` is conditional on new value `1`, helper code `5` follows every changed value.
- **Inferred, candidate symbol association:** the action handler at `0x00B86840` corresponds to donor `UDisSeqAct_SetTaskState::HandleTaskInstance`; `0x00AC17B0` and `0x00AC17A0` correspond to donor `SetTaskState` and `GetTaskState`. The local index confirms exact starts and matching sizes, while the donor matcher reports a byte-perfect row for the handler and setter. The getter row is callee-derived, not byte-matched.
- **Unknown:** which enum label maps to each byte; whether `1` means a particular active/completed state in this retail build; what helper codes `3` and `5` do; whether the Boyle Kismet candidate nodes call these exact functions at runtime; and whether the action field at `+0xFC` is always serialized `m_TaskState`.
- **Limit:** Ghidra pseudocode is a readable rendering of machine code, not original source. Donor symbol names are candidate labels transferred from 2012 through a 2013 matcher; exact-build bytes were not independently compared to the donor binary in this experiment.

## Reproduction

1. Confirm the build SHA in `research/builds/BUILD-STEAM-10256413/build.md`.
2. Resolve the three indexed VAs and sizes in `research/executable/functions.csv`.
3. Re-run read-only decompilation for each address with the configured exact-build static gateway; verify returned `exe_sha256` and `build_id` in each cache output.
4. Recheck donor match rows in the recorded local snapshot and compare pseudocode only as an interpretation aid.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
- Related Kismet lead: [EXP-0169 Boyle task-state crosswalk](EXP-0169-boyle-assassination-task-state-retail-crosswalk.md)
- Prior donor-symbol method: [EXP-0164](EXP-0164-blink-pdb-symbol-candidate-crosswalk.md)
- Open question: inspect `FUN_00BBE6A0` and determine enum value mapping without importing archive-only claims.
