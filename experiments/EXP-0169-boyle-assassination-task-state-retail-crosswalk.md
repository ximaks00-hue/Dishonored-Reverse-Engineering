---
id: EXP-0169
title: Boyle assassination task-state chain crosswalk to retail
experiment_status: done
claim_status: mixed
build: "10256413"
question: Can a browser-archive Boyle task-state sequence be localized to exact retail export-table candidates?
---

# EXP-0169: Boyle assassination task-state chain crosswalk to retail

- Experiment status: done
- Claim status: mixed (archive static graph observed; retail node correspondence inferred)
- Retail build: Steam x86 `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`
- Retail package: `DishonoredGame/CookedPCConsole/L_Boyle_Int_Script.upk`; SHA-256 `17BE4C7BD18F4E400DC053E0FCF61590240B38B0C3666F2F224676FFDFACCB86`
- Question: Does one high-value task-state sequence from the browser archive have exact-path counterparts in the retail mission package?
- Scope and exclusions: Crosswalk of graph/property-link records to retail export-table metadata. No retail property/edge decoding, no causal gameplay conclusion, and no runtime test.
- Tools and versions: Browser archive Stage 15 task/story graph and typed-link CSVs; exact-build UELib export-table metadata; UModel export catalog; retail package manifest.

## Procedure

1. Selected the Boyle Objectives sequence in the archive supported-edge and typed-link datasets.
2. Traced the three task-state setters feeding `SeqCond_CompareBool_9`, the comparer outputs, its linked bool variable, the completion setter, and the subsequent StoryFlag setter.
3. Joined the six action/condition node class/full paths against UELib export rows in the exact retail package, reconstructing outer ownership from `outerIndex`. Checked the linked variable name separately because the archive typed-link row preserves only its leaf name.
4. Cross-checked each retail row against UModel by exact package serial offset, size, and class.
5. Kept task references, link properties, and GUIDs from the archive labeled as archive-only; compared package SHA-256 against the retail manifest.

## Observations

The archive static graph records this fragment under `L_Boyle_Int_Script.TheWorld.PersistentLevel.Main_Sequence.Boyle_Objectives`:

```text
SetTaskState_18 ─┐
SetTaskState_30 ─┼─> CompareBool_9 --True--> SetTaskState (complete 3 tasks) --> SetStoryFlag_14
SetTaskState_31 ─┘                       \--False--> no linked output
```

The three source task-state nodes are associated with `DTS_Active` and the tasks `BoyleAssassination.DishonoredTask_Custom_18`, `_17`, and `_16`, respectively. Their `Task` variable links are `DisSeqVar_Task_24`, `_29`, and `_31`. Each source node's serialized output fan-out includes `CompareBool_9`, `SeqAct_SetBool_15`, and a target-notification node. Their input links each specify a 1-second activation delay. These are serialized archive properties, not observed timing in the game.

`CompareBool_9` has a 4-second input activation delay. Its `Bool` variable link points to `SeqVar_Named_66`; the `True` output links to the completion `SetTaskState` node and the `False` output has no links. The parallel `SeqAct_SetBool_15` link detail reads `SeqVar_Bool_30` as `Value` and writes `SeqVar_Bool_31` as `Target`. The available data does **not** establish that either variable is the same object/value as `SeqVar_Named_66`; do not use this parallel fan-out to explain the comparer result.

The completion node is associated with `EDisTaskState.DTS_Completed` for three task references under `BoyleAssassination`: `DishonoredTask_Custom_16`, `_17`, and `_18`. Its listed task-variable names are `DisSeqVar_Task_29`, `_31`, and `_24`. Its output links to `DisSeqAct_SetStoryFlag_14`, whose archive semantic ID is `(A=1805382155,B=1266333211,C=573585061,D=3495183844)`. The graph/property-link tables do not establish which retail GUID/configuration is serialized in the retail object.

The six action/condition node paths in the fragment have unique exact class/full-path candidates in retail:

