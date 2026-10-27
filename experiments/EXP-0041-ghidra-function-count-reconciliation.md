---
id: EXP-0041
title: Ghidra function count and index reconciliation
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "Does the 488-row difference between the Ghidra function count and functions.csv consist exactly of external functions?"
---

# EXP-0041 — Ghidra function-count reconciliation

- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`; SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matches the build record.
- Ghidra project/program: `Dishonored-RHCP-10256413` / `Dishonored.exe`, x86, image base `0x00400000`.
- Method: `ExportFunctionCountAudit.java` run using headless Ghidra `-noanalysis -readOnly`; exported function addresses were compared against `research/executable/functions.csv` by address.
- Scope: resolve the function-count discrepancy previously left open in EXP-0022/REV-0004. No game files or Ghidra program state were changed; `_excluded_coop_project/` was not accessed.

## Procedure

1. Ran the audit script against the existing workspace Ghidra project with `-noanalysis -readOnly`.
2. Exported unique function entry addresses and external flags to ignored `.tmp/EXP-0041-ghidra-functions.csv`.
3. Compared that address set and its internal subset with `research/executable/functions.csv`.

## Observations

- `FunctionManager.getFunctionCount()` returned `72,925`.
- The union of `getFunctions(true)` and `getExternalFunctions()` contained exactly `72,925` unique entry addresses: `72,437` internal and `488` external.
- `research/executable/functions.csv` contains `72,437` addresses. Every CSV address is in the Ghidra internal set; there were zero CSV-only addresses and zero missing internal addresses.
- The remaining `488` Ghidra addresses are exactly those marked external. Thus `72,437 + 488 = 72,925`.
- The workspace EXE SHA-256 matches BUILD-STEAM-10256413.

## Interpretation / claims

- **Confirmed:** the prior 488-function discrepancy is entirely due to enumeration scope: the CSV covers internal functions, while `getFunctionCount()` includes 488 external functions.
- **Confirmed:** the address sets match exactly for all 72,437 internal functions; the difference does not indicate a changed binary or missing internal-function export.
- **Supersedes:** EXP-0022's strong hypothesis that the 488-count delta was caused by external functions. That explanation is now directly measured.
- **Unchanged:** this reconciliation does not validate the semantic coverage of any particular decompilation or vtable scan; it only resolves function inventory identity/counting.

## Reproduction and limitations

- Run `ExportFunctionCountAudit.java` with the workspace project/program, headless `-noanalysis -readOnly`, then compare its exported internal addresses against `research/executable/functions.csv`.
- The generated CSV is ignored/transient. The script enumerates entries and writes only the requested output; it does not edit the Ghidra program.

## Result

The count discrepancy is closed. Continue the Blink and controller call-path investigations independently of this resolved inventory issue.
