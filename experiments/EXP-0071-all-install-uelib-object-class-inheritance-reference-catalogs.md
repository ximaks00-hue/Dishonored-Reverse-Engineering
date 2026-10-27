---
id: EXP-0071
title: All-install UELib class, inheritance and reference mention catalogs
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can the all-install UELib initialization corpus be converted into searchable class, inheritance, typed-object-relation and default-property reference-mention catalogs with counts reconciled to the emitted corpus?"
---

# EXP-0071 — All-install UELib class, inheritance and reference mention catalogs

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: derive compact, searchable class/object category, `Super`, property-type-reference, and initialized object-field relation catalogs from EXP-0070's full-install UELib JSONL corpus; check catalog denominators and relation counts against source JSONL.
- Exclusions: no rerun of the game, no independent UE3 property decoder, no runtime/reference reachability claim, and no access to `_excluded_coop_project/`.
- Tools: Python 3 standard library, SQLite temporary on-disk index, gzip CSV, the EXP-0070 corpus, and [catalog summarizer](../tools/summarize_uelib_object_graph.py).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the current EXE SHA-256.
2. Stream all rows from `assets/extracted/uelib-object-init-full/initialized-objects.jsonl` into a temporary SQLite index keyed by package path and signed UELib package index. The database is outside the repository and removed after the summarizer exits.
3. Derive grouped class/object-category rows, per-object `Super` rows, property-type-reference groups and per-object relations from the structured fields already emitted by UELib. Normalize the path inside `Type'Package.Path'` for same-package reference-mention checks.
4. Re-read `initialized-edges.jsonl` and compare its total and per-relation counts and source object index/path values with the object-field-derived relation rows.
5. Re-read `default-property-reference-mentions.jsonl`; group mentions by package, owner, property and target, and check whether each unwrapped target path and class label occur among objects from the same package. Preserve these mentions as formatted-text evidence, separate from structured object fields.
6. Store compressed full catalogs and compact summaries under [uelib-object-initialization](../research/packages/uelib-object-initialization/). The original JSONL remains ignored generated data.

Reproduce from the repository root in PowerShell:

```powershell
python tools\summarize_uelib_object_graph.py `
  --run-dir assets\extracted\uelib-object-init-full `
  --output-dir research\packages\uelib-object-initialization
```

The script uses a temporary SQLite database to bound memory for the 3.1-million-object input. The two full relation catalogs are gzip-compressed CSVs.

## Observations

- The source contained 3,110,949 object rows in 904 package paths; there were zero duplicate `(package, packageIndex)` keys.
- The class/object catalog contains 133,660 grouped rows; the inheritance catalog contains 5,355 `Super` rows; the property-type-reference catalog contains 3,896 distinct object-type/reference groups covering 13,138 source object rows.
- The derived initialized relation catalog contains 6,413,586 rows. Its per-relation counts equal the source `initialized-edges.jsonl` counts exactly: class 2,880,410; outer 3,046,617; archetype 395,709; default object 43,205; next field 29,152; property type 13,138; super 5,355.
- All 6,413,586 source edge rows map to a source `(package, packageIndex)` row and its formatted source path matches the object corpus. No object-field relation row is lost by the catalog pass; relation counts are regenerated directly from the structured fields.
- All 288 default-property formatted-text reference mentions (283 distinct package/target pairs) match a same-package object path and UELib export/import class label after removing the `Type'…'` wrapper from the target object's `GetReferencePath()` representation. The unmatched mention catalog has only its header.

## Interpretation and claim limits

- **Confirmed for this corpus transformation:** the summarized class/inheritance/property-type/relation counts and initialized relation totals derive from the complete EXP-0070 source corpus; generated relation type totals match the emitted UELib edge JSONL exactly.
- **Observed:** UELib's structured object model provides package-local class, outer, archetype, default-object, super, next-field and selected property-type references for the rows represented by those fields. The catalog reflects the parser's exposed API values.
- **Observed, weaker text evidence:** formatted default-property text includes 288 reference comments whose path/class labels are internally represented among objects in the same package. This confirms only a same-parser/same-corpus consistency check; it is not an independent check of raw serialized properties.
- **Unknown:** whether these objects or references are loaded/reachable at runtime; semantic completeness of UnknownObject payloads; omitted or unsupported reference forms; correctness against an independent UE3 parser or original source.
- **Limit:** relation presence is not proof of runtime resolution. Grouped rows and catalog files do not supersede per-object/package hashes or EXP-0070's parser limitations. References from formatted property strings remain explicitly separate from structured UELib fields.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Source initialization pass: [EXP-0070](EXP-0070-all-install-uelib-object-initialization-profile.md)
- Catalog outputs: [UELib object initialization profile](../research/packages/uelib-object-initialization/README.md)
- Summarizer: [summarize_uelib_object_graph.py](../tools/summarize_uelib_object_graph.py)