| Node | Retail UELib table index | Retail UModel export index | Retail serial offset | Serial size |
| --- | ---: | ---: | ---: | ---: |
| `DisSeqAct_SetTaskState_18` | 8684 | 8683 | 14,396,819 | 1,551 |
| `DisSeqAct_SetTaskState_30` | 8693 | 8692 | 14,410,284 | 1,551 |
| `DisSeqAct_SetTaskState_31` | 8694 | 8693 | 14,411,835 | 1,551 |
| `SeqCond_CompareBool_9` | 16459 | 16458 | 21,999,558 | 2,166 |
| completion `DisSeqAct_SetTaskState` | 8676 | 8675 | 14,385,430 | 1,431 |
| `DisSeqAct_SetStoryFlag_14` | 8574 | 8573 | 14,232,177 | 1,718 |

All six candidates have outer path `TheWorld.PersistentLevel.Main_Sequence.Boyle_Objectives`. For each, UELib serial offset/size/class matches the UModel listing. UELib table indices are one greater than UModel catalog export indices for these rows. The exact retail package SHA-256 is `17BE4C7BD18F4E400DC053E0FCF61590240B38B0C3666F2F224676FFDFACCB86`.

The archive link names `SeqVar_Named_66` but does not preserve its outer path. The exact-hash retail package contains two `SeqVar_Named_66` exports of class `SeqVar_Named`, each with serial size 184: UELib/UModel indices 17556/17555 at offset 22,653,635 under `Boyle_Objectives`, and indices 17690/17689 at offset 22,678,291 under `Main_Sequence`. Both are same-name retail candidates; the archive link record is insufficient to choose between them.

As a broader scoping metric, 73 of 76 distinct archive `SetTaskState` action paths in `L_Boyle_Int_Script` have a unique exact class/path candidate in retail; 3 have no exact path match. This crosswalk does not validate archive task references or state values in retail.

## Interpretation

- **Observed in archive:** Three active-task setters feed a delayed comparer; its True branch reaches a node associated with completing three BoyleAssassination task references and then a StoryFlag setter. The False output has no serialized target in this fragment.
- **Observed in retail:** Six action/condition paths have exact-hash retail export candidates, with matching class, outer path, serial offset, and size across UELib and UModel metadata. The linked variable name has two retail export candidates with distinct outer paths.
- **Inferred lead:** This is a bounded mission-state fragment for future retail-scoped research. It prioritizes the comparer, six action/condition objects, and the unresolved pair of variable candidates.
- **Unknown:** The CompareBool operand values, which `SeqVar_Named_66` export corresponds to the archive leaf-only link, whether the SetBool target is related to that variable, retail edge/property equivalence, StoryFlag value/GUID, upstream activation, and runtime reachability.
- The archive CSVs do not embed the input UPK SHA-256. Therefore the crosswalk is a name/path candidate and does not claim source-package byte identity.

## Reproduction

Archive source files:

- `D:/Dishonored/40_BROWSER_PORT/repo/research/29-task-story-native-graph/STAGE_15_SUPPORTED_TASK_STORY_EDGES.csv`
- `D:/Dishonored/40_BROWSER_PORT/repo/research/29-task-story-native-graph/STAGE_15_TASK_STATE_WRITES.csv`
- `D:/Dishonored/40_BROWSER_PORT/repo/experiments/campaign_typed_links/link_details/L_Boyle_Int_Script_links.csv`

For the retail candidates, filter `assets/extracted/uelib-package-relations-full/package-objects.jsonl` to `DishonoredGame/CookedPCConsole/L_Boyle_Int_Script.upk`, reconstruct each export's outer chain, and match exact class/full path. Cross-check serial offset and size against `knowledge/database/umodel-package-objects.sqlite` and package SHA-256 against `assets/manifests/packages.csv`.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Retail package: [`L_Boyle_Int_Script` manifest row](../assets/manifests/packages.csv)
- Related: [EXP-0166 retail Kismet census](EXP-0166-retail-kismet-story-and-event-census.md), [EXP-0167 StoryFlag crosswalk](EXP-0167-brothel-storyflag-retail-node-crosswalk.md), [EXP-0168 RemoteEvent crosswalk](EXP-0168-brothel-remote-event-endpoint-crosswalk.md)
