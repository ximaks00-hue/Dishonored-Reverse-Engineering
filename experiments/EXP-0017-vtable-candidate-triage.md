---
id: EXP-0017
title: "Vtable candidate triage for power-selection slots"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Which pointer-run/constructor vtable candidates match PowerWheel/Controller slots, and which are false positives?"
---
# EXP-0017 — Vtable candidate triage for power-selection slots

- Status: two pointer-run candidates and one directly constructor-installed PhysX vftable rejected for the proposed slots; Controller and PowerWheel owners unresolved. A broader read-only constructor-assignment scanner is now available.
- Date: 2026-10-26.
- Binary: workspace `Dishonored RHCP/Binaries/Win32/Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`; x86 little-endian; image base `0x00400000`; 72,925 functions. `list_databases` identifies the workspace EXE; `get_database_info` continues to report stale SteamLibrary path metadata. No Ghidra database save/rebind was attempted.
- Scope: read-only raw PE pointer-run scan, Ghidra xref/decompiler validation, and local temporary CSV output. No game files or Ghidra program bytes/types were changed; `_excluded_coop_project/` was not accessed.

## Identifier note

The supplied REV-0003 text names a vtable-candidate scan “EXP-0015”. In this workspace, `EXP-0015` already records the player-pawn Blink default-object graph. To avoid replacing or duplicating that record, this separate executable scan is recorded as `EXP-0017`.

## Procedure

1. Ran [`vtable_candidate_scan.py`](../tools/analysis/vtable_candidate_scan.py) against the hash-identified workspace EXE. It scans aligned 32-bit words in PE `.rdata` and `.data` for contiguous values that fall inside `.text` and reports runs meeting the requested minimum length.
2. Generated a local-only CSV at `.tmp/vtable-candidates.csv` with `--minimum-pointers 345`, the minimum run length that could contain byte offsets `+0x1F0` and `+0x560`.
3. Treated each row as a pointer-run candidate, not as a vtable. Queried Ghidra references and constructor/decompiler evidence for a high-ranked candidate before assigning any method meaning.

## Direct constructor-assignment follow-up

The original scan only reported the start of long pointer runs. Those runs can contain multiple adjacent tables, so a referenced table can begin in the middle of a run. Added [`vtable_assignment_scan.py`](../tools/analysis/vtable_assignment_scan.py) to scan the indexed Ghidra function bodies for 32-bit `mov [object+0], immediate` stores into `.rdata`/`.data`, then score the assigned address at selected slot offsets.

Against the same EXE SHA-256 and workspace function index (`functions.csv`, 72,437 indexed functions), the tool found 10,002 direct object-base pointer assignments at 4,267 unique addresses. Requiring all 11 configured offsets (`+0x1F0`, `+0x4F8` through `+0x518`, and `+0x560`) to equal indexed function starts still yielded 1,176 candidates. These are not 1,176 proven vtables: long adjacent function-pointer arrays and overlapping candidate starts make this a broad candidate set. Constructor shape, table boundaries, names, and target semantics remain required.

### Rejected candidate: `NxScene::vftable` at `0x0120750C`

The direct-assignment pass surfaced address `0x0120750C` inside a previously merged pointer run. Ghidra's `list_names` identifies it as `NxScene::vftable` (the preceding metadata pointer is at `0x01207508`; `NxdScene::vftable` is separately identified at `0x01207814`). Constructor/destructor evidence agrees: `FUN_00ED5080` and `FUN_00ED5090` install the `NxScene` table; teardown routine `FUN_00ED82D0` installs `NxdScene` at entry, releases PhysX resources, and restores the base `NxScene` table during cleanup.

The exact DWORD at `NxScene::vftable + 0x1F0` is `0x00EC3C8E`, Ghidra's `purecall` entry. The tempting neighboring entry at `+0x4F8` is `FUN_00ED58C0`, whose body forwards a no-argument call to an inner object's vtable slot `+0x1F0`; it is not the target of wrapper `FUN_009F8290`, which passes an integer. At `+0x560`, `FUN_00ED5AE0` similarly forwards a no-argument call to an inner object's slot `+600`. This directly rejects the table for both proposed UE3 slots and shows why a broad run/offset match can misattribute a middleware vftable.

