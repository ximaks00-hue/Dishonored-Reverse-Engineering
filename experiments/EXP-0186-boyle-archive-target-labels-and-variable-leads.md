---
id: EXP-0186
title: Boyle archive target labels and task/actor variable leads
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What target labels and variable references occur on the archive Boyle UpdateTaskTarget nodes that have exact-name retail export candidates?"
---

# EXP-0186 — Boyle archive target labels and task/actor variable leads

- Date: 2026-10-27 (Europe/Kiev).
- Retail comparison target: Steam x86 build `10256413`; exact Boyle Interior package SHA-256 `17BE4C7BD18F4E400DC053E0FCF61590240B38B0C3666F2F224676FFDFACCB86`.
- Archive property input: `task_story_node_inventory/L_Boyle_Int_Script.csv`, SHA-256 `6917FB27CE61A6BE108650D465D472114E7D6318F31A5508947B2DDCA75F205D`; original UPK hash/build identity is unavailable.
- Archive link input: `campaign_typed_links/link_details/L_Boyle_Int_Script_links.csv`, SHA-256 `14F5B16FA8808071544B2E13D0E5B9E952F8D16AE061D8E9BB7CAFDDF6B155C0`.
- Portable joined subset: [22-row archive target-label crosswalk](../research/packages/kismet-update-task-target/boyle-int-archive-target-name-crosswalk.csv), SHA-256 `ED3B2EBE303259A2F16FBAC04C31A07CB7BE820A5D6B97A5C265C0396E9D67FF`.
- Scope: read archive-exported `m_TargetName` strings, task/target variable references, output destinations, and task-variable definitions; join object names to the exact-hash retail export census by class/name/outer path. All browser-archive properties and links remain archive-only leads.
- This experiment does not read retail property payloads or retail Kismet connections.

## Observations

- The archive inventory contains 22 `DisSeqAct_UpdateTaskTarget` rows with property `m_TargetName` of type `StrProperty`. Each object name is among the 24 archive names matched to an exact-hash retail export candidate in [EXP-0185](EXP-0185-boyle-archive-update-task-target-crosswalk.md).
- There are 11 distinct archive target-label strings. Repeated labels include `A Clue`, `Lydia Boyle`, `Esma Boyle`, and `Waverly Boyle`; other labels include `Lord Brisby`, `Miss White`, `Cider Fountain`, `Lord Shaw`, `Upstairs`, `Boat in the Cellar`, and `(Outside) Samuel's Boat`. The joined CSV records each object/value pairing.
- The two names without an `m_TargetName` row in this particular inventory are `DisSeqAct_UpdateTaskTarget_9` and `_20`. This is a bounded inventory absence only; it does not establish that the underlying archive objects lack a label.
- Definitions for all 48 task-variable references across the 22 labelled nodes resolve in the same archive inventory. They point to tasks under objective `BoyleAssassination`; several target actions intentionally link to multiple task variables.
- Forty-seven of the 48 task-variable references point to `BoyleAssassination`. The remaining reference is `DisSeqVar_Task_170` on `_15` (`Lord Shaw`), which resolves in the archive to `DishonoredTask_Custom` under `PendeltonsNote`, despite the action's `Boyle_Objectives` outer path. This is a cross-objective archive clue and a high-value verification candidate, not evidence of a retail inconsistency.
- Repeated archive task bindings provide compact grouping leads: `_12` (`Miss White`) and `_13` (`Cider Fountain`) both link to `DishonoredTask_Custom_25`; the base action, `_1`, `_2` (`A Clue`) and `_14` (`Upstairs`) link to `_22`; `_10` (`Boat in the Cellar`) links to task definitions `_2`, `_3`, and `_4`.
- A separate package-wide archive object inventory (`PACKAGE_OBJECT_INVENTORY.csv`, SHA-256 `9F50D7AA1083FEB71573624889557706D9BB997CA524CB66FCA86AC58FB06397`) has no rows for `L_Boyle_Int_Script`. It contains a same-named `DisSeqVar_SpawnerPawn_1` under `L_Pub_FromBoyle_Script`, but no `_7`; that other-map `_1` is a name collision/control, not a definition of Boyle Interior's linked variable.
- Exact-hash retail export-name search on `L_Boyle_Int_Script.upk` (SHA-256 `17BE4C7BD18F4E400DC053E0FCF61590240B38B0C3666F2F224676FFDFACCB86`) returns one export each for `DisSeqVar_Task_165`, `DisSeqVar_Task_168`, `DishonoredTask_Custom_25`, `DishonoredTask_Custom_26`, and `DisSeqVar_SpawnerPawn_7`. It returns **two exact exports** named `DisSeqVar_SpawnerPawn_1` (UE Explorer rows 9210 and 9247). This confirms retail name/class presence only; the two `_1` rows are unresolved to the archive link, and no serialized links or actor values were read.
- Archive link rows connect `_11`'s task variable `DisSeqVar_Task_165` to `DisSeqVar_SpawnerPawn_1`, and `_12`'s task variable `DisSeqVar_Task_168` to `DisSeqVar_SpawnerPawn_7`. Their archive labels are `Lord Brisby` and `Miss White`. The companion inventory resolves the tasks to `DishonoredTask_Custom_26` and `_25`, respectively, but does not resolve either `SpawnerPawn` variable.
- Archive `_18` and `_19` are both labelled `Esma Boyle` and each links to archive-only RemoteEvent/StoryFlag-check output destinations. `_21`, `_22`, and `_23` are labelled Lydia, Waverly, and Esma Boyle and connect to archive-only StoryFlag checks. These links are retained in the CSV, not transferred to retail.

## Interpretation

- **Observed in the browser-archive exports:** target-action objects have human-readable `m_TargetName` strings and task/target variable references that cluster around named Boyle characters, a boat, and a fountain. This provides high-value candidates for matching archived target actions to task state and actor variables.
- **Candidate retail correspondence:** all 22 labelled action names join to exact-hash retail exports by class/name/outer path, and selected referenced task/spawner variable names exist in the exact-hash retail export catalog. The original archive package identity is missing; duplicate retail `_1` exports and absent payload access prevent a unique actor-variable join. Archive values/links do not establish that retail nodes have the same values or behavior.
- **Unknown:** retail target labels, actor references, task values, property equivalence, Kismet edge equivalence, the definitions of Boyle Interior `SpawnerPawn_*` and `SeqVar_Named_*`, native selector membership for any named actor, and runtime behavior.

## Next discriminating work

1. Resolve `DisSeqVar_SpawnerPawn_1`, `_7`, and relevant `SeqVar_Named_*` objects against other archive artifacts if available, retaining source hashes and archive-only status.
2. Prioritize retail payload verification for `_11`/`_12` dynamic-actor candidates and `_18`–`_23` story/event candidates only through an allowed exact-hash read-only source.
3. Prioritize `_15`/`Lord Shaw` to determine whether the archive cross-objective link has a corresponding retail task binding, if an allowed source becomes available.
4. Do not use name similarity alone to assign a retail actor, task, Kismet edge, or HUD marker.

## Links

- Retail export census: [EXP-0183](EXP-0183-boyle-update-task-target-export-census.md)
- Archive/retail name-path join: [EXP-0185](EXP-0185-boyle-archive-update-task-target-crosswalk.md)
- Exact-build native selector and consumers: [EXP-0184](EXP-0184-task-target-selector-to-marker-and-focus-path.md)
