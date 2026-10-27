---
id: EXP-0187
title: UpdateTaskTarget input actions and archive index census
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do archive UpdateTaskTarget index/input patterns show, and can they be cross-checked against the exact-build native handler candidate?"
---

# EXP-0187 — UpdateTaskTarget input actions and archive index census

- Date: 2026-10-27 (Europe/Kiev).
- Exact-build anchor: Steam x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: browser/editor CSV exports for `DisSeqAct_UpdateTaskTarget`, a cross-map census of serialized input/index properties, one discriminating Overseer graph fragment, and a read-only exact-build check of `FUN_00BA84D0`.
- Provenance: archive exports have no recorded source UPK hash/build identity in these CSVs. Archive observations remain archive-only and are not asserted as retail package contents.
- Portable outputs: [census CSV](../research/packages/kismet-update-task-target/archive-update-task-target-census.csv), [census provenance JSON](../research/packages/kismet-update-task-target/archive-update-task-target-census.json), and [exact-build handler/class crosswalk JSON](../research/executable/evidence/EXP-0187-update-task-target-handler-crosswalk.json). Rebuild archive outputs with [`audit_archive_target_index_census.py`](../tools/audit_archive_target_index_census.py); source directories are recorded in the provenance JSON.
- Related work: [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md), [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md), [EXP-0184](EXP-0184-task-target-selector-to-marker-and-focus-path.md), [EXP-0185](EXP-0185-boyle-archive-update-task-target-crosswalk.md), [EXP-0186](EXP-0186-boyle-archive-target-labels-and-variable-leads.md).

## Procedure

1. Read the 36 available `*_Script.csv` task/story inventories and matching `*_links.csv` exports from the browser/editor research archive. Hash each input.
2. Group `DisSeqAct_UpdateTaskTarget` property rows by `(package, object_path)`, preserving values and joining link rows by the same key.
3. Count unique actions separately from property rows; do not treat an absent property as an empty/default value.
4. For indexed actions, compare input labels, stored impulse bits, output links, task/target variable references, and target labels.
5. Read the exact-build function cache for `FUN_00BA84D0`. Compare its three bit reads to the versioned `FSeqOpInputLink` declaration while retaining the handler/class association caveat.

## Observations

### Archive census

- The 36 inventory CSVs contain **430 property rows** for **384 unique** `DisSeqAct_UpdateTaskTarget` objects.
- Property rows: `m_TargetName` 384, `m_TargetIndex` 39, `m_pTargetActor` 7. All 39 indexed actions also have `m_TargetName`; all seven actor-property actions also have `m_TargetName`. Unique-object property sets: 338 name-only, 39 name+index, and 7 name+actor.
- `m_TargetIndex` appears in 12 packages, with serialized values `1` (20 actions), `2` (15), and `3` (4). The archive census alone does not establish a valid range or identify actor values; exact-build crosswalk evidence below supports it as an index into the task target-record array.
- All 39 indexed actions expose three input labels in order: `Set`, `Clear`, `Toggle`; all 117 exported `bHasImpulse` fields are `false`. These are serialized archive fields, not runtime impulse observations.
- All 39 indexed actions also have both a `Task` and a `Target` variable-link descriptor in the link exports. These identify connected variable nodes in the archive graph; they do not establish the runtime object values.
- The seven `m_pTargetActor` property records instead occur on actions without `m_TargetIndex`: six in `L_Pub_FromBoyle_Script` and one in `L_Pub_FromBridge_Script`. In the Boyle package, four actions point to `DishonoredSpawner_25`; three carry the label `Admiral Havelock` and one `Note and package`. This demonstrates that the archive exports direct actor-property references separately from index-bearing actions, but does not establish how the runtime handler resolves the two forms.
- Of the 39 indexed actions, 35 have no linked output operation; four link to another `DisSeqAct_UpdateTaskTarget`.
- The generated CSV preserves all 384 actions and all available `InputLinks`, `OutputLinks`, and `VariableLinks` rows as JSON arrays, alongside same-sequence task-definition candidates and package-scope candidates. CSV SHA-256: `A21D4A88570E5D8B8BB17D8D6C669BFFB4C24C2F54DFFA75A99DF2D651B8E945`. The JSON records exact SHA-256 values for the 36 inventory and 36 link inputs.