Reproduction output is local and ignored at `.tmp/vtable-assignment-candidates-baseptr.csv`. The scanner is read-only and did not change the Ghidra project or game files.

## Observations

- The raw scan emitted **215 pointer runs** of at least 345 entries across `.rdata` and `.data`. This is not a count of vtables. Runs can combine adjacent tables, pointer arrays, switch data, or other executable-address data; the large count makes xref and semantic validation mandatory.
- Candidate run `0x00FF5608–0x00FF8CFB` contains 3,517 aligned pointers into `.text`. Ghidra reports code/data references to the start from `FUN_0057D960` and `FUN_00585770`. Decompilation confirms `FUN_0057D960` writes `&PTR_FUN_00FF5608` to the object's first DWORD; `FUN_00585770` also installs that pointer after a base initialization call. This supports that the address is an object method/function table in this construction path.
- The DWORD at table byte offset `+0x560` (`0x00FF5B68`) is `0x005656D0`. Ghidra resolves that address inside `FUN_00565680`; decompilation of the containing function maps integer cases to wide strings such as `TMGS_SimpleAverage`, `TMGS_Sharpen0` … `TMGS_Sharpen10`, `TMGS_NoMipmaps`, and `TMGS_LeaveExistingMips`.
- **Rejected for `Dis_SelectPower`:** this candidate's `+0x560` entry leads into a texture-mip-generation label conversion routine, not a player power-selection implementation. This is a concrete false positive for slot-only/raw-pointer-run matching. It does not identify the table's exact class name, and it does not resolve the real controller target.
- Candidate run `0x011AC348–0x011AEF6B` has constructor references and spans the `+0x1F0` slot, but its owner and target were not semantically attributed in this pass. It remains only a candidate run, not an asserted PowerWheel vtable.
- Follow-up validation of `0x011AC348`: `FUN_00CBE4C0` writes this pointer into the object's first DWORD. The DWORD at `0x011AC538` (`+0x1F0`) is `0x004957C0`, inside `FUN_004957C0`. Its decompilation follows a generic object creation/attachment path through `FUN_004955A0`; Ghidra inferred a `__thiscall` signature with three stack arguments after `this`, while wrapper `FUN_009F8290` dispatches one parsed DWORD at `+0x1F0`. This parameter-count mismatch and unrelated-looking body reject the candidate as the PowerWheel `OnSelectionChanged` target for now. The decompiler's inferred types/calling convention are not ground truth, so this is a strong rejection of this candidate, not a semantic name for the owner.

## Conclusions and limits

**Confirmed:** the scanner's candidate count and raw pointer values for this EXE; constructor-installed pointers at `0x00FF5608` and `0x011AC348`; the values stored at their tested slots; and the observed behavior of the containing code routines.

**Not established:** that any scanned run belongs to `DishonoredPlayerController` or `DisGFxMoviePlayerPowerWheel`; the concrete targets at controller `+0x560` or PowerWheel `+0x1F0`; conversion among values `24`, `2`, `0`, and `_ShortcutIdx`; or any path into Blink or position update.

Both scanners are candidate generators only. The pointer-run scanner does not decode instructions or split adjacent arrays. The constructor-assignment scanner recognizes only direct 32-bit immediate stores to a selected object-field offset, and can miss pointers copied through registers/globals or nonzero base subobjects. Neither scanner proves table boundaries or owners. Candidate validation still requires constructor context, class/type evidence, and target behavior. Do not select a controller vtable merely because a candidate has an entry at `+0x560`.

### Package-property offset check

As a second route for joining package fields to native code, a .NET reflection walk inspected the complete UELib runtime type hierarchy and instance fields for `DishonoredPlayerPawn.m_pBlinkPower`, `DishonoredPawn.m_ActivePowers`, and `DishonoredPlayerController.m_WheelCurrentSelection`. The parsed objects expose names, owner/class references, property flags, array dimension, and replication metadata, but no serialized/native `Offset` field. `ElementSize` and `RepOffset` were zero in these three objects. This confirms that UELib 1.13.3 does not provide the needed property-to-native-offset join through these reflected objects; zero values are not valid field offsets and must not be interpreted as such. Full local output: `.tmp/ue-readonly-dump/EXP-0017-uproperty-reflection.log`.

