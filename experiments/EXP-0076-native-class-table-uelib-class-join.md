---
id: EXP-0076
title: Exact-build native class-table keys joined to UELib classes
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do class-like keys paired with native-table pointer symbols in FUN_00A0DBF0 match class labels in the all-install UELib catalog?"
---

# EXP-0076 — Exact-build native class-table keys joined to UELib classes

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: exact-text join of class-name constructor strings and adjacent pointer-symbol labels in `FUN_00A0DBF0` with the class-path rows in the all-install UELib catalog derived by EXP-0071.
- Exclusions: exact spelling agreement is not proof of object identity beyond the parser label, native table layout, bytecode-token dispatch, or runtime registration/use. UELib output is parser-derived and its known limits remain in EXP-0070/0071. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools and data: build/hash-tagged Ghidra decompiler cache `knowledge/cache/decompiles/00A0DBF0.json`; `research/packages/uelib-object-initialization/uelib-class-object-catalog.csv.gz`; generator [`native_class_table_uelib_join.py`](../tools/native_class_table_uelib_join.py); output [EXP-0076-native-class-table-uelib-join.csv](../research/executable/evidence/EXP-0076-native-class-table-uelib-join.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the local executable SHA-256.
2. Extract `FUN_00454FE0("class",1)` strings and `PTR_s_...` symbols from the exact-build `00A0DBF0` decompiler body. Verify the two ordered streams have equal counts and each zipped pair is within 100 characters in decompiler text.
3. For each key, select rows from the EXP-0071 class/object catalog whose `export_or_import_class_label` equals the key and whose `class_path` begins `Class'`. Preserve parser output and package rows in a per-key CSV.
4. Regenerate the CSV with the tool and inspect the exact-join counts and build/hash identity.

## Observations

- The decompiler-text extraction yielded 135 unique class-key strings and 135 pointer-symbol labels. The key and pointer expressions preserve the same order in the body; all paired text offsets are within 100 characters.
- All 135/135 keys have at least one exact class-label row with a non-null `Class'...'` path in the all-install UELib catalog. This includes all 24 class keys containing `DLC` in their labels.
- The joined rows aggregate to 1,798 class/path/package catalog rows across the 135 keys. The per-key CSV records the exact path, number of catalog rows, number of distinct packages, up to five sample package paths, and pointer-symbol address suffix.
- The class catalog spans the 904-package parser corpus, but this particular exact join validates label overlap only. It does not show that a package class consumes the adjacent native table or that any table entry is called.
- Reproduction with `python tools/native_class_table_uelib_join.py` emitted 135 rows and reported `exact Class-path joins: 135 / 135`.

## Interpretation and claim limits

- **Observed:** every extracted key from this one native registration-like function has an exact class-label and non-null class-path match in the derived UELib catalog.
- **Inferred, narrow:** the `00A0DBF0` key/pointer pairs likely refer to classes represented in the package corpus, based on exact label/path matches and the adjacent `PTR_s_...exec...` symbols. This does not establish table ownership, layout, handler mapping, or runtime use.
- **Unknown:** semantic correctness/completeness of UELib class records, exact linkage between each package class object and each binary pointer, runtime registration, and token dispatch.
- **Limit:** the sample is one function and the join is exact-name based; no fuzzy names or hypothesized cross-layer relationships are promoted.

## Links

- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [EXP-0071 all-install class/object catalog](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- [EXP-0075 native registration helper trace](EXP-0075-native-class-table-registration-helper.md)
