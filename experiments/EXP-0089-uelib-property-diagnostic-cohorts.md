---
id: EXP-0089
title: All-install UELib property diagnostic cohorts
experiment_status: done
claim_status: observed
build: "10256413"
question: "Which property class/type/name cohorts account for UELib on-demand value diagnostics in the all-install run?"
---

# EXP-0089 — All-install UELib property diagnostic cohorts

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: stream the 13,418,888 formatted property rows from EXP-0088 and aggregate row presence, parser `valueError`, and captured diagnostic rows by owner class, property type, and property name.
- Exclusions: diagnostic samples are UELib console text, not independent byte-level diagnosis; row counts measure affected property rows, not unique serialized values or objects. No runtime validation. `_excluded_coop_project/` was not accessed.
- Input: ignored [EXP-0088 property JSONL](../assets/extracted/uelib-object-init-ondemand-full/default-properties.jsonl), 9,073,077,390 bytes. Durable outputs: [summary](../research/packages/uelib-on-demand-coverage/diagnostics/diagnostic-summary.json), [diagnostic cohorts](../research/packages/uelib-on-demand-coverage/diagnostics/property-diagnostic-cohorts.csv), [value errors](../research/packages/uelib-on-demand-coverage/diagnostics/property-value-error-cohorts.csv), [field frequencies](../research/packages/uelib-on-demand-coverage/diagnostics/property-field-frequency.csv).
- Tool: [streaming summarizer](../tools/summarize_uelib_property_diagnostics.py), Python 3 standard library.

## Procedure

1. Read the research status, Blink activation graph, build record, and repo instructions; verify the build EXE hash.
2. Stream each JSONL row once, counting total property rows and grouping by owner class/property type/property name. Count rows with `valueError` separately from rows with captured `valueDiagnosticLineCount`; retain one diagnostic sample per field group.

Reproduce from the repository root:

```powershell
python tools\summarize_uelib_property_diagnostics.py `
  --input assets\extracted\uelib-object-init-ondemand-full\default-properties.jsonl `
  --output-dir research\packages\uelib-on-demand-coverage\diagnostics
```

## Observations

- The input contained 13,418,888 property rows and collapsed to 25,910 distinct owner-class/property-type/property-name groups.
- 2,048,157 rows had one or more captured value-diagnostic lines, totaling 9,220,977 lines. This diagnostic subset is not equivalent to failed property rows.
- The largest affected field groups by row count were `StaticMeshComponent.IrrelevantLights` (152,692), `AnimSequence.Notifies` (115,226), `ParticleLODLevel.Modules` (70,696), `ParticleModuleSpawn.Rate` (63,700), `StaticMeshComponent.Materials` (62,751), and `MaterialInstanceConstant.ReferencedTextureGuids` (43,498). The leading samples report `Couldn't acquire array type`; some struct-valued particle fields additionally report value-deserialization exceptions.
- All 325 `valueError` rows fell into one cohort: `ParticleModuleSpawn.Rate` (`StructProperty`), each with `EndOfStreamException: Unable to read beyond the end of the stream.`

## Interpretation and claim limits

- **Observed:** diagnostic output is concentrated in recurring array/struct field groups across mesh, animation, particle, and material classes. This gives concrete prioritization targets for independent format work.
- **Observed:** the extractor's `valueError` field is much narrower than captured diagnostic text: 325 rows report a value error, while over two million rows have captured diagnostics. Do not equate console diagnostics with failed loads or incorrect values.
- **Unknown:** whether each diagnostic indicates unsupported tag metadata, a version-specific layout difference, partial recovery, or wrong values; no raw-byte parser was used here.
- **Limit:** counts are for UELib 1.13.3 output on the exact build and corpus. Grouping on class/type/name does not distinguish package or value variants; source rows and one sample per field remain in linked outputs only as aggregates.

## Links

- [EXP-0088 all-install on-demand object loading](EXP-0088-uelib-all-install-on-demand-object-load.md)
- [Property diagnostic summarizer](../tools/summarize_uelib_property_diagnostics.py)