A class-level reflection pass over `DishonoredPawn`, `DishonoredPlayerPawn`, `DishonoredPlayerController`, and `DisGFxMoviePlayerPowerWheel` found their class flags, native-class binding names, child-field chains, and function maps, but no `PropertiesSize`, `StructSize`, or per-property native offset member exposed by these UELib objects. The output is `.tmp/ue-readonly-dump/EXP-0017-class-layout-reflection.log`. This is a limitation of the current parser object model, not evidence that the runtime classes have no layout metadata elsewhere.

## Reproduction

```powershell
& '.venv/Scripts/python.exe' `
  'tools/analysis/vtable_candidate_scan.py' `
  'Dishonored RHCP/Binaries/Win32/Dishonored.exe' `
  --minimum-pointers 345 `
  --output '.tmp/vtable-candidates.csv'
```

Ghidra checks: `get_xrefs_to(0x00FF5608)`, decompile `0x0057D960` and `0x00585770`, read `0x00FF5B68`, and decompile the containing function at `0x00565680`. The complete scanner output is ignored local data at `.tmp/vtable-candidates.csv`.

The constructor-assignment follow-up is reproduced with:

```powershell
& '.venv/Scripts/python.exe' `
  'tools/analysis/vtable_assignment_scan.py' `
  'Dishonored RHCP/Binaries/Win32/Dishonored.exe' `
  'research/executable/functions.csv' `
  --minimum-function-slots 11 `
  --output '.tmp/vtable-assignment-candidates-baseptr.csv'
```

Candidate validation: `list_names` / `get_address_info(0x0120750C)`, decompile `0x00ED5080`, `0x00ED5090`, `0x00ED82D0`, `0x00ED58C0`, and `0x00ED5AE0`, then compare the `+0x1F0` and `+0x560` raw targets with the wrapper argument behavior.

### Additional target-signature triage

Applied the same direct-assignment candidate list to three more constructor-installed tables whose targets were in the game-code range. The function bodies were re-decompiled through the read-only static MCP:

| Candidate table | Installing functions | `+0x1F0` target | `+0x560` target | Result |
| --- | --- | --- | --- | --- |
| `0x010B4C48` | `FUN_009751F0`, `FUN_0097A8E0` | `FUN_009806B0` reads fields at `this+4/+8`, calls a helper, and writes to `+0x350/+0x354`; it takes no second semantic argument. | `FUN_00983F00` performs cleanup and tests a byte flag. | Rejected for PowerWheel `OnSelectionChanged`; target behavior does not consume the parsed selected-item integer. The `+0x560` target also does not show power selection behavior. |
| `0x011CADD0` | `FUN_00A71E00`, `FUN_00A749D0`, `FUN_00A77C00`, `FUN_00A78460` (plus derived setup paths) | `FUN_00CA2900` takes only `this`, calls slot `+0x64`, checks a returned object's flag, then calls `FUN_00CA2170`. | `FUN_00B53F60` has four explicit arguments after `this` and routes data to `FUN_00573920`. | Rejected: `+0x1F0` does not take the wrapper's integer; `+0x560` has a multi-argument shape incompatible with `Dis_SelectPower`'s one integer. Exact class owner remains unknown. |
| `0x01121478` | `FUN_00AC7010`, `FUN_00ADCFD0` | `FUN_00C73D60` takes only `this`, checks a virtual result and calls initialization helpers. | `FUN_00AE4B80` takes one object pointer and copies two globals into its first fields. | Rejected: neither slot body consumes the wrapper's integer argument. |
| `0x01127D08` | `FUN_00AE65A0`, `FUN_00AF9010` | `FUN_00AF2B40` accepts an adjusted object, another value, and an output buffer; it checks an object flag and writes three output fields. | `FUN_00AE6D00` takes no arguments and returns a static data pointer. | Rejected: the `+0x1F0` function expects more than the single parsed scalar; the `+0x560` function is a zero-argument getter. |

These checks reject the tested owner/slot proposals; they do not prove that no other table in the 1,176-entry candidate set belongs to either game class. The count is a broad scan result, not a finite list of proven vtables.
