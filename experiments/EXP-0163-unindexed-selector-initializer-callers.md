---
id: EXP-0163
title: Out-of-index selector initializer callers and non-sentinel indices
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do direct calls to selector-table initializer FUN_00426C60 exist outside indexed function bodies, and do any carry non-sentinel indices omitted by the indexed-body census?"
---

# EXP-0163 — Out-of-index selector initializer callers and non-sentinel indices

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the build record, local EXE, and install-manifest row (18,041,856 bytes).
- Scope: direct relative-call encodings in file-backed `.text` resolving to `FUN_00426C60`; classification against exact-build indexed body intervals; raw caller-wrapper arguments, result-byte stores, and second-argument pointer-cell values for calls outside those intervals.
- Exclusions: no function-index edits; no claim that each aligned wrapper is a saved Ghidra function; no runtime execution, selector-table snapshot, or gameplay-reachability claim.
- Tools: Python 3.12.10, `pefile` 2024.8.26, Capstone 5.0.7, build record, install manifest, exact-build `functions.csv`, EXP-0066 [NativeToken-derived catalog](../research/executable/evidence/native-token-dispatch-catalog.csv), and the local Dishonored Recompiled 2013 retail symbol/native exports. External snapshot provenance and row-level joins are recorded in the [crosswalk provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json); [audit script](../tools/audit_unindexed_selector_initializer_calls.py).
- Durable outputs: [1,185 out-of-index wrapper candidates](../research/executable/evidence/EXP-0163-unindexed-selector-initializer-calls.csv), [raw audit provenance/summary](../research/executable/evidence/EXP-0163-unindexed-selector-initializer-calls.json), and compact [retail native crosswalk](../research/executable/evidence/EXP-0163-retail-native-crosswalk.csv).

## Procedure

1. Verify the local EXE SHA-256 against build `10256413` and the exact executable row in the registered install manifest.
2. Load all 72,437 indexed function body intervals. Decode each indexed body with Capstone and collect instruction-aligned direct calls to `0x00426C60`.
3. Scan only file-backed `.text` for `E8 rel32` encodings that resolve to `0x00426C60`; require the raw hits inside indexed body intervals to equal the Capstone-decoded set.
4. For each remaining hit, validate the two immediate pushes, direct relative call, `add esp, 8`, `mov byte ptr [absolute], al`, and `ret`. Require the candidate entry (the first immediate push) to be 16-byte aligned and outside all indexed body intervals.
5. Read the pointer-cell DWORD from file-backed `.data`, require its value to point into `.text`, and record whether it is an exact function-index entry. Compare non-sentinel token values only against the checked-in EXP-0066-derived catalog.
6. Write CSV and JSON provenance with hashes of the EXE, function index, NativeToken catalog, build record, install manifest, and tool.
7. Independently join the two non-sentinel target VAs and indices against the local `natives_2013.csv` and `functions_2013.csv` exports, then join each mangled name/RVA to `match_2012_2013.csv`. Record the selected rows and source-file hashes without importing the full external exports.

## Observations

