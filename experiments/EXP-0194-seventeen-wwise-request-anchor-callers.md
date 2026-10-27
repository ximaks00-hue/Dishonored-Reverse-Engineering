---
id: EXP-0194
title: Seventeen Wwise caller bodies directly reference the reviewed request anchor
experiment_status: done
claim_status: observed
build: "10256413"
question: Do the remaining unreviewed callers of the EXP-0128 request anchor contain direct calls to the same exact-build function, and what additional direct-call structure is visible in their bodies?
---

# EXP-0194 — Seventeen Wwise caller bodies directly reference the reviewed request anchor

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: review the 17 previously unreviewed indexed callers in the EXP-0128/EXP-0111 caller set for `FUN_00D27810`. Each exact indexed byte range was hashed and fully decoded as x86-32.
- Exclusions: function-name labels from the triage catalog are candidate metadata; this EXP does not independently establish Wwise source identity, wrapper semantics, caller reachability, queue behavior, audio behavior, or runtime execution. A direct call edge is not a confirmed dataflow edge and does not advance L3.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping and exact-build `functions.csv`.
- Durable outputs: [17-row body review](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0194.csv), [137-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0194.csv), and [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0194.json). Per-function hashes, indexed sizes, file offsets, direct-call sites, and tool provenance are recorded in the evidence CSV.

## Procedure

1. Verify the configured executable SHA-256 against the build record and load the exact-build function index and EXP-0193 cumulative review overlay.
2. Select the 17 exact function starts in the indexed `FUN_00D27810` caller set that were absent from the cumulative body-review overlay. Three other direct callers in this bounded caller set had already been reviewed; this batch does not recount them.
3. Map each indexed VA and size through the PE32 image, hash the full byte range, and decode the full range with Capstone x86-32.
4. Inspect direct immediate call operands and record every direct call site/target. Keep indirect calls as unresolved indirect sites.
5. Add the 17 observations to the cumulative manual body-review overlay without adding semantic, dataflow, or runtime claims.

## Observations

- The executable hash matches build `10256413`; all 17 addresses are exact starts in the 72,437-row internal function index and were absent from the 120-row EXP-0193 cumulative overlay.
- All 17 indexed ranges decode completely with no uncovered bytes. Their sizes range from 92 to 310 bytes. Every body contains exactly one direct call to `0x00D27810`; the individual call instruction address and raw SHA-256 are in the evidence CSV.
- The 17 functions are `00D144E0`, `00D14600`, `00D146B0`, `00D14750`, `00D147D0`, `00D148C0`, `00D151D0`, `00D15300`, `00D153C0`, `00D15450`, `00D154F0`, `00D155D0`, `00D15660`, `00D159A0`, `00D15AA0`, `00D15BA0`, and `00D15CE0`.
- Other direct calls visible in this cohort include targets `0x00D13590`, `0x00D148C0`, `0x009AE3D0`, `0x00D15260`, `0x00D5CF80`, `0x00D14D60`, `0x00D14DF0`, `0x00D14310`, and `0x00D143F0`. Exact sites and full target lists are recorded per row. Several bodies also contain an indirect call through memory at `0x00F941D8`; its target and role were not resolved.
- The cumulative manual body-review overlay rises from 120 to 137 unique functions, or 0.189130% of the internal index. This cohort is outside EXP-0139, so that set remains at 89/254 body-reviewed with 165 pending. The EXP adds zero confirmed semantic claims and zero runtime-verified functions.

## Interpretation and claim limits

- **Observed:** each of these 17 exact-build body ranges contains one direct call to `0x00D27810`; the raw call sites, other direct calls, complete decode lengths, and per-body SHA-256 values are recorded.
- **Observed:** the selected addresses belong to the call-site set already associated with `FUN_00D27810` in EXP-0128 and EXP-0111. The machine-code call instructions independently reproduce the anchor edge for these bodies.
- **Unknown:** operation meanings, argument/record semantics, success and failure behavior, ownership of indirect targets, and runtime reachability.
- **Not established:** triage labels such as `LoadBank`, `UnloadBank`, `PrepareEvent`, and `PrepareGameSyncs` are symbol/name-match metadata, not implementation proof. Similar callers do not by themselves prove a shared source implementation or dataflow relation.

## Reproduction and limitations

From the repository root, with Python, pefile, and Capstone installed:

1. Verify the executable hash in the summary against the registered build record.
2. Resolve each evidence-row address and size in `research/executable/functions.csv`; map `RVA = VA - 0x00400000` through the PE section table.
3. Hash the full indexed body and compare with `raw_body_sha256`; decode in x86-32 mode and verify decoded instruction sizes cover the entire range.
4. Inspect immediate `call` operands and compare call sites/targets with `direct_call_sites_and_targets`; indirect operands remain unresolved.
5. Verify the 17 rows are unique and absent from EXP-0193, and that the cumulative overlay contains 137 unique addresses.

This was read-only raw-byte analysis. No Ghidra project, game process, or runtime state was changed or used.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Existing request-path analysis: [EXP-0128](EXP-0128-audio-request-queue-submission.md)
- Existing caller cohort: [EXP-0111](EXP-0111-audio-api-direct-callee-cohort.md)
- Previous function batch: [EXP-0193](EXP-0193-twenty-short-native-wrapper-family-review.md)
- Function evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
