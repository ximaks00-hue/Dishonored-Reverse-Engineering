---
id: EXP-0040
title: Candidate vtable region ownership audit
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the data region containing FUN_00BFAE60/FUN_00BF8DD0 resolve to a live vtable with an identifiable owner?"
---

# EXP-0040 — Candidate vtable-region ownership audit

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra project: `Dishonored-RHCP-10256413`, x86, image base `0x00400000`; headless processing used `-noanalysis -readOnly`.
- Scope: compare Ghidra symbols/references around pointer-table-shaped data containing functions studied in EXP-0038/0039 with the known Blink vtable.
- Exclusions: no game launch or modification; `_excluded_coop_project/` not accessed.

## Procedure

1. Added `research/executable/scripts/ExportVtableRegionEvidence.java`, which exports each DWORD, any primary symbol, the function at its pointer target, and Ghidra references to the DWORD address.
2. Ran the script read-only over `0x01168380`–`0x01168698`, exporting to ignored `.tmp/EXP-0040-vtable-region.csv`.
3. Compared candidate data addresses with the exact Blink vtable and constructor references already established in EXP-0022/0027.
4. Independently rechecked the workspace EXE SHA-256 against the build record.

## Observations

- At `0x01168698`, Ghidra identifies primary symbol `PTR_FUN_01168698`, whose first DWORD targets `FUN_00BF9A40`. The vtable start has two recognized references, from `0x00BF9A29` and `0x00BF8A39`, both inside constructors that install the Blink vptr (EXP-0022/0027).
- Pointer-shaped entries include `FUN_00BFE3C0` at `0x01168408`, `FUN_00BFAE60` at `0x01168458`, and `FUN_00BF8DD0` at `0x011685EC`.
- Candidate starts `0x011683F8`, `0x01168410`, `0x01168590`, and `0x011685C0` have no primary symbol and no recognized references to their first DWORD addresses in this Ghidra program. A raw image scan likewise found no absolute pointer occurrence of these candidate start addresses.
- The region contains multiple runs of executable-looking DWORD targets and repeated common entries. The target entries alone do not establish which address begins a live vtable or which constructor installs it.
- This strengthens the bounded negative result from EXP-0038/0039: no class owner has been recovered for the data entries containing `FUN_00BFAE60` or `FUN_00BF8DD0`. Computed addressing or runtime table construction is not excluded.

## Interpretation / claims

- **Confirmed:** the known Blink vtable start has a primary symbol and two constructor references in the exact-build Ghidra database.
- **Observed:** candidate region starts listed above have no Ghidra-recognized xrefs to their first DWORD addresses and no primary symbols; the relevant function pointers occur within the data region.
- **Unknown:** whether any candidate sequence is a live vtable, the owner/constructor of the functions `FUN_00BFAE60` and `FUN_00BF8DD0`, and whether their receiver is Blink.
- **Conclusion:** no new receiver-class evidence supports upgrading the EXP-0039 same-instance hypothesis. Keep the shared `+0x60/+0x64/+0x68` field overlap inferred and do not treat address proximity as class ownership.

## Limitations and reproduction

- Ghidra reference absence is bounded to recognized references in this program; it does not rule out calculated addresses, runtime-generated tables, or references missed during initial analysis.
- Reproduce with `ExportVtableRegionEvidence.java` and headless Ghidra `-noanalysis -readOnly`, using the same build/project and region. The CSV output is transient/ignored.
- The script reads memory/symbol/reference APIs and only writes the requested output CSV; it does not mutate the Ghidra program.

## Next action

Prioritize positive provenance: find a constructor or caller that supplies the receiver to `FUN_00BFAE60`, or trace a recognized incoming dispatch to the corresponding method pointer. If none appears, preserve this as an unowned candidate-position routine and continue searching for the event caller of the established UsePower/Blink methods.
