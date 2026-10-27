---
id: EXP-0109
title: Audio record producer cohort and visible dispatcher case coverage
experiment_status: done
claim_status: observed
build: "10256413"
question: How much of the visible FUN_00D20940 discriminator switch has a statically observed producer route into the shared queue writer?
---

# EXP-0109 — Audio record producer cohort and visible dispatcher case coverage

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: reconcile direct callsites to `FUN_00D21A00` against producer discriminator stores in 48 exact-build Ghidra decompilations, the function-triage labels, and visible top-level cases in `FUN_00D20940`.
- Exclusions: runtime reachability, operation frequency, true API ownership for address-named callers, exhaustive record field typing, and actual audio behavior. Decompiled pseudocode is analysis output, not original source.
- Durable outputs: [50-row producer/callsite cohort](../research/executable/evidence/EXP-0109-audio-record-producer-caller-cohort.csv), [37-case coverage table](../research/executable/evidence/EXP-0109-audio-record-dispatch-case-coverage.csv), and [count reconciliation](../research/executable/evidence/EXP-0109-audio-record-dispatch-case-coverage.json).

## Procedure

1. Confirm the current build registry SHA, read `docs/research-status.md` and the Blink activation graph, and inspect EXP-0108.
2. Query the exact-build callgraph SQLite for `kind='call' AND to_addr='00D21A00'`; decompile the 48 unique callers in one read-only Ghidra headless run using `DecompileAddressBatch.java`.
3. For each caller, read the 16-bit discriminator written at record offset +2 and associate it with each direct callsite. Cross-check audio-name candidate labels against EXP-0072 triage.
4. Compare the tags with all explicit top-level cases in the cached `FUN_00D20940` decompile. Review each case body and record only visible direct helper calls, inline state changes, and nested dispatches; retain RenderAudio's tag-0 path from EXP-0107/0108 as a separate producer route.
5. Run `python tools/audio_record_producer_cohort.py` to regenerate the three durable tables and assertions from the exact-build DB, triage CSV, and local read-only batch decompile at `assets/extracted/audio-command-producers-decompile.txt`.

## Observations

- The exact-build callgraph DB metadata identifies build `10256413` and the expected executable SHA. It records 50 direct callsite edges to `FUN_00D21A00` from 48 unique caller functions.
- `function_dossier(00D21A00)` returns `count=30` and 30 caller items. The same DB query returns 50 edge rows; therefore the dossier result is a truncated view for this address and must not be used as the cohort denominator.
- Of 48 callers, 41 intersect the EXP-0072 `audio_middleware_candidate` name-label bucket. That bucket contains 181 functions total. Seven callers have address-derived/unknown candidate labels; this label join is not proof of middleware ownership.
- The 48 bodies contain 50 discriminator-store/callsite matches covering 36 distinct values. Every value matches an explicit visible case in `FUN_00D20940`.
- `FUN_00D20940` exposes 37 top-level case values: `0`, `1`, `2`, `3`, `5`, `6`, `7`, `8`, `0x0A`–`0x0E`, `0x10`–`0x16`, `0x18`–`0x26`, `0x28`, and `0x29` (with gaps as shown in the coverage CSV). The 36 queue-writer tags plus the separate RenderAudio marker route for case `0` account for all 37 visible values.
- The per-case CSV now lists producer labels, visible helper calls, and a concise description of the case body, including nested dispatch or inline mutations where present. This is a description of the decompiler output, not validated source semantics; indirect calls and fields not followed into callees remain unresolved.

## Interpretation and claim limits

- **Observed:** the exact-build static corpus connects a producer discriminator route to every explicit top-level case visible in the dispatcher decompile. The shared writer cohort has 50 direct callsite edges / 48 unique functions; 36 unique tags originate in that cohort and tag 0 is accounted for by the separate RenderAudio route. For each of the 37 visible cases the catalog now records the visible handler calls or inline operation summary.
- **Observed:** the knowledge dossier's 30-item caller listing is incomplete relative to the local exact-build edge table. The SQL count is the denominator used here; this does not establish the completeness of other dossier responses.
- **Unknown:** whether these paths execute in a real session, all indirect callers/alternate producers, field meanings beyond directly inspected wrappers, and any audio outcome.
- **Limit:** decompiler struct/local names vary; the reproduction script asserts the expected tag/callsite counts and the exact-build metadata, but results remain based on static analysis. The dispatcher has the Ghidra jumptable/spacebase warning already recorded in EXP-0108.

## Reproduction

Run from the repository root after producing `assets/extracted/audio-command-producers-decompile.txt` with the checked-in `DecompileAddressBatch.java` through read-only Ghidra headless mode:

```powershell
python tools/audio_record_producer_cohort.py
```

The script checks the expected build/hash, 50 edges, 48 callers, 181 audio-name candidates, 36 queue-writer tags, and full accounting for the 37 explicit cases. The local decompile dump is an ignored intermediate and is not committed. Handler summaries in `CASE_OPERATIONS` are manually reviewed notes from the build-matched cached `FUN_00D20940` pseudocode in `knowledge/cache/decompiles/00D20940.json`; the script asserts that every visible case has one summary entry.

## Links

- [EXP-0108 reader and selected opcode matches](EXP-0108-audio-record-consumer-opcode-matches.md)
- [EXP-0107 RenderAudio shared-buffer link](EXP-0107-renderaudio-shared-buffer-link.md)
- [EXP-0072 function triage](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- [Reproduction script](../tools/audio_record_producer_cohort.py)
- [Batch decompile script](../research/executable/scripts/DecompileAddressBatch.java)
