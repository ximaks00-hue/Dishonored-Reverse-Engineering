---
id: EXP-0167
title: Brothel ObjectivesTracker StoryFlag nodes crosswalk to retail
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do the browser-archive Brothel StoryFlag graph endpoints have identifiable counterparts in the retail 10256413 export table?
---

# EXP-0167: Brothel ObjectivesTracker StoryFlag nodes crosswalk to retail

- Experiment status: done
- Claim status: mixed (archive graph facts observed; retail semantic correspondence inferred)
- Retail build: Steam x86 `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`
- Retail package: `DishonoredGame/CookedPCConsole/L_Brothel_Script.upk`; SHA-256 `1F249BF31F90636CE300FFA75103C654FE6B91BF1CABAB495FF55918C893D4D4`
- Question: Can one high-value browser-archive StoryFlag edge be localized to exact retail export candidates without transferring its serialized properties?
- Scope and exclusions: Read-only comparison of graph records and package export-table metadata. No retail property decoding or bytecode interpretation, no runtime test, and no claim that the archive and retail packages have equivalent properties.
- Tools and versions: Browser-port Stage 18/42 graph artifacts; retail `uelib-package-relations-full/package-objects.jsonl` (UELib table metadata); `umodel-package-objects.sqlite` (UModel export list); retail package manifest.

## Procedure

1. Read the browser archive's Brothel ObjectivesTracker graph, which records endpoint object paths, export indices, one authored link, and the two node GUIDs.
2. Filter the retail UELib export-table metadata for StoryFlag classes with the `ObjectivesTracker` outer chain.
3. Cross-check each candidate against the retail UModel object catalog by exact package serial offset, serialized size, class, and object name.
4. Verify the package SHA-256 against `assets/manifests/packages.csv` and the registered retail build record.

## Observations

The browser archive graph at `D:/Dishonored/40_BROWSER_PORT/repo/research/18-kismet-runtime/BROTHEL_FLAG_CHECK_GRAPH.json` records an edge from setter output 0 to checker input 0 in `TheWorld.PersistentLevel.Main_Sequence.ObjectivesTracker`. The edge is enabled, has zero delay, and is sourced from the original UPK graph. Its model trace reports setter GUID `(497584135,1339922769,2015806893,1029544126)` and checker GUID `(3135351192,1201314465,1627257227,1768995829)`; they differ. The trace is marked `STATIC_MODEL`; game-runtime comparison is `NOT_TESTED`. Its source package hash is `75CAE2B76EBB950AFAB8AC6D4BDB4E82D4AEC4D9829DEB34F18B0836FFF4715B`, which differs from retail.

The exact retail package SHA-256 is `1F249BF31F90636CE300FFA75103C654FE6B91BF1CABAB495FF55918C893D4D4` in both the UELib table-metadata rows and package manifest. Two export-table candidates reproduce the graph's class/name/outer-path pattern:

| Role | Archive node path suffix | Retail UELib export row | Retail UModel export row | Retail outer path | Class | Serial size | Serial offset |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: |
| Setter candidate | `ObjectivesTracker.DisSeqAct_SetStoryFlag` | 11352 | 11351 (`_0`) | `TheWorld.PersistentLevel.Main_Sequence.ObjectivesTracker` | `DisSeqAct_SetStoryFlag` | 1654 (`0x676`) | 20,376,466 (`0x0136EB92`) |
| Checker candidate | `ObjectivesTracker.DisSeqCond_CheckStoryFlag_57` | 11472 | 11471 (`_57`) | `TheWorld.PersistentLevel.Main_Sequence.ObjectivesTracker` | `DisSeqCond_CheckStoryFlag` | 1376 (`0x560`) | 20,561,657 (`0x0139BEF9`) |

For these records, UELib's export-table index is one greater than the UModel catalog's export index; serial offset, size, and class cross-check the rows. The retail package has other StoryFlag nodes, so class alone is not a unique identifier.

## Interpretation

- **Observed in the archive:** One enabled setter-to-checker edge is authored in the ObjectivesTracker graph, but the nodes target different flag GUIDs. The browser runner's False branch is consistent with its distinct-key static model. This is not a game-runtime observation.
- **Observed in retail:** The exact-hash retail package contains export-table entries with corresponding StoryFlag classes and matching parent-sequence/name pattern. UModel independently agrees on the relevant retail class, size, and serial offset.
- **Inferred lead:** These are strong retail node candidates for rechecking the archive result. The differing package hashes mean neither the edge nor either GUID has been established for retail. The browser setter's unsuffixed display name and UModel's `_0` display name also warn against treating display-name equality alone as identity.
- **Unknown:** Retail serialized GUIDs, retail link target, link flags/delays, the semantic meaning of the two flags, and runtime execution.
- **Next discriminating check:** The export listing does not expose the retail GUIDs or setter output target. Keep them unknown under the current compressed-package scope. Any later property/link analysis must use an explicitly allowed input path and keep export-table and UModel listing indices labeled by their own convention.

## Reproduction

The full retail table metadata is in the ignored generated file `assets/extracted/uelib-package-relations-full/package-objects.jsonl`. Filter rows with the exact package path and `table == "export"`; follow each positive `outerIndex` through the same package's export rows to reconstruct the outer path. Compare the resulting `serialOffset` and `serialSize` to `package_offset` and `export_size` in `knowledge/database/umodel-package-objects.sqlite` for the retail export listing. Finally compare the package SHA-256 with `assets/manifests/packages.csv`.

Archive source files:

- `D:/Dishonored/40_BROWSER_PORT/repo/research/18-kismet-runtime/BROTHEL_FLAG_CHECK_GRAPH.json`
- `D:/Dishonored/40_BROWSER_PORT/repo/research/56-stage42-brothel-flag-fragment/STAGE_42_TRACE_COMPARISON.json`
- `D:/Dishonored/40_BROWSER_PORT/repo/research/56-stage42-brothel-flag-fragment/STAGE_42_BROWSER_TRACE_BROTHEL.json`

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Retail package: [`L_Brothel_Script` manifest row](../assets/manifests/packages.csv)
- Related: [EXP-0166 retail Kismet census](EXP-0166-retail-kismet-story-and-event-census.md), [external-drive audit](../docs/external-drive-audit.md)
