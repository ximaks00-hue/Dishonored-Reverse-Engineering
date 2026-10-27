---
id: EXP-0013
title: "Full Ghidra pass and Blink native-name correlation"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does full Ghidra analysis of the workspace EXE complete, and what Blink name/native-table correlations appear?"
---
# EXP-0013 — Full Ghidra pass and Blink native-name correlation

- Status: full auto-analysis completed; Blink correlation is partial and native movement implementation remains unidentified.
- Binary: `Dishonored RHCP/Binaries/Win32/Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (Steam build 10256413).
- Package: decompressed copy `assets/extracted/dishonored-blink/DishonoredGame.upk`, derived from the original package as documented in [EXP-0009](EXP-0009-blink-decompression-and-uelib.md).
- Scope: read-only inspection of the executable and decompressed package. No game EXE or UPK was written. `_excluded_coop_project/` was not accessed.

## Ghidra database and binary identity

1. Opened the workspace EXE path with Ghidra MCP `run_auto_analysis=true` in database `dishonored_exact_full`.
2. Waited for analysis. The first two five-minute MCP waits timed out; a subsequent database listing showed analysis complete.
3. The database listing reports the exact workspace path and 72,925 functions. `get_database_info` reports an older, unavailable `E:/SteamLibrary/.../Dishonored.exe` source path. This is a Ghidra MCP metadata inconsistency; `open_database` and `list_databases` identify the requested workspace file. A raw-byte check further corroborated the loaded image: Ghidra VA `0x401000` matched the first 32 raw `.text` bytes at file offset `0x400` in the workspace EXE. The workspace file hash matches the recorded build.
4. Ghidra reported PE image base `0x400000`, x86 little-endian, 7 memory blocks, and 72,925 functions after analysis. The `.text` block is `0x401000–0xF935FF`, `.rdata` `0xF94000–0x12681FF`, and `.data` `0x1269000–0x14843BB`.
5. One analysis bookmark was returned: a bad-instruction/conflicting-flow warning at `0x6D0064/0x6D0069`. This did not prevent the completed analysis or the relevant queries below.
6. `save_database` was attempted, but Ghidra returned `Unable to lock due to active transaction`; the analysis database remains open in the MCP session. This failure did not affect the executable.

## UPK metadata from the decompressed copy

UELib 1.13.3 initialized the separate decompressed file with `CompressionFlags=0`, 30,049 exports and 652 imports. It decompiled:

- `DishonoredActivePowerComponent_Blink extends DishonoredActivePowerComponent`, marked `native(Power)` and `config(Power)`.
- The base `DishonoredActivePowerComponent` is also marked `native(Power)`.
- The Blink class declares no child UnrealScript function exports. Enumeration found zero direct `Function` exports under both the Blink class and its base class.
- The Blink class contains transient state such as `m_BlinkMode`, `m_bActive`, target/position values, timers and step count, plus `native const Pointer m_pPowerAttributes`.
- The class default object serializes `m_PowerName="Blink"`, `m_fBlinkStepDistance=500`, `m_bSustainedCast=true`, and a reference to `DisTweaks_Blink'Twk_Powers.Blink.Twk_Blink'`. The default block does not serialize a value for `m_fBlinkDistanceMax`.
- `DisTweaks_Blink` is marked `native(Tweaks)` and declares native struct `PowerAttributes_Blink`, held in `m_Levels[2]`. The class default serializes both levels with distance/horizontal/vertical values `2000/1400/400`, default step distance `300`, and step interval `0.01`. See EXP-0009 for the complete defaults and tweak-instance values.
- UELib resolved three Blink component instances in defaults: `Default__DishonoredPlayerPawn.PowerBlink`, `Default__DisDLC06PlayerPawn.PowerBlink`, and `Default__DisDLC07PlayerPawn.PowerBlink`.

These are package declarations/defaults; they do not establish runtime values after initialization or identify the C++ implementation.

## Executable native/exec wrapper table

String/xref search found 27 defined strings matching `exec.*(Blink|Power|Teleport)`. In this search set there is no `UDishonoredActivePowerComponent_Blinkexec...` entry. Two Blink-specific entries are on the cheat manager:

| Name string | `.data` pair address | Wrapper address | Decompiler observation |
| --- | ---: | ---: | --- |
| `UDishonoredCheatManagerexecBlinkShowRangeFull` | `0x12E4838` | `0x009F4090` | Reads one script parameter, then calls a virtual method at vtable offset `+0x514` |
| `UDishonoredCheatManagerexecBlinkShowRange` | `0x12E4840` | `0x009F4020` | Reads one script parameter, then calls a virtual method at vtable offset `+0x510` |

Raw database bytes at `0x12E4838` decode as two little-endian pointers: name string `0x010C8A70` and wrapper `0x009F4090`. The next pair at `0x12E4840` points to name `0x010C8AA0` and wrapper `0x009F4020`. This establishes the observed string/wrapper pair layout for these entries. The wrappers are generated UnrealScript exec adapters; neither decompilation shows Blink movement logic.

Other power-related wrappers include:

| Name string | `.data` pair address | Wrapper address | Decompiler observation |
| --- | ---: | ---: | --- |
| `ADishonoredPlayerPawnexecOnCancelPlayerActivePower` | `0x12E5018` | `0x009EF8A0` | Virtual dispatch at `+0x7E4` |
| `ADishonoredPlayerPawnexecOnAddPower` | `0x12E50D0` | `0x009EF0C0` | Virtual dispatch at `+0x788` |
| `ADishonoredPlayerControllerexecDis_SelectPower` | `0x12E5240` | `0x009EE630` | Virtual dispatch at `+0x560` |

These confirm the executable contains reflection/exec bindings for player power control, but their class names and virtual slots do not identify the Blink component's native methods.

## Blink name use in native code

- Ghidra found strings `BlinkBlender` at `0x010A5830` and `Blink` at `0x010A5840`. The corresponding small code stubs at `0x00F837E2` and `0x00F83802` pass each string and a distinct global destination to helper `0x00454FE0`.
- The analyzed function `FUN_00956660` consumes the resulting two global name pairs through `FUN_00592BE0`. That helper iterates a three-field array, compares the first two fields against the pair, and returns the third field when they match. `FUN_00956660` stores the two lookup results in separate fields of its object.
- A `.rdata` data pointer at `0x010A66B0` points to `FUN_00956660`. This is compatible with a virtual/function table entry, but its owning native class has not been established.
- **Confirmed correlation:** an executable native routine uses the two literal names `BlinkBlender` and `Blink` as keys to retrieve associated objects/components. The UPK separately sets the Blink component's `m_PowerName` to `Blink` and points it at Blink tweak data.
- **Not established:** whether `FUN_00956660` initializes the active-power component, a camera/lens effect, or another owner; whether either lookup result is `DishonoredActivePowerComponent_Blink`; and whether this routine moves the player. No class pointer, call path from the Blink component, or field-offset mapping to its UPK properties has been proved.

## Conclusions

- **Confirmed:** full Ghidra auto-analysis ran on the requested workspace EXE path, whose SHA-256 matches build 10256413; an independent `.text` byte sample matched the file.
- **Confirmed:** the two `BlinkShowRange` bindings are cheat/debug exec wrappers. Power UI/control bindings also exist, but they dispatch to virtual methods on other named classes.
- **Confirmed:** UPK Blink and its base class have zero direct `Function` exports while their classes are marked `native(Power)`; Blink tweak metadata is stored separately under `native(Tweaks)`.
- **Confirmed:** native code contains and uses name keys `BlinkBlender` and `Blink` to look up objects/components.
- **Inference:** the core Blink behavior is implemented through native class/virtual code rather than a Blink-owned UnrealScript `exec` wrapper. This is consistent with the native class declaration and the absence of component-owned functions, but the exact registration, class/vtable owner, and movement routine remain unknown.

## Next discriminating work

1. Identify the native class/table containing the data pointer to `FUN_00956660` and determine the types of its two returned objects.
2. Trace the Blink component's C++ class registration/vtable or locate code that reads its serialized fields (`m_fBlinkDistanceMax`, `m_pPowerAttributes`, step/timing state).
3. Keep `FUN_009F4020/009F4090` and power-control wrappers classified as adapters/debug/UI callbacks unless a specific call path proves otherwise.

## Reproduction references

- Full executable identity/build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Blink declarations/defaults and decompression provenance: [EXP-0009](EXP-0009-blink-decompression-and-uelib.md)
- Previous static triage: [EXP-0012](EXP-0012-blink-native-path-triage.md)
- Ghidra database id in this MCP session: `dishonored_exact_full`
