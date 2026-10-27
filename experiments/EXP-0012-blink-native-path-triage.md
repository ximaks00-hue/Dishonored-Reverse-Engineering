---
id: EXP-0012
title: "Static Blink native-path triage"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What Blink-related native leads exist before full EXE analysis, and what are the Ghidra binding caveats?"
---
# EXP-0012 — Static Blink native-path triage

- Status: partial; no Blink native implementation has been identified.
- Build target: `Dishonored.exe`, expected local copy `Dishonored RHCP/Binaries/Win32/Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Package: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, parsed as described in EXP-0009.
- All inspection tools used were read-only. No game executable/package file was modified; `_excluded_coop_project/` was not accessed.

## Question

Can the exact-build executable's static function/string indexes directly identify the native registration or execution routine for `DishonoredActivePowerComponent_Blink`?

## Procedure and observations

1. Queried `ue_explorer.search_objects` for `DishonoredActivePowerComponent_Blink` and `PowerBlink` in the compressed package.
2. Queried `ue_explorer.decompile_object` for the Blink class, its `PowerBlink` member, `DisTweaks_Blink`, and `PowerAttributes_Blink`.
3. Queried the saved 72,437-function index with `Blink`, `ActivePower`, `PowerComponent`, `Teleport`, `DisTweaks_Blink`, `m_fDefaultBlinkStepDistance`, and `PowerAttributes_Blink`.
4. Queried Ghidra names/strings in the currently open database `dishonored_blink`.

### Confirmed

- UModel's object listing places class `DishonoredActivePowerComponent_Blink` at export-list position 6411 and three `PowerBlink` member entries at 18320, 28549, and 29598. These are package listing positions/offsets, not executable addresses.
- `decompile_object` still rejects all queried objects because the original package has compressed object tables; this MCP call does not automatically apply the separately built decompressor from EXP-0009.
- The saved function index returned zero matches for all tested Blink-related text queries. This is a symbol/name-search result only.
- The Ghidra server database named `dishonored_blink` identifies its input path as `/E:/SteamLibrary/steamapps/common/Dishonored RHCP/Binaries/Win32/Dishonored.exe`, with 176 functions, six segments, and 433 entry points. This differs from the local target path recorded above; the open database is not established as the workspace copy.
- In that open database, literal `Blink` strings and names were not found. A broad string query found `SymFunctionTableAccess64`, `CallNtPowerInformation`, Steam imports, and common DLL strings, but no relevant Blink identifier. This cannot exclude unnamed native code.
- The open database's current function list contains six 1-byte delayed PhysX loader stubs. It is not a useful analyzed function index for the game executable.

### Inference and limitations

- A class flagged `native(Power)` makes a native implementation path plausible (EXP-0009), but the string/name searches here do not establish which function or registration record implements it.
- The saved index can decompile a few functions by address but does not expose instruction cross-references or a usable arbitrary-address query. A targeted `FUN_009f4090` decompilation showed a bytecode/native-dispatch-style indirect call and virtual call, but its role is not attributed to Blink; it is not evidence of Blink implementation.
- The `dishonored_blink` Ghidra database is bound to a different path and is under-analyzed. Until a full analysis is run against the exact workspace executable and its function boundaries/call references are usable, zero name matches do not imply no implementation exists.
- No `native(Power)` native-index value, registration table, class vtable mapping, or Blink call site has been extracted yet. The implementation remains unknown.

## Next discriminating step

Run or open a full read-only Ghidra analysis for the exact workspace `Dishonored.exe`, then inspect UnrealScript VM/native registration dispatch tables and string/class-name references using the decompressed UPK metadata. Treat addresses as RVAs only after confirming the PE image base and database mapping. Do not attribute generic script VM functions to Blink without a specific class/native index or call-path correlation.

## Related records

- UPK class/defaults and native boundary: [EXP-0009](EXP-0009-blink-decompression-and-uelib.md)
- Compressed-package parser limitation: [EXP-0007](EXP-0007-ue-explorer-mcp.md)
- Package index/coverage: [EXP-0011](EXP-0011-cookedpcconsole-inventory.md)