### Discriminating Overseer pair

In `L_Ovrsr_Script`, two actions share target label `To Distillery District`, task variable leaf `DisSeqVar_Task_30`, and target variable leaf `SeqVar_Named_4`, but have different indices:

| Action | Index | Output |
| --- | ---: | --- |
| `DisSeqAct_UpdateTaskTarget_11` | 1 | links to `_8`, input 0 |
| `DisSeqAct_UpdateTaskTarget_8` | 2 | no linked output |

The inventory SHA-256 is `555435B77D9C823F585E8289063A4D02087E4FA81100F151BB62A071491CCEEE`; link export SHA-256 is `9EFC925A2E0ECD340EABC37C6E94AEDA8A4796880860C23D3D9CE2C495A6DCB3`. The pair has the same serialized task/target variable leaf names and label. The action's sequence path contains an `Objective_Markers.DisSeqVar_Task_30` definition (Custom_5 / Optional_HelpGrannyRags), but the package also has a different `Objectives_Manager.DisSeqVar_Task_30` (Custom_9 / Ovrsr_KillOverseerCambell). The exported `VariableLinks` text does not preserve the linked variable's object path or export index; choosing the same-sequence definition is a scoped candidate join, not proof of the pointer target. The bounded inventory also has no definition for `SeqVar_Named_4`, so the target actor/object is unresolved.

Across the 39 indexed actions, the same-sequence candidate join produces 54 Task-variable link occurrences over 49 distinct `(package, sequence_path, variable leaf)` instances; all 54 have one candidate definition under that scope. Five scoped task-variable instances have both index 1 and index 2 actions, and four index-1 actions link by `OutputLinks` to their index-2 partner. These are useful archive graph candidates; the serialized link exports do not give the task-variable object path/index, so the scope join remains a caveat.

### Exact-build native input-bit pattern

- Exact-build `FUN_00BA84D0` reads `param_1+0xA0` as an array descriptor and checks its count at `param_1+0xA4` for at least three entries.
- It reads bit 0 at entry-data offsets `+0x0C`, `+0x3C`, and `+0x6C`: three reads at a `0x30` stride, each `+0x0C` from the entry start.
- The pinned 2013 `source/Development/Src/Engine/Inc/EngineSequenceClasses.h` declares `FSeqOpInputLink` with `FStringNoInit LinkDesc` followed by `BITFIELD bHasImpulse:1`, and `USequenceOp::InputLinks` as `TArrayNoInit<FSeqOpInputLink>`. Header SHA-256: `F2B989AF0543EF8B0E4008648178BAEA2D133551ED5315DE2A08A6DD0493C18F`. This is external layout evidence, not target-binary proof. The target code establishes the observed `0x30` spacing; the preceding three-DWORD string header aligns the bit reads with the declared field order.
- The header is from the external `dishonoredrecompiled` source pinned in EXP-0182 at commit `e7829390fa1c2fc7c200357e9de695ad4c613527`; its README scopes the reconstruction to retail 2013 / engine 9411. The exact-build decompile cache `knowledge/cache/decompiles/00BA84D0.json` has SHA-256 `91738D7C17EA472804B1CA58A0F9BD90A00949FC72D6BE2F6E2C74714CF50BA6` and is bound to the registered build/hash.
- The same pinned source defines `UDisSeqAct_UpdateTaskTarget` fields `m_TargetIndex`, `m_pTargetActor`, `m_TargetName`, and `m_MarkerVanishPreset` at `+0xFC`, `+0x100`, `+0x104`, and `+0x110`; `source/Development/Src/DishonoredGame/Inc/DishonoredGameObjectivesClasses.h` SHA-256 is `F5153AB3CF81341C94ADF6DE6B773721DED71E73CA22D45CAF586461EEC7979E`, and assertions in `source/Development/Src/DishonoredGame/Inc/DishonoredGameLayouts.h` match those offsets (SHA-256 `F52C10720197B894203BC953DE4BE931634340CA2DFB4AF70D8B82473333F4D0`). `source/Development/Src/Core/Inc/DishonoredLayouts.h` asserts `sizeof(FStringNoInit)==12` (SHA-256 `8FE014D5B3663B80BA1C1422E7D65D051F80340DBB0B7AF4BE1DBB56458E8BAD`). These are versioned cross-source layouts, not names read from the target EXE.
- The candidate handler uses action `+0xFC` as the row index into the second argument's task-target descriptor at `+0x68`, with `0x24`-byte rows. Given the pinned field layout and EXP-0181/0182 dataflow, this strongly supports `m_TargetIndex` as an index into that task's `m_Targets` array. The method body is not recovered: the donor-body match is weak (0.609), and the external implementation is a stub.
- Exact-build constructor `FUN_00BB87E0` (27 bytes; cache SHA-256 `073D4C1787CB7612AB2C3D3055FB622B4D9794A55013C0A4E2F63E7499C1DC59`) calls base constructor `0x00414DB0`, then stores vptr `0x01158DE0`. The exact-build vtable candidate at `0x01158DE0` has slot `+0x190` pointing to `FUN_00BA84D0` (EXP-0179). The pinned retail-2013 function export maps the 27-byte constructor to `UDisSeqAct_UpdateTaskTarget::InternalConstructor` with a 1.000 neighbor match. This strongly corroborates class/table ownership for the handler slot; it does not upgrade the handler-body name, whose donor match remains order/0.609.
- The function then tests whether the selected `0x24`-byte task-target row exists. Its branch creates/updates a row when the first impulse is set, or when the third impulse is set and the row is absent; otherwise it removes an existing row when the second impulse is set or when the third impulse is set and the row exists. No matching impulse condition leaves the selected row unchanged.
- In raw target x86, the three impulse-bit loads occur at `0x00BA8528`, `0x00BA855C`, and `0x00BA8590`; the Set-to-create/update branch begins at `0x00BA85F7` and reaches row writes at `0x00BA8771`. The Clear test is at `0x00BA8612`; the Toggle path selects create/update for an absent row and removal for an existing row. The no-mutation exit is `0x00BA88D8`.
- A bounded search of 384 local decompile-cache pseudocodes found no other function with this same three-read array pattern. The search did not scan uncached functions, the full binary, or all assembly, so it does not establish uniqueness.
- Archive labels (`Set`, `Clear`, `Toggle`) and exact-build bit order/branch pattern align across sources. Mapping those labels to `FUN_00BA84D0` remains conditional: EXP-0179 has a weak external method-name match, and EXP-0182 treats the action-field crosswalk as corroboration, not a name embedded in the target code.

