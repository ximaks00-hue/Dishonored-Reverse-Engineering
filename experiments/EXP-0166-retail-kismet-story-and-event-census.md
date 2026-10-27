---
id: EXP-0166
title: Retail Kismet story-state and remote-event census
experiment_status: done
claim_status: observed
build: "10256413"
question: Which exact-build retail script packages are efficient targets for tracing story-state and RemoteEvent Kismet links?
---

# EXP-0166: Retail Kismet story-state and remote-event census

- Experiment status: done
- Claim status: observed
- Build ID: Steam x86 `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`
- Question: Which exact-build retail script packages contain useful, bounded cohorts of story-state setters/checkers and RemoteEvent send/receive nodes?
- Scope and exclusions: Read-only inventory and export-list metadata. No package property decompilation, bytecode interpretation, game launch, or runtime claims.
- Tools and versions: Full local UModel export catalog `knowledge/database/umodel-package-objects.sqlite`; read-only SQLite queries; Dishonored Assets MCP `list_package_objects` for independent package-list confirmation. Catalog reports UModel package version `801/30` and per-package engine versions below.

## Procedure

1. Confirmed the executable identity against [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Queried the full local object catalog for exact `object_class` values `SeqAct_ActivateRemoteEvent`, `SeqEvent_RemoteEvent`, `DisSeqAct_SetTaskState`, `DisSeqAct_SetStoryFlag`, and `DisSeqCond_CheckStoryFlag`.
3. Counted objects and distinct package paths; ranked packages containing both story-flag setters and checkers, with remote-event node counts as context.
4. Compared selected package rows (export index, package offset, serialized size, class, object name) to the Assets MCP export-list result for `L_ArtDealer_Scripts.upk`.
5. Matched package length and SHA-256 from the catalog to `assets/manifests/packages.csv`.

## Observations

The full catalog contains these exact-class object totals:

| Class | Objects | Distinct packages |
| --- | ---: | ---: |
| `SeqAct_ActivateRemoteEvent` | 7,194 | 226 |
| `SeqEvent_RemoteEvent` | 6,999 | 268 |
| `DisSeqAct_SetTaskState` | 1,430 | 95 |
| `DisSeqAct_SetStoryFlag` | 1,634 | 122 |
| `DisSeqCond_CheckStoryFlag` | 1,997 | 144 |

Three useful exact-build package candidates:

| Package | SetStoryFlag | CheckStoryFlag | ActivateRemoteEvent | RemoteEvent | SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `DishonoredGame/CookedPCConsole/L_ArtDealer_Scripts.upk` | 10 | 9 | 11 | 12 | `C6AE37F5953FBBCC1359A2E03EDF4DCD1BA037946AE045502AE6D1A755587841` |
| `DishonoredGame/CookedPCConsole/L_Brothel_Script.upk` | 57 | 89 | 196 | 137 | `1F249BF31F90636CE300FFA75103C654FE6B91BF1CABAB495FF55918C893D4D4` |
| `DishonoredGame/DLC/PCConsole/DLC06/DLC06_Slaughter_Int_Script.upk` | 101 | 141 | 113 | 87 | `9D3784EAA379B64FBE735EFDC1BBD984F12C2A82D81B7578E437972BA8E53544` |

The ArtDealer package is 13,150,605 bytes and its catalog metadata is `801/30`, engine `9098`, 7,152 names, 11,334 exports, 1,094 imports. Its manifest row matches the catalog length and SHA-256. The Assets MCP listing confirms the relevant class/name/export-index/offset/size rows, including:

- Story setters at exports `7098–7107`, offsets `0xC71A79–0xC735BF`, serial sizes `0x636` or `0x666`.
- Story checks at exports `7113–7121`, offsets `0xC7C0E2–0xC7E7C2`, serial size `0x520` each.
- Remote-event activators at exports `10189–10199`, offsets `0xEC1C10–0xEC54AC`.
- Remote-event receivers at exports `10371–10382`, offsets `0xF1FC85–0xF22E55`.

The full catalog also identifies DLC06 Slaughter Int as the densest combined candidate among the sampled high-ranked packages, with 139 task-state setters in addition to the story and remote-event cohorts. Its package metadata is `801/30`, engine `9411`, 22,230,722 bytes, and its SHA-256 matches the package manifest.

## Interpretation

- **Observed:** The exact-build retail object catalog contains large, recurring cohorts of story-state and named remote-event Kismet node classes, and identifies specific script packages where both sides of these mechanisms are present.
- **Useful next target:** Start with `L_ArtDealer_Scripts.upk` for a bounded graph-parser proof of concept (42 target nodes across the four queried classes); then scale to `L_Brothel_Script.upk` or DLC06 Slaughter Int. The count is a scoping estimate, not a graph-component count.
- **Unknown:** The catalog does not reveal serialized flag names, event names, parent sequence ownership, input/output links, or execution order. Co-presence in a package does not establish that any sender reaches any receiver or that a setter feeds a checker.
- June/browser/editor package semantics and same-name nodes are not transferred to retail by this census. Any such mapping requires a separate build-bound crosswalk.

## Reproduction

Read-only SQLite query against `knowledge/database/umodel-package-objects.sqlite`:

```sql
SELECT object_class, COUNT(*) AS objects, COUNT(DISTINCT relative_path) AS packages
FROM objects
WHERE object_class IN (
  'SeqAct_ActivateRemoteEvent', 'SeqEvent_RemoteEvent',
  'DisSeqAct_SetTaskState', 'DisSeqAct_SetStoryFlag',
  'DisSeqCond_CheckStoryFlag'
)
GROUP BY object_class
ORDER BY object_class;
```

For package-level cohort counts, group by `relative_path` and use conditional sums for the same five `object_class` values. Compare package length/SHA-256 with `assets/manifests/packages.csv` before any follow-up work. The MCP export listing is capped at 500 rows per call; the local full-catalog SQL query is used for complete counts.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package manifest: [`packages.csv`](../assets/manifests/packages.csv)
- Related material: [external-drive audit](../docs/external-drive-audit.md)
- Follow-up: Parse link descriptors and parent/outer sequence ownership for the ArtDealer cohort; retain each parsed edge's package SHA, export indices, and confidence. Do not infer runtime reachability from static links alone.
