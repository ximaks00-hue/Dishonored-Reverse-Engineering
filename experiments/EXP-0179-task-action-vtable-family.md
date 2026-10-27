---
id: EXP-0179
title: Task-action family virtual handler slot cross-check
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do related task-action classes use a shared exact-build virtual slot for their per-task handler, and which donor vtable mappings are reliable?"
---

# EXP-0179 — Task-action family virtual handler slot cross-check

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build PE `.rdata` pointer tables for SetTaskHidden, SetTaskState, UpdateCustomTask, and UpdateTaskTarget candidate vtables; shared slot neighborhood and each `+0x190` entry; donor function/global matcher quality.
- Exclusions: no runtime vtable observation, object-instance confirmation, or specific retail Kismet node association. Class and handler labels remain external candidates with the evidence quality shown below.
- Raw evidence: [EXP-0179 vtable slot JSON](../research/executable/evidence/EXP-0179-taskaction-vtable-family.json) records target EXE hash, candidate RVAs, raw offsets/bytes, source table hashes, and the rejected low-quality UpdateCustomTask table candidate.
- External symbol snapshot: `D:\Dishonored\01_REFERENCE\community\dishonoredrecompiled-main\resources\docs\symbols`; `functions_2013.csv` SHA-256 `C3B6821A018D30E2A317D95396B6584EB0C378BA5C0BD0075EC1E8C6C240CE88`, `match_2012_2013.csv` SHA-256 `06164572249FD3E2477F1C404B2AF6A27CACF83ACECB8C82DB08FCEDE037B330`.

## Procedure

1. Confirm registered EXE SHA-256 and PE image base.
2. For three donor vtable rows with strong `global-table` method/ratio, translate the 2013 RVAs to target VAs and read slots 93–100 from exact-build `.rdata`.
3. Verify the exact-build indexed function starts/sizes and donor handler-match rows for slot `+0x190` targets.
4. For UpdateCustomTask, inspect the weak donor table candidate separately; scan aligned exact-build `.rdata` DWORDs for the unique pointer to handler candidate `0x00B86880`, subtract `+0x190`, and compare neighboring slots with the other task-action tables.
5. Keep raw slot observations separate from inferred class names and donor method labels.

## Observations

- Four exact-build table candidates share the same seven DWORDs in slot indices 93–99 (`+0x174` through `+0x18C`): `00BA8300, 006D9680, 00459D10, 006CF2C0, 006FEF20, 00459D10, 005CB0C0`. The first pointer `00BA8300` is independently mapped as a low-confidence candidate for `UDisSeqAct_TaskAction::Activated` in EXP-0177.
- At slot index 100 (byte offset `+0x190`), the exact-build tables contain:

| Candidate table identity | Table RVA | Exact-build slot target | Target index size | Donor method/name evidence |
| --- | ---: | ---: | ---: | --- |
| `UDisSeqAct_SetTaskHidden` | `0x00D58780` | `0x00B86820` | 25 bytes | `HandleTaskInstance`, `bytes`, 1.000, 25/25 |
| `UDisSeqAct_SetTaskState` | `0x00D58918` | `0x00B86840` | 23 bytes | `HandleTaskInstance`, `bytes`, 1.000, 23/23 |
| `UDisSeqAct_UpdateCustomTask` candidate | `0x00D55430` | `0x00B86880` | 16 bytes | `HandleTaskInstance`, `neighbours`, 1.000, 16/16 |
| `UDisSeqAct_UpdateTaskTarget` | `0x00D58DE0` | `0x00BA84D0` | 1,052 bytes | `HandleTaskInstance`, `order`, 0.609, donor 882 bytes |

