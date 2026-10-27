---
id: EXP-0138
title: Raw PE validation of selected native class-table name and code pointers
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do the class-table pointer symbols extracted in EXP-0137 address raw name/code pointer pairs in the exact-build PE, and how many code targets match the indexed function starts?"
---

# EXP-0138 — Raw PE validation of selected native class-table name and code pointers

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: raw PE inspection at the 332 table-pointer symbol suffix addresses preserved by [EXP-0137](EXP-0137-native-class-registration-group-uelib-join.md); decode the adjacent name and target DWORDs and compare target VAs to the exact-build Ghidra function index.
- Exclusions: no table length or sibling-entry scan, no function recovery for unindexed targets, no runtime execution, and no proof of table consumption, NativeToken conversion, or dispatch.
- Tools and inputs: Python 3, `pefile`, exact-build executable and `files.csv`, `research/executable/functions.csv`, EXP-0137 CSV; [validator](../tools/validate_native_class_table_pointer_targets.py).
- Durable outputs: [per-key raw pointer audit](../research/executable/evidence/EXP-0138-native-class-table-raw-pointer-validation.csv) and [summary](../research/executable/evidence/EXP-0138-native-class-table-raw-pointer-validation-summary.json).

## Procedure

1. Re-read research status, Blink activation graph, and the exact build record. Require the recorded build ID and executable SHA-256.
2. Rehash the local executable and compare it to both the build record and the manifest row. Check that EXP-0137 supplies exactly 332 unique function/key pairs for build 10256413.
3. For each Ghidra pointer-symbol suffix address, map the address to the executable's raw PE sections and read two little-endian DWORDs: the name pointer at the symbol address and the adjacent target pointer at `+4`.
4. Resolve the name pointer to a bounded NUL-terminated ASCII string, verify the pointer slot is in `.data`, the string is in `.rdata`, and the target is in `.text`.
5. Check that each decoded name begins with the exact class key, optionally preceded by the observed `A` or `U` owner prefix. Compare each target VA to the indexed function starts and inclusive indexed function ranges.
6. Emit one row per EXP-0137 input and summary counts, preserving all unresolved targets rather than dropping them.

## Observations

- The local executable hash matched the exact build record and manifest. All 332 EXP-0137 symbol suffixes map to `.data` slots whose first DWORD points to an ASCII NUL-terminated `.rdata` string and whose adjacent DWORD points into `.text`.
- All 332 decoded strings start with their class key, with the observed optional `A`/`U` prefix. Examples include `UDownloadableContentEnumerator` → `UDownloadableContentEnumeratorexecCleanLaunchedDLC` and `DisCrusher` → `ADisCrusherexecEncroachingOn`.
- 329/332 adjacent target VAs exactly match an indexed function start.
- Three targets remain unresolved by the current function index and do not fall inside any indexed function body range:

| Class key | Decoded name | `.text` target |
| --- | --- | --- |
| `RB_Handle` | `URB_HandleexecGetOrientation` | `0x005D0B60` |
| `RB_ConstraintInstance` | `URB_ConstraintInstanceexecMoveKinActorTransform` | `0x005D3120` |
| `UISceneClient` | `UUISceneClientexecGetInverseCanvasToScreen` | `0x005C64F0` |

- Per-key source slot, string, target, section, function-index result, and build identity are preserved in the CSV.

## Interpretation and claim limits

- **Observed:** at every one of the 332 selected data addresses, the raw PE contains a `.data` pointer to a `.rdata` exec-name string followed by a `.text` target address. The decoded string begins with the class key from the paired EXP-0137 decompiler expression.
- **Confirmed static address join:** 329 adjacent target addresses equal exact indexed function starts. The other three are `.text` targets outside all indexed function starts and ranges; their identity remains unknown.
- **Inferred, narrow:** the class/key and name/target pairs are consistent with a class-associated native-exec table representation. This does not prove the table is consumed at runtime or that the key maps through NativeToken.
- **Unknown:** why the three targets are absent from the index, whether they are function entries/thunks missed by indexing, the full table boundaries, runtime ownership/use, and dispatch semantics.
- **Evidence that would change the unresolved claims:** read-only disassembly/dataflow can establish instruction boundaries for the three VAs; a build-matched runtime trace or independent consumer proof is needed for table-use claims.

## Reproduction and limitations

- From the repository root, run `python tools/validate_native_class_table_pointer_targets.py`.
- The tool rehashes the executable, checks the build record and manifest, consumes EXP-0137's 332-row catalog and the function index, and regenerates the two outputs.
- No reset is required; temporary output is not created.
- Section membership and exact indexed starts validate static address relationships only. `.text` membership does not itself prove an address is executed or is a complete function.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent key/class join: [EXP-0137](EXP-0137-native-class-registration-group-uelib-join.md)
- Related NativeToken candidate join: [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md)
- Function index: [functions.csv](../research/executable/functions.csv)
- Validator: [validate_native_class_table_pointer_targets.py](../tools/validate_native_class_table_pointer_targets.py)
