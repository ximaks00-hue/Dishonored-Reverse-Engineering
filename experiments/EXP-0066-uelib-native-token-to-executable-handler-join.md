---
id: EXP-0066
title: UELib NativeToken names and executable handler-table candidates
experiment_status: done
claim_status: mixed
build: "10256413"
question: "For nonzero UELib NativeToken values in the function-bearing packages, can the exact-build executable's name-pointer references be joined to adjacent code addresses?"
---

# EXP-0066 — UELib NativeToken names and executable handler-table candidates

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: re-profile the eight packages with standalone `Function` exports, record UELib's `UFunction.NativeToken`, search corresponding native-exec strings in the matching Ghidra project read-only, and compare the raw PE pointer adjacent to each `.data` string-pointer reference with the exact-build function index.
- Exclusions: no game launch/runtime execution, Ghidra database edits, or package modification; this does not cover native functions with token zero, function-like payloads outside the eight packages, all native registrations, token lookup/dispatch code, or runtime reachability; `_excluded_coop_project/` was not accessed.
- Tools: Eliot.UELib 1.13.3; [uelib-function-census](../tools/uelib-function-census/); Ghidra 12.1.2 `analyzeHeadless -noanalysis -readOnly`; [ExportNativeTokenStringRefs.java](../research/executable/scripts/ExportNativeTokenStringRefs.java); [native_token_dispatch_catalog.py](../tools/native_token_dispatch_catalog.py); Python 3 and `pefile`.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the local executable SHA-256 for build 10256413.
2. Re-ran the UELib function census for the eight packages in EXP-0057. Extended the JSONL output with the parsed `NativeToken` and operator-precedence properties; compared each package input hash with the full-install manifest.
3. Selected exported UFunctions where UELib reports `nativeFlag=true` and `NativeToken != 0`. Parsed the emitted `// Export <class>::exec<name>` identifier. The executable's registration strings use `AActor`, `AController`, and `APlayerController` prefixes where UELib prints `UActor`, `UController`, and `UPlayerController`; the reproducer records this spelling normalization explicitly.
4. Ran the Ghidra script on the existing exact-build project using `-noanalysis -readOnly`. It searched each exact registration string, collected data references to every occurrence, and wrote their addresses to a temporary CSV.
5. At each Ghidra source site, mapped the RVA through the raw PE sections, read the DWORD at that slot and the adjacent DWORD at `site+4`, checked the source section and target section, and matched target VAs to `research/executable/functions.csv`.
6. Wrote the per-reference result to [native-token-dispatch-catalog.csv](../research/executable/evidence/native-token-dispatch-catalog.csv). Reproduce the catalog from the repo root (the JSONL directory is a local ignored output from procedure step 2):

Reproduce the UELib source JSONL for the eight packages:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-function-census --no-restore -- `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-root assets\extracted\uelib-census `
  --emit-decompiled-jsonl `
  --json-output assets\extracted\uelib-census\native-token-reprobe.json `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\Core.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\Engine.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\GFxUI.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\GameFramework.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\IpDrv.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\OnlineSubsystemPC.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\OnlineSubsystemSteamworks.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\DishonoredGame.upk'
```

The helper prints a new JSON `runDirectory`; pass that directory as `--jsonl-root` in the next command.

```powershell
python tools/native_token_dispatch_catalog.py `
  --jsonl-root assets/extracted/uelib-census/<run-directory> `
  --package-manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --game-root "Dishonored RHCP" `
  --executable "Dishonored RHCP/Binaries/Win32/Dishonored.exe" `
  --function-index research/executable/functions.csv `
  --analyze-headless "E:/Dev/Tools/ghidra_12.1.2_PUBLIC/support/analyzeHeadless.bat" `
  --ghidra-project research/executable/ghidra-project `
  --output research/executable/evidence/native-token-dispatch-catalog.csv
```

The UELib JSONL source hashes are checked against the package manifest. The helper verifies the exact executable hash before the Ghidra query and preserves the read-only/no-analysis mode.

## Observations

