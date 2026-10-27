---
id: EXP-0156
title: "Three DishonoredGame exports share a frame-decoding adapter"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What can be established from the three DishonoredGame zero-token export joins to 0x009F53F0 and its exact-build machine code?"
---

# EXP-0156 — Three DishonoredGame exports share a frame-decoding adapter

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect one indexed `.text` target with three EXP-0139 class-table edges, verify export metadata and raw x86 effects, and record a limited L1 role candidate.
- Exclusions: no claim of runtime dispatch/reachability, concrete receiver ownership, gameplay behavior, decoder-table meaning, or semantic interpretation of vtable slot `+0x3AC`.
- Inputs: EXP-0139 candidate catalog and raw join; exact-build function index and executable; UELib JSONL census; build-scoped local decompilation cache.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0156.csv), [48-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0156.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0156.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the exact build ID and EXE SHA-256.
2. Select EXP-0139 rows for `0x009F53F0`; inspect the three joined UELib exports and their package, declaration, NativeFlag, NativeToken, and script-size fields.
3. Verify the function-index start and size, map VA to PE RVA/raw offset, hash the exact 96-byte range, and inspect the x86 instructions.
4. Compare the machine-code observations with the cached decompilation only as a secondary analysis aid; retain the cache provenance limitations.
5. Add one inferred static role candidate to the manual review overlay; leave subsystem and runtime status unresolved.

## Observations

- The EXP-0139 candidate catalog maps three class-table edges to indexed start `0x009F53F0` (`FUN_009f53f0`, 96 bytes): `DishonoredSpawner.OnStartSpawn(DisSeqAct_StartSpawn _pAction)`, `DisRiverKrust.OnRiverKrustDisable(DisSeqAct_RiverKrustDisable _pAction)`, and `DisDLC07GravehoundSpawner.OnStartSpawn(DisSeqAct_StartSpawn _pAction)`. Each source export is marked NativeFlag=true and NativeToken=0; each has script size 7. All are in `DishonoredGame.upk` and name their class-specific `exec...` wrapper.
- The source JSONL snapshot `assets/extracted/uelib-census/20261026-230210-253-c7ad73d8/007-DishonoredGame/DishonoredGame.upk.functions.jsonl` has SHA-256 `09F41841F403B8A1CA11E11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`. Its 1-based lines 814, 839, and 961 contain the three matching records, respectively. The package source SHA recorded in each is `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`.
- The exact local EXE SHA matches the build record. PE mapping places VA `0x009F53F0` at RVA `0x005F53F0`, file offset `0x005F47F0`, section `.text`. The 96-byte range SHA-256 is `BF4E7C984FE150A3A702BCDA843B9694E5F59A93EE15DB587D8A6CC9D79F8234`.
- Raw x86 initializes a local dword to zero; reads one byte through the frame cursor at `[frame+0x18]`; advances that cursor; and calls a function pointer selected from the table based at `0x014068F0`, passing the frame and local-dword address. It then advances the cursor by one more byte. If the next byte is `0x41` (`'A'`), it consumes that byte and calls the pointer at `0x014069F4` with the frame and zero.
- The function loads the receiver vtable from the incoming `this` pointer, reads the pointer at byte displacement `+0x3AC`, and calls it with `this` in ECX and the local dword as one stack argument. The function returns with `ret 8`.
- The local decompilation cache entry identifies build ID `10256413` and the matching executable SHA, but does not record Ghidra version/options, analyzer revision, or analysis-project revision. Therefore the raw byte-range hash and direct x86 inspection are the primary body evidence; pseudocode is corroborative only.
- The prior EXP-0155 cumulative overlay has 47 unique reviewed addresses and does not contain `009F53F0`.

## Interpretation and claim limits

- **Observed:** three exact class-table/name/export joins point to this indexed function start, and their declarations each contain one object parameter.
- **Observed:** the raw body consumes frame bytes, dispatches through a byte-indexed table, optionally consumes an `A` marker and invokes another indirect helper, then makes a receiver virtual call using a local dword.
- **Inferred, limited:** this is a shared single-value native-exec frame-decoding adapter candidate for the three joined exports. The machine-code shape and joins support the candidate role but do not establish runtime table dispatch.
- **Unknown:** what the decoded dword represents; what the decoder table and optional marker mean; which concrete object owns the receiver; what virtual slot `+0x3AC` does; whether any joined path executes at runtime; and any higher-level gameplay effect or subsystem assignment.

## Reproduction and limitations

1. Filter `research/executable/evidence/function-triage/native-class-table-handler-candidates-EXP-0139.csv` for address `009F53F0` and inspect the matching source records at lines 814, 839, and 961 of the identified JSONL snapshot.
2. Verify the executable SHA-256 and map VA to RVA using image base `0x00400000` and the PE section table; hash 96 bytes from file offset `0x005F47F0`.
3. Disassemble those bytes as 32-bit x86 and check the frame cursor updates, indirect calls, receiver register, stack argument, and `ret 8`.
4. Verify the new review row is additive to the EXP-0155 cumulative overlay and does not change the function-index denominator.

The UELib snapshot is local and ignored by Git; its file hash, package hash, and source lines are recorded above. Static class-table joins and raw instructions do not establish runtime reachability. No game launch or runtime experiment was performed. The cache's incomplete analyzer/project provenance remains a reproducibility limitation.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- Prior overlay review: [EXP-0155](EXP-0155-set-enabled-shared-native-adapter.md)
