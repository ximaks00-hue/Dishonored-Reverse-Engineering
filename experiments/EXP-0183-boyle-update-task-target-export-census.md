---
id: EXP-0183
title: Boyle UpdateTaskTarget export census
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Which exact-hash Boyle script packages contain UpdateTaskTarget exports, and where do the Boyle Interior exports sit in the serialized outer hierarchy?"
---

# EXP-0183 — Boyle UpdateTaskTarget export census

- Date: 2026-10-27 (Europe/Kiev).
- Target executable: Steam app `217980`, build `10256413`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Packages: four manifest-listed Boyle mission script UPKs, each individually SHA-256 verified; see the [portable census JSON](../research/packages/kismet-update-task-target/EXP-0183-boyle-update-task-target-export-census.json).
- Detailed export subset: [25 Boyle Interior UpdateTaskTarget rows](../research/packages/kismet-update-task-target/boyle-int-update-task-target-exports.csv).
- Scope: read-only package summary, export/class-name search, and UELib import/export outer-path metadata. No package object decompilation or property/sequence-link extraction.

## Procedure

1. Confirm the registered EXE hash against [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Recompute the installed SHA-256 for `L_BoyleStreet_Ext_Script.upk`, `L_Boyle_Ext_Script.upk`, `L_Boyle_Int_Script.upk`, and `L_Pub_FromBoyle_Script.upk`; compare them to the installed package manifest.
3. Query each exact path with `mcp__dishonored_assets__get_package_info` for package summary and `mcp__ue_explorer__search_objects` with query `UpdateTaskTarget` for exports matching the class/name.
4. For Boyle Interior, check the 25 matching rows in the local UELib package import/export relations catalog. Require each row's `sourceSha256` to equal the installed UPK hash, and record both UELib `tableIndex` and UE Explorer `export_index`, name, class, outer path, serial offset, and serial size in the compact CSV.
5. Stop at export-table and outer-path metadata. Do not infer reflected property values, TargetIndex, Task/Actor references, Kismet connections, or runtime execution from these records.

## Observations

- The four package-specific searches return 7 matches in Boyle Street Exterior, 8 in Boyle Exterior, 25 in Boyle Interior, and 6 in `L_Pub_FromBoyle_Script.upk` (46 total search results across this bounded set).
- The other 21 matches are also sequence-scoped in the export relations: all 7 Boyle Street Exterior and all 6 `L_Pub_FromBoyle` results are under `Main_Sequence`; Boyle Exterior has 5 under `Main_Sequence` and 3 under `Pistols_in_the_Yard`.
- All 25 Boyle Interior exports are class `DisSeqAct_UpdateTaskTarget` and have the path `TheWorld.PersistentLevel.Main_Sequence.Boyle_Objectives`. UELib reports outer `tableIndex` 16751; UE Explorer reports `export_index` 16750. The outer chain is Boyle_Objectives → Main_Sequence → PersistentLevel → TheWorld.
- The 25 detailed rows include UELib `tableIndex` values 8790–8814 and corresponding UE Explorer `export_index` values 8789–8813. The source conventions differ by one for these records. Serialized offsets range from `14531469` through `14592521`, and sizes range from 2443 to 2686 bytes. Object suffix ordering does not equal table-index ordering; the CSV preserves both indices and each exact row.
- The installed hashes match the local package manifest. All Boyle Interior relation rows carry the same `sourceSha256` as the actual UPK.
- The four mission packages report UE package version `801/30`, EngineVersion `9098`; the separate base `DishonoredGame.upk` package summary reports EngineVersion `9411`. These are package-specific metadata values and are not interchangeable.

## Interpretation

- **Observed, exact-package metadata:** Boyle Interior contains a dense cluster of 25 `DisSeqAct_UpdateTaskTarget` exports under the outer sequence path `Boyle_Objectives`; 21 additional search results occur in the other three Boyle packages. UELib `tableIndex` and UE Explorer `export_index` are recorded separately because their values differ by one.
- **Useful prioritization lead:** the Boyle Interior cluster is a concrete bounded set for a future serialized-property and Kismet-link analysis. The location is stronger than a global class search because the outer path is recorded for each export.
- **Unknown:** every node's target index, task link, actor/name/preset values, input/output/variable links, event reachability, and relation to the exact-build native handler. The class/handler crosswalk remains tentative; [EXP-0179](EXP-0179-task-action-vtable-family.md) reports a weak order-based match for the UpdateTaskTarget handler.
- **Limit:** object names, class names, outer path, serial offsets, and sizes establish export identity only. They do not prove that any of these 25 nodes updates the native task-target array or produces a visible HUD marker.

## Next discriminating work

The name/path comparison to the browser archive is now recorded in [EXP-0185](EXP-0185-boyle-archive-update-task-target-crosswalk.md): all 24 archive names have retail export candidates, with one retail-only `_41`. Archive variable references and output edges remain archive-only. Next, compare specific retail fields/links only through an allowed exact-hash source; retain unknown status under the current compressed-UPK summary/search-only rule when those values cannot be inspected.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Target-array static evidence: [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md)
- Layout/name crosswalk: [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md)
- Objective/task/Kismet/HUD cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