- The eight-package JSONL corpus contains 4,772 exported UFunctions, of which 2,572 carry UELib's Native flag (EXP-0057). UELib reports 189 distinct nonzero `NativeToken` values: 156 in `Core.upk` and 33 in `Engine.upk`; the other six function-bearing packages contribute none in this subset. Each of the 189 values is unique in this corpus and matches the number in its decompiled `native(N)` declaration.
- Ghidra found 207 data-reference rows for those 189 definition records, covering 201 distinct `.data` source sites. Eleven function records have multiple string-reference rows, accounting for 18 extra rows.
- For all 207 rows, the raw DWORD at the Ghidra reference site equals the matched string VA; the site is in `.data`, and the adjacent `site+4` DWORD points into `.text`.
- 190/207 adjacent targets exactly match an entry in the 72,437-row Ghidra function index. The other 17 still point into `.text` but do not match any indexed function start. The catalog retains those as unresolved targets.
- Example: UELib reports `Not_PreBool` as `native(129)` in `Core.upk`. The matching string is referenced from `.data` at `0x01269F48`; the adjacent DWORD is `0x00405F90`, an indexed Ghidra function entry (`FUN_00405f90`). `Sleep` (`native(256)`) maps through the corresponding `AActorexecSleep` string to `0x005BE620`; `LineOfSightTo` (`native(514)`) maps to `0x005CA4A0`.
- Static decompilation of sample handlers at `0x00405F90`, `0x005BE620`, and `0x005CA4A0` shows code reading an `FFrame`-like argument and advancing the bytecode pointer. This is consistent with the handler interpretation; pseudocode remains decompiler output, not original source.

## Interpretation / claims

- **Observed:** within this exact-build subset, every nonzero UELib `NativeToken` value corresponds to the number in a `native(N)` declaration, and every searched export name has at least one Ghidra data xref.
- **Confirmed static pointer relation:** all 207 catalog rows have a raw `.data` DWORD equal to the referenced native-exec string VA, followed at `+4` by an address in the executable `.text` section. In 190 cases the adjacent address is an exact function start in the Ghidra index.
- **Inferred:** the paired name/code-pointer records are native-exec registration entries, and the shared function name permits a candidate `NativeToken` → executable handler join. Multiple entries for some names and unindexed targets prevent treating this as a total one-to-one mapping.
- **Observed follow-up (EXP-0067):** exact-build function `FUN_006067A0` passes class-name keys and pointers to `.data` exec-table starts to `FUN_0044C310` for a large base-class set. This identifies a static class-table handoff path for the referenced tables, but does not establish what `FUN_0044C310` stores or how execution later reads the records.
- **Unknown:** how the bytecode token selects a table entry, whether all 189 candidate handlers are invoked in gameplay, and which functions correspond to the 17 `.text` targets absent from the function index.
- **Not established:** complete mapping of the 2,572 Native-flagged exported functions, complete mapping for the wider executable, or runtime semantics of all handlers.

## Reproduction and limitations

- The checked-in CSV retains one row per Ghidra string-reference occurrence. It records source package path/hash, UELib token/name, executable string VA, `.data` site, raw-pointer check, adjacent target VA/section, function-index match, and reference type.
- The PCK/package outputs and UELib JSONL corpus remain under ignored `assets/extracted/`; no game payload is included in the catalog.
- Name spelling aliases are based on the selected UELib export comments and matching executable strings. A row is a static address relation; it is not proof of runtime table consumption.
- A target in `.text` without an exact index entry may be code that Ghidra did not identify as a function, a thunk/entry variant, or another address form. These remain unresolved rather than being promoted to functions.
- `nativeFlag=true` with `NativeToken=0` occurs for 2,383 exported functions in this eight-package corpus. They are outside this token-specific join and must not be interpreted as missing or non-native implementations.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Function output census: [EXP-0057](EXP-0057-engine-upk-function-decompile-census.md)
- Function-label distribution: [EXP-0056](EXP-0056-standalone-function-export-distribution.md)
- Per-reference catalog: [native-token-dispatch-catalog.csv](../research/executable/evidence/native-token-dispatch-catalog.csv)
- UELib helper: [Program.cs](../tools/uelib-function-census/Program.cs)
- Catalog helper: [native_token_dispatch_catalog.py](../tools/native_token_dispatch_catalog.py)
- Ghidra query: [ExportNativeTokenStringRefs.java](../research/executable/scripts/ExportNativeTokenStringRefs.java)
- Consumer follow-up: [EXP-0067](EXP-0067-native-exec-class-table-handoff.md)
- Completion scope: [roadmap](../docs/roadmap.md)
