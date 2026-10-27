---
id: EXP-0168
title: Brothel RemoteEvent endpoint crosswalk to retail
experiment_status: done
claim_status: mixed
build: "10256413"
question: Which browser-archive RemoteEvent endpoints can be localized to exact retail export-table entries by class and full outer path?
---

# EXP-0168: Brothel RemoteEvent endpoint crosswalk to retail

- Experiment status: done
- Claim status: mixed (source candidate groups and retail table matches observed; retail event-property correspondence inferred)
- Retail build: Steam x86 `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`
- Retail package: `DishonoredGame/CookedPCConsole/L_Brothel_Script.upk`; SHA-256 `1F249BF31F90636CE300FFA75103C654FE6B91BF1CABAB495FF55918C893D4D4`
- Question: Can the browser archive's Brothel RemoteEvent inventory be crosswalked to exact retail object-table candidates without assuming the serialized event names or runtime dispatch are the same?
- Scope and exclusions: Object identity candidates only. No retail event-name property extraction, no Kismet edge recovery in retail, and no runtime trace.
- Tools and versions: Browser archive `remote_event_inventory/L_Brothel_Script.csv` and `remote_event_scope_analysis/WITHIN_ROOT_CANDIDATE_PAIRS.csv`; exact-build UELib export-table metadata; UModel export catalog; retail package manifest.

## Procedure

1. Read every activator/receiver row in the browser archive's L_Brothel remote-event inventory.
2. Reconstructed each retail export's full outer path from the generated UELib table metadata for the exact retail package.
3. Joined by exact class and full object path; retained zero-match rows and counted any ambiguous joins.
4. Cross-checked each unique match against UModel by retail serial offset, size, and class, then wrote the compact crosswalk CSV.
5. Kept browser event names as source-corpus labels only; they are not asserted as retail property values.

## Observations

The browser archive inventory contains 326 nodes: 192 `SeqAct_ActivateRemoteEvent` and 134 `SeqEvent_RemoteEvent`. Exact class + full outer-path + object-name matching gives:

- 321 unique retail table candidates;
- 0 ambiguous candidates;
- 5 rows with no exact retail path match.

For every unique row, UELib serial offset/size/class agrees with the UModel export listing. The UELib export table index is one greater than the UModel catalog's export index for these matched rows; both indices are preserved in the output. The exact retail package SHA-256 is included on every mapped CSV row.

The browser archive's own scope analysis has three notable same-immediate-sequence name candidates under `Main_Sequence.Art_Dealer`:

| Event name in archive | Archive activators | Archive receiver | Retail candidate paths |
| --- | --- | --- | --- |
| `ArtDealer_Incapacited` | `SeqAct_ActivateRemoteEvent_199`, `_201` | `SeqEvent_RemoteEvent_311` | All three exact class/path matches |
| `Bunting_SleepDart` | `SeqAct_ActivateRemoteEvent_200` | `SeqEvent_RemoteEvent_313` | Both exact class/path matches |

For example, the retail candidates are:

- Activator `_199`: UELib row 18918 / UModel row 18917, serial offset 27,262,354, size 1,467.
- Activator `_201`: UELib row 18922 / UModel row 18921, serial offset 27,268,198, size 1,403.
- Receiver `_311`: UELib row 19945 / UModel row 19944, serial offset 29,669,193, size 1,110.
- Activator `_200`: UELib row 18921 / UModel row 18920, serial offset 27,266,735, size 1,463.
- Receiver `_313`: UELib row 19946 / UModel row 19945, serial offset 29,670,303, size 1,106.

The checked-in evidence file [`L_Brothel_Script.csv`](../research/packages/kismet-remote-event-crosswalk/L_Brothel_Script.csv) preserves all 326 archive rows, including the five unmatched rows and all 321 retail candidates.

## Interpretation

- **Observed in archive:** The event-name grouping tool labels the listed pairs `same-root event-name candidate; not a runtime trace`. The selected pairs also share their immediate `Art_Dealer` sequence in the source inventory.
- **Observed in retail:** Matching class/path endpoints exist in the exact-hash retail export table, and offsets/sizes agree with independent UModel listing metadata.
- **Inferred:** These are high-value exact retail objects to inspect if/when retail property decoding is allowed. The archive event names make a concrete search list, but do not establish those event names in retail.
- **Unknown:** Retail `RemoteEvent` property names, whether the candidate nodes pair under retail properties, their link graph, the reason for the five unmatched paths, and runtime behavior.
- **Denominator caveat:** The retail package catalog has 196 activators and 137 receivers, while the browser inventory lists 192 and 134. The source inventory does not embed its input package SHA; do not interpret the count differences as changed game content until the source bytes and extraction coverage are matched.

## Reproduction

Use the external archive files:

- `D:/Dishonored/40_BROWSER_PORT/repo/experiments/remote_event_inventory/L_Brothel_Script.csv`
- `D:/Dishonored/40_BROWSER_PORT/repo/experiments/remote_event_scope_analysis/WITHIN_ROOT_CANDIDATE_PAIRS.csv`

Use the exact retail package identity and export-table metadata in `assets/manifests/packages.csv` and `assets/extracted/uelib-package-relations-full/package-objects.jsonl`. Reconstruct outer paths by following positive `outerIndex` values within the package. Match `(className, full outer path + objectName)`, then compare `serialOffset` / `serialSize` with `package_offset` / `export_size` in `knowledge/database/umodel-package-objects.sqlite`.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Retail package: [`L_Brothel_Script` manifest row](../assets/manifests/packages.csv)
- Related: [EXP-0166 retail Kismet census](EXP-0166-retail-kismet-story-and-event-census.md), [EXP-0167 StoryFlag crosswalk](EXP-0167-brothel-storyflag-retail-node-crosswalk.md)
