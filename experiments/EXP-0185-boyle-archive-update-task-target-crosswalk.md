---
id: EXP-0185
title: Boyle archive UpdateTaskTarget to retail export-name crosswalk
experiment_status: done
claim_status: mixed
build: "10256413"
question: "How many browser-archive Boyle Interior UpdateTaskTarget objects have exact-name retail export candidates, and what archive-only links can prioritize future verification?"
---

# EXP-0185 — Boyle archive UpdateTaskTarget to retail export-name crosswalk

- Date: 2026-10-27 (Europe/Kiev).
- Retail target: Steam x86 build `10256413`, EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Retail package: `L_Boyle_Int_Script.upk`, SHA-256 `17BE4C7BD18F4E400DC053E0FCF61590240B38B0C3666F2F224676FFDFACCB86`.
- Archive input: `L_Boyle_Int_Script_links.csv`, SHA-256 `14F5B16FA8808071544B2E13D0E5B9E952F8D16AE061D8E9BB7CAFDDF6B155C0`; local browser-port research corpus. The source package SHA-256 was not available.
- Portable joined subset: [24-row archive-to-retail crosswalk CSV](../research/packages/kismet-update-task-target/boyle-int-archive-retail-name-crosswalk.csv), SHA-256 `B0CF9E5F18B9B62C109A44A6BBD504E93D50A05855B95B674B8995BE4281CFC8`.
- Scope: compare archive `DisSeqAct_UpdateTaskTarget` object class/name/path with exact-hash retail package export rows; retain archive variable-link and output-link metadata as archive-only fields.
- No compressed retail package property payload was read or decompiled.

## Procedure

1. Read the archive link-detail CSV and group property rows by the full object path for class `DisSeqAct_UpdateTaskTarget`.
2. Read the exact-hash Boyle Interior retail export subset recorded in [EXP-0183](EXP-0183-boyle-update-task-target-export-census.md).
3. Join archive objects to retail exports by exact class, object name, and the shared outer path `TheWorld.PersistentLevel.Main_Sequence.Boyle_Objectives`; do not join by numeric index.
4. Preserve each tool's export-index convention independently. For matched objects, carry the archive `Task`/`Target` linked-variable names and any serialized archive output links into a review CSV labelled archive-only.
5. Compare the full distinct-name sets, record unmatched objects on either side, and retain source hashes and missing archive package identity as provenance limits.

## Observations

- The archive CSV contains 72 property rows for 24 distinct `DisSeqAct_UpdateTaskTarget` objects, all under `Boyle_Objectives`.
- All 24 archive object names have one matching retail export with the same class, object name, and outer path. The exact-hash retail census contains 25 objects in that sequence; `DisSeqAct_UpdateTaskTarget_41` is retail-only relative to this archive corpus.
- The archive rows use export indices around 10617–10640. Retail UELib `tableIndex` values are 8790–8814, while UE Explorer `export_index` values are 8789–8813. These indexes belong to different inventories and are not comparable identities.
- The crosswalk CSV contains one row per matched name and records archive `Task` and `Target` linked-variable references, archive output links where present, retail table/export indices, package SHA-256, serial offset/size, and outer path. All 24 objects contain both `Task` and `Target` variable-link group blocks; 23 have nonempty `Task` references, 23 have nonempty `Target` references, and 22 have both. The two `LinkedVariables=none` values are preserved explicitly. Ten rows contain output links (13 linked destination/input pairs).
- Examples of archive-only task-target output destinations include `_18`/`_19` to `ActivateRemoteEvent_46` and `CheckStoryFlag_14`, and `_21`/`_22`/`_23` to `CheckStoryFlag_26`/`_25`/`_11`. Other archive links involve task-state setters, touch events, level-loaded events, and task variables. The joined CSV preserves the per-object link metadata; these are not asserted as retail links.
- The archive source lacks the original UPK hash, and same-name/path identity does not prove byte-identical serialized properties or graph edges across archive and retail builds.

## Interpretation

- **Observed candidate crosswalk:** class/name/outer-path matching yields 24/24 archive-name candidates among 25 exact-hash retail exports. This makes the matching objects concrete priorities for later payload comparison.
- **Archive-only evidence:** linked-variable names and output destinations help select informative candidates and expose what a retail verification would need to test. They remain claims about the browser-archive CSV only.
- **Unknown:** retail node properties, target actors, target presets, task bindings, Kismet links, handler reachability, archive source build identity, and runtime behavior. The retail-only `_41` object is an unmatched name, not evidence of a new or changed gameplay feature.

## Next discriminating work

1. Use an allowed read-only exact-hash source to inspect a small set of high-value retail exports, beginning with archive nodes whose output links connect to task-state/story/event nodes.
2. Compare serialized fields and links property-by-property; record the retail package hash and exact export identity before confirming any archive-to-retail equivalence.
3. For nodes still inaccessible under the compressed-UPK policy, preserve them as candidate tasks rather than importing archive edges into the retail evidence graph.

## Links

- Retail census: [EXP-0183](EXP-0183-boyle-update-task-target-export-census.md)
- Native selector and marker consumers: [EXP-0184](EXP-0184-task-target-selector-to-marker-and-focus-path.md)
- Objective/task/Kismet/HUD evidence cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
