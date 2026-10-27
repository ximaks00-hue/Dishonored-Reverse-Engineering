---
id: EXP-0184
title: Task-target selector consumers and marker-object construction
experiment_status: done
claim_status: mixed
build: "10256413"
question: "How do exact-build task-target records flow from the selector into marker objects and actor-focus checks?"
---

# EXP-0184 — Task-target selector consumers and marker-object construction

- Date: 2026-10-27 (Europe/Kiev).
- Target executable: Steam app `217980`, x86 build `10256413`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Portable evidence: [machine-readable evidence record](../research/executable/evidence/EXP-0184-task-target-selector-to-marker-and-focus-path.json).
- Scope: exact-build decompile-cache/callgraph review for the selector, its marker-building caller, a second consumer, constructor, and a virtual-table path; the unindexed update candidate was bounded with raw target x86.
- No game launch, runtime trace, package decompilation, memory write, or binary patch was performed.

## Procedure

1. Confirm the registered EXE SHA-256 in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Inspect exact-build decompilation caches for `FUN_00AD9910`, `FUN_00BAD550`, `FUN_00C36920`, `FUN_00BCE750`, and `FUN_00BB9FA0`; verify each cache records the same build ID and EXE hash.
3. Follow direct callsites and fields from selector output to its consumers. Treat Ghidra pseudocode as a decompiler rendering of target instructions, not as original source.
4. Read the target PE pointer table at VA `0x011635A8`, map its raw file offset, and verify its slot pointers against the indexed function boundaries and the raw unindexed body at `0x00BC57F0`.
5. Compare external function labels only as crosswalk candidates; retain target addresses and exact byte/call evidence as primary observations.

## Observations

### Selector behavior

- `FUN_00AD9910` walks owner/objective entries, task entries, and per-task target descriptors. It checks objective state byte `+0x45`, objective flags at `+0x48`, task flags at `+0x60`, task state byte `+0x5D`, and target actor fields.
- For each accepted target row, it appends the **row address** (`task + 0x68 + index * 0x24`) to its output array. The selector does not copy a display name or construct a marker object.
- It excludes rows with a null actor pointer, actor byte `+0x120` bit 3 set, or actor DWORD `+0x0C` mask `0x20000000` set. Optional selector parameter `param_3` adds objective/task bit gates (`+0x48` bit 5 and task `+0x60` bit 4). These are observed numeric predicates; their semantic labels remain open.
- The exact-build function index reports two direct callers, and an independent raw `.text` scan found exactly two direct `E8 rel32` call references: `FUN_00BAD550` at `0x00BAD5E7` and `FUN_00C36920` at `0x00C36BC7`. No absolute-pointer reference to the function VA was found in the file scan. This bounds statically identifiable direct callers, not dynamically computed or otherwise indirect dispatch.

### Marker-object consumer