- The raw `.text` scan found 2,267 `E8 rel32` candidates resolving to `0x00426C60`. The 1,082 candidates inside indexed body intervals exactly equal the direct call instructions decoded from those indexed bodies.
- The other 1,185 candidates lie outside every indexed body interval. All 1,185 have the validated immediate-push/call/stack-cleanup/result-byte-store/return sequence; each proposed entry is 16-byte aligned. Every second-argument cell is file-backed `.data`, and every DWORD in those cells points into `.text`. The function index is unchanged.
- The 1,185 wrapper candidates pass 1,183 sentinel values (`0xFFFFFFFF`) and two non-sentinel values: `0x181` at callsite `0x00F720BA` and `0x180` at `0x00F7D6BA`.
- For `0x181`, pointer cell `0x01286C78` contains `0x0058C820`. That target is in `.text` but is neither an indexed entry nor inside an indexed body. Raw disassembly at the target begins `mov eax, [ecx+0x1AC]` and reaches `ret 8` at `0x0058C848`; it remains an unindexed target candidate without assigned ownership or semantics.
- For `0x180`, pointer cell `0x012A0268` contains `0x006CC1D0`, an exact indexed entry named `FUN_006CC1D0`. No semantic role is inferred from that relation.
- **Independent retail-export crosswalk:** a local Dishonored Recompiled snapshot's `natives_2013.csv` maps `(native_index=385, VA=0x0058C820)` to `AActor::PollFinishAnim`, and `(native_index=384, VA=0x006CC1D0)` to `AActor::PollSleep`. `functions_2013.csv` independently has the same VA, RVA, size, and mangled exec name for both. The matching rows in `match_2012_2013.csv` show byte-match ratio `1.000` and equal 2012/2013 sizes (43 and 56 bytes respectively). The compact row-level joins and SHA-256s are preserved in [crosswalk CSV](../research/executable/evidence/EXP-0163-retail-native-crosswalk.csv) and [crosswalk provenance](../research/executable/evidence/EXP-0163-retail-native-crosswalk.json). This strengthens the static association of these registrations with those named AActor native exec bindings; it does not prove the wrappers execute or identify gameplay effects.
- Neither `0x180` nor `0x181` occurs as a token value in the checked-in 207-row EXP-0066-derived NativeToken catalog. This is a bounded catalog absence, not proof that no package or runtime registry contains either value.
- The two sampled Core consumers in EXP-0161 read a single byte from the bytecode cursor; these observed `0x180`/`0x181` registration arguments are greater than `0xFF` and therefore are not representable by that byte read. This does not exclude other table consumers or establish what the two values mean.
- The CSV records each wrapper candidate, callsite, token encoding/value, pointer cell, target, result-byte address, and exact-index-entry status. The JSON records source hashes, counts, and limits.

## Interpretation and claim limits

- **Confirmed, static call pattern:** these 1,185 outside-index byte sequences encode direct relative calls to `FUN_00426C60` with the documented wrapper shape. The alignment and return patterns support wrapper-entry candidates; the Ghidra function index remains unchanged.
- **Observed, non-sentinel arguments:** two wrappers pass `0x180` and `0x181` with pointer cells whose raw DWORDs are `0x006CC1D0` and `0x0058C820`. EXP-0160 records that the helper's non-sentinel path writes the pointer value to the indexed selector table when executed. This does not prove either caller executes.
- **Inferred from independent static exports:** `0x180` is the AActor `PollSleep` native binding and `0x181` is the AActor `PollFinishAnim` native binding at the joined target addresses. The third-party export describes how it extracts numbered GNatives registration indices from the retail named database; the selected VA/index pairs agree exactly across its native and function exports. Its `functions_2013.csv` names were propagated from a 2012 PDB, but the selected rows have exact byte matches and equal sizes in the 2012/2013 match file. The 2012 PDB remains a name donor, not retail-layout authority.
- **Unknown:** whether another consumer reads these selector slots, whether either wrapper or target executes, and what runtime/gameplay effect the bindings have. Their absence from EXP-0066 remains limited to that 207-row catalog.
- **Limit:** raw `E8` scanning by itself is not instruction-boundary proof. The indexed-side set was checked against Capstone body disassembly; every outside candidate was separately validated against its full argument/call/postlude byte pattern, aligned candidate entry, `.data` pointer cell, and `.text` target. These checks support static wrapper candidates but do not establish saved function boundaries or semantic ownership.

## Reproduction

With the registered local build present:

```powershell
python tools\audit_unindexed_selector_initializer_calls.py
```

The script fails if the build/manifest identity, function count, indexed call cross-check, candidate counts, wrapper pattern, alignment, pointer-section checks, or catalog-absence check changes. It writes the raw audit artifacts and does not alter `functions.csv`, the Ghidra project, or the local knowledge database. The compact crosswalk is a separately preserved extract from the local external snapshot; its source-file hashes and limits are recorded alongside it.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Indexed-body initializer and Engine token census: [EXP-0160](EXP-0160-native-selector-table-static-registration-census.md)
- Core catalog and sampled byte consumers: [EXP-0161](EXP-0161-core-native-selector-consumer-samples.md)
- Static boundaries for the 17 unindexed Core catalog targets: [EXP-0162](EXP-0162-core-native-unindexed-target-boundaries.md)
- NativeToken-derived catalog: [native-token-dispatch-catalog.csv](../research/executable/evidence/native-token-dispatch-catalog.csv)
- Script: [audit_unindexed_selector_initializer_calls.py](../tools/audit_unindexed_selector_initializer_calls.py)
