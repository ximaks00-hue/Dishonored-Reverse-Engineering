# EXP-0014 — Native Blink owner attribution

**Status:** planned, NOT executed. **Build SHA-256:** `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (from first report). **Image base:** `0x00400000`, x86.

## Goal
Determine owner of `FUN_00956660` and exact meaning of its two lookups involving `BlinkBlender` and `Blink`. Do **not** infer that this method implements player teleportation.

## Preconditions
- Independently calculate the EXE SHA-256; separately record Ghidra's imported program SHA and loaded image base.
- Resolve Ghidra database lock, save and snapshot the project using supported Ghidra operations. Do not force-close active transactions.
- Store all raw extracted data locally under ignored directories. Do not execute unknown `dinput8.dll`.

## Procedure
1. Collect all references to `0x00956660`, `0x00592BE0`, `0x00454FE0`, `0x010A5830`, `0x010A5840`, and `0x010A66B0`.
2. Inspect +/- `0x80` around the candidate pointer at `0x010A66B0`. Check alignment and whether adjacent DWORDs point to recognized functions in executable memory. **Do not label as vtable from adjacency alone.**
3. Find references to candidate **table start** and constructor stores to candidate object, rather than only references to the method.
4. Within `FUN_00956660`, document registers, arguments, `this+offset` writes, branches and called functions.
5. For `FUN_00592BE0`, derive record stride and return type, and test whether the compared fields are truly FName-compatible or arbitrary integers.
6. Follow consumers of each returned third field. Determine whether each is an object/component pointer, numeric ID, or another type.
7. Cross-check findings against native UE3 metadata and distinct Blink properties. Build a call graph only for observed edges.

## Alternatives and falsification
- A virtual table is only one explanation for `.rdata`; other possibilities: callback table, dispatch table, interface method array, unrelated data.
- `BlinkBlender` may refer to animation/VFX/UI rather than ability targeting.
- Absence of direct UE3 Function exports in this UPK class does not imply that it has no inherited/native implementation.

## Deliverables
- Ghidra xrefs table (source RVA, destination RVA, reference type, source function, block).
- Pointer neighborhood with documented table boundaries or explicit unknown status.
- Two independent reasons supporting owner attribution or retained uncertainty.
- Three-field lookup representation and consumer-site references, if recoverable.
- Source digest, Ghidra version, date, queries and known parser limitations.
- Review note distinguishing observation, inference, rejected alternatives, open questions.

**Exit:** cannot mark confirmed without executing analysis on exact source build.