- `FUN_00BAD550` calls the selector at `0x00BAD5E7` only when its owner flag at `+0x1C0` has bit `0x80` set. It iterates returned row pointers and deduplicates them against existing marker objects by comparing each existing marker object's `+0x08` pointer to the row's first DWORD.
- Raw x86 at `0x00BAD5E1` pushes `1` as selector `param_3`; this caller therefore enables the extra objective `+0x48` bit `0x20` and task `+0x60` bit `0x10` gates.
- For each nonduplicate row it chooses one of two settings pointers according to row DWORD `+0x20` bit 0, allocates `0x88` bytes, and calls `FUN_00BCE750` at `0x00BAD6C1` with the row pointer, selected settings, and owner context. Bit clear selects settings base `owner+0x1B0` plus `0x6FC`; bit set selects the same base plus `0x744`. The result is stored in the marker-object array at owner `+0x524`; the same object pointer is also appended to a second array at `+0x554`.
- A pinned 2013 UI layout labels these settings offsets `m_TaskMarkerSettings` and `m_OptionalTaskMarkerSettings` (header SHA-256 `E7018174981593A15B3BAAC10E54E4C68923A94F83A0E668BA84BFA3EACBEAE6`; static-assert file SHA-256 `F52C10720197B894203BC953DE4BE931634340CA2DFB4AF70D8B82473333F4D0`). The target pointer choices are exact, but the field names are cross-source labels. Row `+0x20` bit 0 is consistent with the external `m_bOptional` bitfield order; the individual bit offset is not asserted against target bytes.
- `FUN_00BCE750` passes row DWORD `+0x00` to `FUN_00BCE380`; consumes FString-shaped members at `+0x04` and `+0x10` with counts at `+0x08` and `+0x14`, passing them to a helper with the exact literal `L"m_TargetName"`; and installs vtable pointer `0x011635A8` at the new object's first DWORD.
- `FUN_00BCE380` stores its second argument at object `+0x08`, its third at `+0x0C`, and its fourth at `+0x10`. Thus the target row's first pointer flows to object `+0x08`, the selected settings pointer flows to `+0x0C`, and the owner-context pointer flows to `+0x10`. Vtable slot 4 points to `FUN_00BB9FA0`, which reads object `+0x08` and fetches coordinates from the referenced object at `+0xC4`, `+0xC8`, and `+0xCC`, with a helper-derived Z adjustment. This is direct static pointer/dataflow evidence for the location calculation path, without proving runtime display or the referenced object's semantic class.
- Raw x86 at `0x00BCE890` loads the byte at `row + 0x1C` with `movzx`. Value `0` stores `settings+0x38` into marker-object `+0x48`; value `1` stores `owner-root+0x790`; value `2` stores `owner-root+0x7A0`; other values leave that field unset. The exact-build handler candidate copies action byte `+0x110` into row `+0x1C` (EXP-0181). This proves a three-way pointer-selection branch in marker-object setup, not a visible vanish effect.
- A pinned `dishonoredrecompiled` source at commit `e7829390fa1c2fc7c200357e9de695ad4c613527` (retail 2013 / engine 9411) declares `EDisTaskMarkerVanishPreset` values `DTTVP_Default=0`, `DTTVP_VeryClose=1`, `DTTVP_Never=2`, `DTTVP_MAX=3`. `DishonoredGameEngineShims.h` SHA-256 is `28C42700560E38AFDBB8ECD46D11065E9CD4BC89F8DFD8DFDC045A0216D7D2CA`. Its `UDisSeqAct_UpdateTaskTarget::m_MarkerVanishPreset` and `FDisTaskTarget::m_VanishPreset` fields are declared as bytes in `DishonoredGameObjectivesClasses.h` (SHA-256 `F5153AB3CF81341C94ADF6DE6B773721DED71E73CA22D45CAF586461EEC7979E`); retail-2013 assertions in `DishonoredGameLayouts.h` place them at action `+0x110` and row `+0x1C` (SHA-256 `F52C10720197B894203BC953DE4BE931634340CA2DFB4AF70D8B82473333F4D0`). `DishonoredGameUIClasses.h` declares settings members `m_VanishPreset_VeryClose` and `m_VanishPreset_Never` (SHA-256 `E7018174981593A15B3BAAC10E54E4C68923A94F83A0E668BA84BFA3EACBEAE6`). The versioned labels therefore match the byte values and observed offsets, but remain cross-source names, not symbols recovered from the target EXE. The pinned source has no handler implementation using the enum, so the visible semantics of the three target pointer choices remain unknown.
- The available browser/editor exports do not contain any serialized vanish/preset property for these actions: the bounded `task_story_node_inventory` slice has 36 files, 384 unique actions and 430 action-property rows; 37 matching `link_details` CSVs have 1,166 action-property rows. Neither slice contains `m_MarkerVanishPreset`, `m_VanishPreset`, or a property name containing `vanish`/`preset`. This is absence only from these filtered exports, not proof about source package payloads. The inventory-manifest SHA-256 is `221AAB7F5707D3C0887381FC7FAE961AFC4F1D78350D1652AF01350F80FC8A37`; link-manifest SHA-256 is `7E4460E51CFD8C62BC64892192BF4A8C5E0850F1BF9E225B34D1D8A89A6EA76A`.
- The raw pointer table at VA `0x011635A8` (file offset `0x00D61FA8`) has slot 4 = `0x00BB9FA0` and slot 5 = `0x00BC57F0`. `FUN_00BB9FA0` is an indexed 75-byte body that reads the object `+0x08` actor-like pointer and copies coordinates from `+0xC4/+0xC8/+0xCC`, with a helper-derived Z adjustment.
- `0x00BC57F0` is absent from the function index. Raw x86 at RVA `0x7C57F0` decodes as a function-like body of 837 bytes ending in `ret 0x18` at VA `0x00BC5B32`; the next indexed start is `0x00BC5B40`. It calls indexed `FUN_00BBD430` at `0x00BC5865`. The external matcher labels `0x00BB9FA0` as `FDisTaskMarker::GetLocation` with an exact byte match and labels `0x00BC57F0` as `FDisTaskMarker::Update` with a neighbor-based score of 0.929; keep both names as crosswalks, especially the unindexed one.
- In the raw `0x00BC57F0` body, no direct branch on preset values `0/1/2` was found. Several masks apply to a stack argument identified by the external candidate signature as flags; that does not establish visible vanish behavior.
- The exact-build owner path calls `FUN_00BB00C0` from `FUN_00BB2280` at `0x00BB23C4`. The wrapper calls `FUN_00BAD550` at `0x00BB00C7`, then the separate `FUN_00BAD960`, and loops over the secondary array at owner `+0x554`/count `+0x558`, invoking slot `+0x0C` on each object. In this vtable, slot `+0x0C` points to `FUN_005CB0C0`, whose target bytes are `C2 04 00` (`ret 4`), a no-op stub. The call is observed, but it does not establish an object update effect.
- Vtable slot `+0x14` points to unindexed body `0x00BC57F0`, the external `FDisTaskMarker::Update` candidate. A raw PE scan found no direct `.text` call to that VA; its only absolute pointer occurrence is this vtable entry at file offset `0x00D61FBC`. The target proves slot membership, not that this method is invoked.
- In `FUN_00BAD550` reconciliation, matching prior objects are retained by equality between existing object `+0x08` and candidate row first DWORD. For stale tail entries, raw x86 at `0x00BAD88E–0x00BAD8A3` sets ECX to owner `+0x554` and pushes the address of the current entry in primary owner `+0x524`, then calls `FUN_00B36C00`; the helper removes that pointer from the secondary array. The object then receives a slot-0 callback with argument `1`, followed by `FUN_00A4DDD0` with ECX=owner `+0x524`, the current index, and count `1`, removing the primary entry. The callback's semantic effect remains unknown here. The distinct `FUN_00BAD960` cleanup path is analyzed in [EXP-0188](EXP-0188-parallel-task-marker-reconciliation-paths.md).

