---
id: EXP-0181
title: Per-instance task-target array and archive-associated paths
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What object owns the target-record array accessed by the UpdateTaskTarget handler, and how do the indexed archive-associated paths access it?"
---

# EXP-0181 — Per-instance task-target array and archive-associated paths

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build accessor `FUN_00B27E60`, its three indexed direct callers, task-action candidate `FUN_00BA84D0`, record-copy helper `FUN_00A08A90`, and the two indexed functions that resolve the exact UTF-16 string `DisTaskTargetsSaveData`.
- Exclusions: no proof of the virtual method's save/load direction or persistence lifecycle, no complete record schema, no claim that every access to `+0x68` goes through the accessor, and no runtime observation. A bounded text scan of local decompile caches supplements the direct-call graph but does not cover the full binary.
- Portable raw evidence: [EXP-0181 task-target array JSON](../research/executable/evidence/EXP-0181-task-target-per-instance-array.json) records the target hash, accessor bytes, direct callers, receiver setup, literal locations, and claim limits.
- Exact-build caches: [00BA84D0](../knowledge/cache/decompiles/00BA84D0.json), [00B27E60](../knowledge/cache/decompiles/00B27E60.json), [00A0BA70](../knowledge/cache/decompiles/00A0BA70.json), [00A11780](../knowledge/cache/decompiles/00A11780.json), and [00A08A90](../knowledge/cache/decompiles/00A08A90.json). Each was checked for build ID `10256413` and the registered EXE SHA. `FUN_00ACC160` is cited only as an indexed call boundary in `FUN_00A0BA70`; its body is outside this experiment's scope.
- External naming lead: EXP-0179 records the candidate `UDisSeqAct_UpdateTaskTarget` vtable and handler association, but its donor method match is weak (`order`, 0.609; 882-byte donor vs 1,052-byte target). That label is not used as proof of property meanings here.

## Procedure

1. Recompute the installed EXE SHA-256 and use the exact-build function index/call graph to identify `FUN_00B27E60` and its direct callers.
2. Decode the accessor and all three callsites from the registered PE to identify the ECX receiver passed to the accessor.
3. Read-only decompile the update handler and descriptor-copy helper; record literal offsets, stride, and writes without importing external property names.
4. Search the target executable for UTF-16 `DisTaskTargetsSaveData`, map each occurrence and code reference through PE sections, and inspect the associated virtual calls.
5. Verify cited caches against the exact executable SHA/build ID and preserve uncertainties about dynamic method identity and lifecycle direction.
6. As a bounded secondary check, parse every local `knowledge/cache/decompiles/*.json`, validate build/hash metadata, search `pseudocode` for `0x68` and then same-file combinations of `0x68`, `0x6c`, and `0x70`, and manually inspect candidate contexts for a common descriptor base. This screen does not inspect assembly or uncached functions.

## Observations