## Interpretation

- **Observed, archive-only:** 39 indexed actions occur in this corpus; repeated labels can have different indices and graph context. The Overseer pair is one example.
- **Observed, exact-build static:** `FUN_00BA84D0` reads three `+0x0C` bits from successive `0x30`-spaced entries, then its selected-row branch creates/updates, removes, or leaves the row unchanged according to the three bits and row presence.
- **Strongly corroborated, cross-source:** exact-build constructor vptr storage plus the versioned constructor export support the table's `UDisSeqAct_UpdateTaskTarget` class ownership, and its `+0x190` entry points to the handler candidate. The action field at `+0xFC` crosswalks to `m_TargetIndex` and is used to index the task's `+0x68` target-row array. Input-bit layout and archive labels align with `Set` / `Clear` / `Toggle`.
- **Unknown:** whether each archive index value selects the same row contents in build `10256413`; the handler's source-level method name/implementation; actual linked variable object identity where the export gives only a leaf name; retail Kismet property/link values; and runtime execution or marker visibility.

## Reproduction

1. Verify the EXE identity in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Run `python tools/audit_archive_target_index_census.py --inventory-dir <task_story_node_inventory> --links-dir <link_details> --csv-out <output.csv> --json-out <output.json>` against the two browser-archive export directories.
3. Recheck counts by unique `(package, object_path)`, index values, and the three input labels. The JSON gives exact hashes for each CSV input.
4. Resolve `FUN_00BA84D0` using the exact-hash build cache and inspect its three reads/branches. Confirm the external header SHA before using its field order.
5. Keep handler-to-class mapping conditional; do not infer target identity, retail archive values, or runtime behavior from these exports.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Exact-build task-target row/field crosswalk: [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md)
- Selector and marker consumer: [EXP-0184](EXP-0184-task-target-selector-to-marker-and-focus-path.md)
- Boyle archive/retail crosswalk: [EXP-0185](EXP-0185-boyle-archive-update-task-target-crosswalk.md)