### Second selector consumer: actor-focus membership

- `FUN_00C36920` performs a periodic trace using actor/camera context, stores a hit actor pointer at `this + 0x12C`, and under timer/flag gates calls `FUN_00AD9910` at `0x00C36BC7`.
- Raw x86 shows this caller pushes `EBX` as selector `param_3`; `EBX` was zeroed at function entry. It therefore uses the same base selector filters without the two extra nonzero-parameter bit gates.
- It compares the first DWORD of each returned target row to the current hit actor pointer. A match sets a local membership flag and takes a distinct downstream branch that writes the hit actor into a response object at `+0x20`, passes mode `0x78` to `FUN_00AA23F0`, and updates a timer through `FUN_00C45D10`; the alternate path can pass `0x79` after scanning a separate actor-associated array.
- This is a second exact-build consumer of selector rows, consistent with target-actor eligibility affecting a focus/interaction response. The higher-level feature name and runtime effect are not established.

## Interpretation

- **Observed:** task-target row addresses feed both marker-object construction and a separate hit-actor membership check. This connects the per-task target descriptor documented in [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md) to two native consumer paths.
- **Strong static connection:** the row's first pointer is stored at marker-like object `+0x08`, and vtable slot 4's indexed function reads that field to obtain coordinates. The constructor also installs the pointer table whose slot 5 points to a raw unindexed update candidate. This establishes object/vtable/dataflow structure, not execution of either virtual method.
- **Observed lifecycle connection:** the owner wrapper reconciles selected rows, calls a no-op slot-`+0x0C` stub for secondary entries, and removes stale entries from the secondary `+0x554` and primary `+0x524` arrays in the order documented above. The external update candidate is only proven as vtable slot `+0x14`; no direct invocation was found. The companion primary `+0x530` cleanup is documented separately in EXP-0188.
- **Cross-source inference:** `FDisTaskMarker`, `GetLocation`, `Update`, and the preset enum/field names are external 2013 layout/matcher labels. `GetLocation` has a byte-exact match; the update label is weaker and the target body is not in the static function index. The enum's numeric values agree with the exact-build row-byte branch, but the target-visible meaning is unknown.
- **Unknown:** which Boyle `DisSeqAct_UpdateTaskTarget` node populates the observed records; serialized retail node values/links; semantic names for selector bit predicates; runtime target eligibility, marker visibility, update behavior, or preset effects.

## Next discriminating work

1. The archive-to-retail export joins are now recorded in [EXP-0185](EXP-0185-boyle-archive-update-task-target-crosswalk.md) through [EXP-0187](EXP-0187-task-target-input-actions-and-index-census.md). Recover retail serialized values and links only through an allowed exact-hash source; do not transfer browser-archive edges to retail facts. Prioritize distinguishing duplicate leaf-only task-variable references and ambiguous actor exports.
2. Continue only with permitted retail serialized-value/link recovery and high-value exact-build field consumers; the parallel reconciliation path and both stale-entry array updates are documented in EXP-0188. Keep marker preset labels cross-source until the target's visible behavior is independently established.
3. Keep the task-target flag domains distinct from task state, objective state, notification codes, and popup event bytes documented in [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md).

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Task-target layout and storage: [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md), [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md)
- Boyle export census: [EXP-0183](EXP-0183-boyle-update-task-target-export-census.md)
- Evidence cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
