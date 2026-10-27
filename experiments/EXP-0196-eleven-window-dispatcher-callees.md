---
id: EXP-0196
title: Eleven unreviewed functions are direct callees of the reviewed window dispatcher
experiment_status: done
claim_status: observed
build: "10256413"
question: What exact-build caller/callee edges and raw body shapes can be established for the remaining unreviewed targets directly called by FUN_009C8970?
---

# EXP-0196 — Eleven unreviewed functions are direct callees of the reviewed window dispatcher

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: raw-body review of 11 previously unreviewed exact-build indexed functions called directly from `FUN_009C8970`, whose static dispatcher role is described in EXP-0127. Also re-decode and hash the complete 4,047-byte parent body to verify the selected caller-to-target edges.
- Exclusions: selection under the prior EXP-0127 dispatcher analysis does not establish the target functions' message-case assignment, callback ABI, native ownership, semantics, or runtime reachability. Candidate labels remain catalog metadata. No L3/L4 claims are added.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping and exact-build `functions.csv`.
- Durable outputs: [11-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0196.csv), [168-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0196.csv), and [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0196.json). These record per-body hashes, exact sizes, full decode shape, outgoing calls, parent call sites, and tool provenance.

## Procedure

1. Verify the executable hash against the build record and load the exact-build function index and EXP-0195 cumulative overlay.
2. Decode the complete indexed body of `FUN_009C8970` and record direct immediate calls to the selected target starts.
3. Confirm each selected target is an exact function start and absent from the EXP-0195 cumulative manual-review overlay.
4. Hash and fully decode each target's indexed body as x86-32. Record direct call sites/targets and indirect-call operands separately; do not assign targets to indirect calls.
5. Append the 11 target-body observations to the cumulative overlay without promoting dispatcher membership or candidate labels into semantic claims.

## Observations

- The executable hash matches build `10256413`. The exact-build function index contains 72,437 internal starts. All 11 target addresses below are indexed starts and were absent from EXP-0195.
- The indexed parent `FUN_009C8970` has size 4,047 bytes, decodes completely to 1,324 x86-32 instructions, and hashes to `67D69BAFC6A2268CB2A966421B08A60B01E6A9827C54A61D445567CBF5A59EE3`.
- Raw decoding of that parent body confirms 13 unique direct-call targets that are exact indexed starts; two were already in the prior review overlay. The 11 new targets account for 42 direct call instructions, with several targets called at multiple sites. All `(site,target)` pairs are recorded in the EXP-0196 evidence CSV and provenance summary.
- All 11 target bodies decode completely, from 21 to 490 bytes. Their exact per-body SHA-256 values and outgoing calls are recorded in the evidence CSV. No single normalized body template is evident across the sampled targets; seven contain indirect calls whose destinations remain unresolved.
- The cumulative manual body-review overlay rises from 157 to 168 unique functions, or 0.231926% of the internal index. The batch adds zero confirmed semantic claims and zero runtime-verified functions.

### Target set

| Exact-build VA | Indexed bytes | Parent direct call sites | Candidate label source |
| --- | ---: | --- | --- |
| `00428B50` | 490 | `009C8AEC`, `009C9379`, `009C93B7`, `009C93F8`, `009C943C`, `009C9792`, `009C97D0`, `009C9811`, `009C9855` | EXP-0072/callgraph label; unresolved role |
| `009C6380` | 268 | `009C8BE1`, `009C8BEF`, `009C8BFD`, `009C8C0B`, `009C8C19`, `009C922A`, `009C9238`, `009C9246`, `009C9254`, `009C9262`, `009C9736` | EXP-0072/callgraph label; unresolved role |
| `009C3A10` | 171 | `009C8C89`, `009C8CBB`, `009C8CE4`, `009C8D0D`, `009C990D` | EXP-0072/callgraph label; unresolved role |
| `009C64B0` | 56 | `009C8E28`, `009C9086` | EXP-0072/callgraph label; unresolved role |
| `00401750` | 35 | `009C8E51`, `009C8E70` | EXP-0072/callgraph label; unresolved role |
| `009C3AC0` | 21 | `009C8F94`, `009C90C9`, `009C9127`, `009C92BA`, `009C94AF`, `009C98C8` | EXP-0072/callgraph label; unresolved role |
| `009C6170` | 240 | `009C92AB` | EXP-0072/callgraph label; unresolved role |
| `009C6260` | 255 | `009C9312` | EXP-0072/callgraph label; unresolved role |
| `009C3D40` | 66 | `009C9452`, `009C986B` | EXP-0072/callgraph label; unresolved role |
| `00401150` | 43 | `009C9488`, `009C98A1` | EXP-0072/callgraph label; unresolved role |
| `005518C0` | 71 | `009C9926` | EXP-0072/callgraph label; unresolved role |

## Interpretation and claim limits

- **Observed:** each target is reached by at least one direct near-call instruction in the decoded body of `FUN_009C8970`; the site and exact target are recorded. The 11 target bodies are individually hashed and fully decoded.
- **Observed:** three target bodies have unresolved indirect-call instructions; other direct outgoing calls are separately recorded and do not establish target purpose.
- **Unknown:** which input/message branches reach each call site, the target functions' ownership and purpose, calling-convention details for indirect interfaces, and runtime execution.
- **Not established:** “dispatcher callee” means a static call edge in one body. It does not prove an OS callback, user-visible input behavior, or semantic relationship among the callees.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify the executable SHA-256 against the build record.
2. Resolve each VA and size in `research/executable/functions.csv`; map `RVA = VA - 0x00400000` through the PE sections.
3. Verify the parent dispatcher hash and fully decode the 4,047-byte body. For each tabled site, verify the direct call target matches the table row.
4. Verify every target-body hash and full decode length against the evidence CSV. Compare direct calls exactly; keep indirect operands unresolved.
5. Verify that all 11 target addresses were absent from EXP-0195 and that the cumulative overlay contains 168 unique addresses.

This was read-only static byte analysis. No Ghidra project, game process, or runtime state was changed or used.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent dispatcher analysis: [EXP-0127](EXP-0127-windows-input-message-dispatch.md)
- Previous batch: [EXP-0195](EXP-0195-nineteen-audio-api-callers-to-shared-anchor.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
