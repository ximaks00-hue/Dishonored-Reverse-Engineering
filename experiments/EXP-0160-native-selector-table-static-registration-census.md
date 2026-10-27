---
id: EXP-0160
title: Static initialization and NativeToken entries for the executable selector table
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What initialization, static registration calls, and indexed consumers can be established for executable table 0x014068F0, and do token/target pairs match UELib NativeToken records?"
---

# EXP-0160 — Static initialization and NativeToken entries for the executable selector table

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: exact-build raw-x86 initialization and writes for table `0x014068F0`; direct indexed-function consumers; direct calls to `FUN_00426C60`; exact token/target comparison with the UELib-derived EXP-0066 catalog.
- Exclusions: no game launch or process attach, no proof that static registration wrappers execute, no runtime table snapshot, no complete mapping of the 156 Core `NativeToken` values, and no proof of gameplay dispatch or reachability.
- Tools: Python 3.12.10, `pefile` 2024.8.26, Capstone 5.0.7, [scan_native_selector_table.py](../tools/scan_native_selector_table.py), [disassemble_va.py](../tools/disassemble_va.py), and the EXP-0066 [native-token dispatch catalog](../research/executable/evidence/native-token-dispatch-catalog.csv).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the configured executable hash against build `10256413`.
2. Disassemble `FUN_00426C60` from the raw executable. Trace its guarded table fill, non-sentinel path, index checks, pointer load, and indexed write.
3. Run `tools/scan_native_selector_table.py`. The script verifies the EXE SHA-256, decodes all function bodies listed in `research/executable/functions.csv`, counts explicit table operands, records direct calls to the initializer and their two immediate stack arguments, reads the target pointer cells, joins token/target pairs to the EXP-0066 catalog, and writes the CSV plus provenance JSON.
4. Independently compare the set of non-sentinel token values in the resulting CSV with distinct nonzero UELib `NativeToken` values from `Engine.upk` in EXP-0066.
5. Recheck representative raw registration stubs for tokens `0x0100`, `0x0105`, and `0x0106`; do not infer execution from their presence or from their `.rdata` references.

## Observations

- The executable hash matches the build record. PE metadata places `0x014068F0` at offset `0x19D8F0` within virtual `.data` starting at `0x01269000`; `.data` has `SizeOfRawData=0x14D000` and virtual size `0x21B3BC`. The table address is inside the virtual range but beyond file-backed `.data` bytes.
- Raw x86 for `FUN_00426C60` checks initialization flag `0x0143B910`. If clear, it sets `EDI=0x014068F0`, `EAX=0x00425E60`, `ECX=0x1000`, executes `REP STOSD`, then sets the flag. This initializes 4,096 DWORD entries, indices `0` through `0xFFF`, to pointer `0x00425E60` on that code path.
- When the first argument is `0xFFFFFFFF`, `FUN_00426C60` skips the token-specific write. For other values, raw x86 records the index at `0x0141B348` if the signed value is negative, the value is greater than `0x1000`, or the indexed table slot differs from `0x00425E60`; it then loads the DWORD at the second argument and writes it to `0x014068F0 + index*4`. The check does not branch around that write. The `0x1000` boundary is allowed by the comparison although the fill loop initializes only indices `0..0xFFF`; no registration in the census uses `0x1000`.
- The reproducible function-body scan covers 72,437 indexed functions. It finds 3,276 explicit memory operands based at `0x014068F0` across 1,595 functions: 3,274 `MOV` reads, one `CMP` read, and one indexed `MOV` write. The helper's `REP STOSD` fill uses a register base and is separate from this explicit-operand count.
- The scan finds 1,082 indexed functions with direct calls to `FUN_00426C60`. Their second immediate arguments point to 1,082 distinct, contiguous four-byte cells from `0x0128C2D4` through `0x0128D3B8`. Of these calls, 1,049 pass token `0xFFFFFFFF` and 33 pass non-sentinel values; all 33 non-sentinel tokens are distinct.
- The 33 non-sentinel pointer cells contain `.text` addresses that exactly match indexed function starts. Each token/target pair has exactly one matching row in the EXP-0066 UELib catalog. The 33 registered tokens equal the complete set of 33 distinct nonzero `NativeToken` values recorded for `Engine.upk` in that catalog; no token is missing from this static comparison.
- Examples: the wrapper at `0x00F74EE0` passes token `0x0100` and pointer cell `0x0128C574`, whose DWORD is handler `0x005BE620` (`Sleep`); `0x00F74EC0` passes `0x0105` with cell `0x0128C570` and target `0x005BE680` (`FinishAnim`); `0x00F74EA0` passes `0x0106` with cell `0x0128C56C` and target `0x006CC210` (`SetCollision`). These token and target pairs also match EXP-0066 by exact token and adjacent target address.
- The generated [registration census](../research/executable/evidence/native-selector-table-registration-census.csv) contains the 33 non-sentinel rows. Its [provenance manifest](../research/executable/evidence/native-selector-table-registration-census.json) records the build hash, input hashes, tool versions, counts, output hash, and limits.

## Interpretation and claim limits

- **Confirmed static initialization path:** a guarded code path fills 4,096 table slots with `0x00425E60`.
- **Confirmed static registration dataflow:** for a non-sentinel first argument, `FUN_00426C60` loads a function pointer through its second argument and writes that pointer into the table slot selected by the first argument. The check records some suspicious or occupied indices but does not prevent the indexed write.
- **Confirmed static token/target correspondence:** 33 direct callers provide 33 distinct non-sentinel tokens and pointer cells. Every resulting token/target pair exactly matches an EXP-0066 UELib `Engine.upk` record, and this set equals all 33 distinct nonzero Engine tokens in that catalog.
- **Inferred subsystem meaning:** the shared table is consistent with a native-function token dispatch table. This interpretation is supported by the token values, exact handler targets, and thousands of indexed function reads; execution of the wrappers and runtime dispatch are not established here.
- **Unknown:** whether and when the indexed registration wrappers execute; runtime table contents; whether the sentinel wrappers have a later dynamic path; static registration for the 156 Core token values; the meaning of `0x0141B348`; consequences of occupied/out-of-range indices; and whether any target is invoked in a particular gameplay condition.
- **Limit:** the census recognizes explicit table operands and direct calls inside indexed function bodies. It does not enumerate accesses through computed base pointers or indirect helper calls, and the UELib comparison is bounded to the EXP-0066 package/catalog subset.

## Reproduction

From the repository root, with the registered build installed at the configured path:

```powershell
python tools\scan_native_selector_table.py
python tools\disassemble_va.py --start 0x00426C60 --end 0x00426CBD
python tools\disassemble_va.py --start 0x00F74EE0 --end 0x00F74EF8
python tools\disassemble_va.py --start 0x00F74EC0 --end 0x00F74ED8
python tools\disassemble_va.py --start 0x00F74EA0 --end 0x00F74EB8
```

The scanner regenerates the registration CSV and provenance JSON. Its function-reference denominator is the checked-in exact-build `functions.csv`; computed-address and indirect references may not appear as explicit table operands.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior UELib token/name/target candidates: [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md)
- Class-table handoff and token-zero boundary: [EXP-0067](EXP-0067-native-exec-class-table-handoff.md)
- Selector consumer and unresolved field owner: [EXP-0159](EXP-0159-native-class-table-static-consumer-lookup.md)
- Generic indexed reader candidate: [EXP-0046](EXP-0046-blink-tick-dispatch-search.md)
- Script: [scan_native_selector_table.py](../tools/scan_native_selector_table.py)