- The three high-confidence donor table rows are `global-table` matches at ratio 1.000 for SetTaskHidden, SetTaskState, and UpdateTaskTarget. Their target `.rdata` entries at `+0x190` point to the handler candidate VAs above.
- The donor matcher assigns the UpdateCustomTask vtable name to RVA `0x00D59C60` with only `global-votes`, ratio 0.800. In exact-build bytes at that table candidate, slots 93–99 do not match the shared task-action sequence and slot `+0x190` points to `0x00BA1670`.
- Donor rows identify `0x00BA1670` as `UDisSeqAct_GameOver` scalar deleting destructor (vtable method, ratio 1.000, 38/38), while the exact-build index size is 38 bytes. This contradicts treating table `0x00D59C60` as the UpdateCustomTask table for this executable.
- An aligned `.rdata` scan finds exactly one pointer to `0x00B86880`, at RVA `0x00D555C0`. Subtracting the shared handler slot offset `0x190` gives candidate table RVA `0x00D55430`; this table has the same slot-93–99 fingerprint as the three strong task-action tables and points to `0x00B86880` at slot `+0x190`.
- Target table and slot bytes, image-base calculations, source hashes, and rejected candidate are retained in the linked JSON. The registered executable hash was verified before reading.
- **Constructor ownership cross-check (EXP-0187):** exact-build `FUN_00BB87E0` (27 bytes) calls base constructor `0x00414DB0` and stores vptr `0x01158DE0`, the table above. The pinned retail-2013 function export labels the same VA as `UDisSeqAct_UpdateTaskTarget::InternalConstructor`; the cross-build neighbor match is 1.000 at 27/27 bytes. This strongly corroborates the table's class ownership. It does not improve the separate handler-body match at `0x00BA84D0`, which remains order/0.609. See the [portable constructor crosswalk](../research/executable/evidence/EXP-0187-update-task-target-handler-crosswalk.json).

## Interpretation

- **Observed, exact-build static:** all four candidate tables have the same seven-entry slot sequence at indices 93–99, followed at index 100 by four distinct function pointers. Three pointers align with donor-labeled handler functions; the fourth (`00BA84D0`) has a weak order-based donor label.
- **Inferred, shared family layout:** the shared prefix and unique handler-pointer pattern support interpreting `+0x190` as a common per-task dispatch slot across these task-action classes. The class identity for the UpdateCustomTask table at `0x00D55430` is inferred from its unique handler pointer and the family fingerprint, not from the donor global-table row.
- **Rejected, target table association:** donor-derived UpdateCustomTask table RVA `0x00D59C60` is not supported for the registered executable: it has a different neighbor fingerprint and points at a GameOver destructor candidate in the shared handler slot. Keep that donor row as a false/low-confidence cross-build association for this target.
- **Inferred, handler labels:** SetTaskHidden and SetTaskState have byte-perfect donor function matches; UpdateCustomTask is a neighbor match; UpdateTaskTarget is a low-confidence order match with a 170-byte size discrepancy. Do not treat all four names as equally established.
- **Unknown:** runtime instance vptrs, actual invocation of each handler, per-node variable-link values, and downstream gameplay/UI effects for hidden/custom/target actions.
- **Limit:** exact bytes establish pointer values in the registered EXE. They do not independently identify C++ class names; those names use external 2013 symbols and cross-build matching.

## Reproduction

1. Verify the target EXE SHA in `research/builds/BUILD-STEAM-10256413/build.md`.
2. Recreate the PE section/RVA-to-file-offset map and compare the linked JSON's raw DWORDs at each candidate table plus offsets `0x174`–`0x190`.
3. Re-scan aligned `.rdata` DWORDs for `0x00B86880`; verify the unique hit at RVA `0x00D555C0` and candidate base `0x00D55430`.
4. Resolve target function sizes in `research/executable/functions.csv` and donor rows in the symbol snapshot; preserve matcher method, ratio, and size differences.
5. Re-evaluate the `0x00D59C60` table row separately; do not transfer its class label to the target table without new discriminating evidence.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Generic task-action link resolution: [EXP-0177](EXP-0177-kismet-task-variable-to-native-dispatch.md)
- Task-action gating: [EXP-0178](EXP-0178-task-action-objective-and-hud-gates.md)
- UpdateTaskTarget input/class crosswalk: [EXP-0187](EXP-0187-task-target-input-actions-and-index-census.md)
- Objective/task/HUD cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