- `FUN_00B27E60` is four bytes: `8D 41 68 C3`, disassembled as `lea eax, [ecx+0x68]; ret`. It returns the address `this + 0x68`; it is not a process-global array getter.
- The exact-build indexed direct-call graph has three callers: `FUN_00BA84D0` at `0x00BA859C`, `FUN_00A0BA70` at `0x00A0BB78`, and `FUN_00A11780` at `0x00A11908`. This bounds direct calls to the accessor, not every possible inline access to objects at `+0x68`.
- A bounded screen of all 368 local decompile-cache JSON files found no additional convincing pseudocode candidate using a common object base at `+0x68` with descriptor fields at `+0x6C/+0x70`. All 368 JSON files parsed and matched the registered build ID and EXE SHA. The screen used pseudocode text only, followed by manual candidate review; assembly, uncached functions, and the remaining indexed binary were not searched.
- At `0x00BA8593`, the UpdateTaskTarget handler candidate loads its second stack argument into ECX before calling `FUN_00B27E60`. The returned per-object descriptor is then indexed with action field `+0xFC`; rows use stride `0x24` and the descriptor's data/count/capacity fields at `+0/+4/+8`.
- `FUN_00BA84D0` has a create/update branch that grows or initializes rows through the selected index, writes row `+0x00` from action `+0x100`, fills outputs at row `+0x04` and `+0x10` through `FUN_00463BD0`, writes row byte `+0x1C` from action `+0x110`, and sets row `+0x20` bit 0 from second-argument `+0x60` bit 1. A separate branch removes selected rows and can prune null rows from the tail through `FUN_00BA6FA0`. Its action-side condition bits and record fields are retained as offsets; their semantic names are unknown.
- In `FUN_00A0BA70`, the exact string `DisTaskTargetsSaveData` is pushed to `FUN_009FAD70`, whose returned object is invoked through virtual slot `+0x138` with a local descriptor. The result then passes through `FUN_00ACC160`; when nonzero, that returned object's `+0x68` descriptor is the receiver of `FUN_00A08A90`, which copies entries from a local descriptor into it.
- In `FUN_00A11780`, an object selected from an owner array is passed as ECX to `FUN_00B27E60`. The function copies its `+0x68` descriptor into a nested descriptor in a temporary `0x10`-byte record, gathers those records, then resolves `DisTaskTargetsSaveData` and calls virtual slot `+0x138` for each temporary record.
- `FUN_00A08A90` treats its receiver and second argument as array descriptors, prepares destination storage, processes `0x24`-byte entries, and sets the receiver count from the source count. These two callers show transfers between object-owned descriptors and local/archive-associated records; they do not establish the virtual method's serialization direction.
- The exact UTF-16 literal occurs in target `.rdata` at file offsets `0x00CD4C3E` / `0x00CD4C6E` (VAs `0x010D623E` / `0x010D626E`). The corresponding `push` instructions are at `0x00A119F0` and `0x00A0BB40`; each is followed by a call to `FUN_009FAD70` and use of vtable slot `+0x138`.
- Function-index sizes are: `00BA84D0` 1,052 bytes; `00B27E60` 4; `00A0BA70` 321; `00A11780` 807; `00A08A90` 246; and `00ACC160` 181. The registered executable's recomputed SHA matches the build record.

## Interpretation

- **Observed, exact-build static:** the accessor returns an embedded `this+0x68` descriptor. The UpdateTaskTarget candidate uses the second argument as the receiver and operates on `0x24`-byte records. Two other indexed callers route descriptor data through code that resolves `DisTaskTargetsSaveData` and invokes a dynamic method at slot `+0x138`.
- **Inferred, archive association:** the literal and virtual call patterns support describing those two paths as `DisTaskTargetsSaveData`-associated archive/record processing. The exact class identity and the `+0x138` method's save/load direction are not established.
- **Unknown:** the row field meanings, the action condition-bit meanings, the exact owner class of the `+0x68` field, whether and where records persist between sessions, and whether all accesses use the four-byte accessor.
- **Limit:** exact offsets, pointer values, and code flow are target-build observations. `UpdateTaskTarget` and property labels come from an external cross-build symbol/layout source with weak method-match quality; they are not promoted to exact-build names.

## Reproduction

1. Verify the target SHA in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Resolve the six function starts/sizes and direct caller list in the exact-build index.
3. Recreate the PE mapping and decode `FUN_00B27E60`, callsites `00BA8593–00BA859C`, `00A0BB76–00A0BB83`, and `00A11903–00A11908`.
4. Search `.rdata` for the UTF-16 string, verify both VAs/raw offsets, and decode each call to `FUN_009FAD70` and the subsequent virtual `+0x138` dispatch.
5. Inspect `FUN_00BA84D0` and `FUN_00A08A90` caches, confirming their SHA/build metadata before interpreting their offsets.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Task-action virtual slot cross-check: [EXP-0179](EXP-0179-task-action-vtable-family.md)
- Related subsystem index: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
