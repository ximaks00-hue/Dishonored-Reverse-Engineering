---
id: EXP-0019
title: PowerWheel Scaleform selection bridge
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "How does PowerWheel Scaleform selection reach native OnSelectionChanged, and does it activate Blink?"
---
# EXP-0019 — PowerWheel Scaleform selection bridge

- Status: PowerWheel ActionScript selection value and native callback boundary confirmed; callback target and Blink activation path unresolved.
- Date: 2026-10-26.
- Build: Steam app 217980, build 10256413, x86.
- Package: `DishonoredGame/CookedPCConsole/UI_PowerWheel_SF.upk`, manifest SHA-256 `C2CA9A892D029108FE895992AEFEBAE66195873414CBA8B509A35D6510191A4F`.
- Extracted object: `SwfMovie powerwheel`, exported from the package as `powerwheel.gfx`; SHA-256 `7D829A0DB1732D5941BAFEA61143DE9B4FC493D3EB872A9998BAA31747B3F0AA`.
- Tools: workspace UModel build at `.tmp/UEViewer-source/umodel.exe` (SHA-256 `13502E5A4D8F6B5F32252AFEBD6360F7302CCFACCF6B8DDA65BEFF0BE2D364A0`); JPEXS FFDec 26.4.0 (`ffdec.jar` SHA-256 `80F8CED0BFDE98B434C28E9807E91FE5558255B2F712051A0E65221519BD392A`, release ZIP SHA-256 `56CE960AEAFC7CAF034E2052BA49F878A883F7C7CA690DA6EEFFCA9587B5E4B9`).
- Extracted source hashes: `WheelItems.as` SHA-256 `9C9BAF55878ADDAD5248634B69B4369B872ED16F0876738122135235BBCB9B94`; `WheelHandler.as` SHA-256 `71FD8A197791E92248A709BAE27DDB99406E39CF8AB49B1DE5350C1E7D30B0F2`.
- Shortcut source hashes: `ShortcutsHandler.as` SHA-256 `013C6D22AB6B6C63D1190AE56C61757394A89FA52A6FC2F7C2F4CFC416D78BBD`; `PC_ShortcutsHandler.as` SHA-256 `5D9257E06EC9674FE9A5244603302F6BF65732A2251B05DC77A2D4E3EC8F24C2`.
- Scope: read-only extraction and ActionScript inspection of the workspace package. Outputs are under ignored `assets/extracted/ui_powerwheel/` and `.tmp/ffdec-26.4.0/`. No installed game file or Ghidra program was modified; `_excluded_coop_project/` was not accessed.

## Procedure

1. Checked the package manifest entry and inspected `UI_PowerWheel_SF.upk` with the configured `ue_explorer`. Its summary reports UE package version 801/30, engine 9098, 59 exports, and a `SwfMovie powerwheel` export.
2. The `dishonored_assets.export_package` MCP call returned a generic tool error. Used the locally built UModel CLI against the same package and exported only `powerwheel` to the workspace extraction directory. The resulting GFX file has a Scaleform GFX header (`47 46 58 0A`).
3. Installed JPEXS FFDec 26.4.0 to ignored `.tmp/` from its official upstream release, then ran its CLI to export ActionScript. FFDec reported 85 ActionScript files and warned that external SWF requests were ignored; the wheel handler and item-enum scripts are present in the output.
4. Read the exported sources `scripts/__Packages/_powerWheel/WheelItems.as` and `WheelHandler.as`. Their line-level findings are listed below. Independently re-decompiled `0x009F8290` through the read-only `dishonored_static` MCP; the pseudocode reads one argument into a local and calls `(**(code **)(*param_1 + 0x1f0))(local_8)`, confirming receiver slot `+0x1F0` without modifying or saving the Ghidra project.
5. Re-decompiled native registration routine `FUN_00A0DBF0`, which registers class name `DisGFxMoviePlayerPowerWheel` with native-entry table pointer `0x012E4728`. The routine then calls `FUN_00BBD3A0`, but follow-up inspection in EXP-0020 established that this lazy initializer belongs to `DisGFxMoviePlayerStore`, based on its descriptor name. The call's adjacency to PowerWheel registration does not identify it as PowerWheel initialization. Read the original executable bytes at the exec table address. At `+0x18`, the record is string pointer `0x010C85B0` (`UDisGFxMoviePlayerPowerWheelexecOnSelectionChanged`) followed by function pointer `0x009F8290`. This independently corroborates the wrapper/class registration association recorded in EXP-0014.
6. Read the full PowerWheel exec table from the EXE. Its four name/function pairs are `OnClosed → 0x009F82F0`, `ConsumeManaPotion → 0x009F8250`, `ConsumeHealthPotion → 0x009F73A0`, and `OnSelectionChanged → 0x009F8290`, followed by a null terminator. Search of all 85 exported ActionScript files finds no `onUse`, `UsePower`, or `SelectPower` token. In `ShortcutsHandler.as`, shortcut records retain `itemIndex` values; in `PC_ShortcutsHandler.as`, `DockBarPressed` calls `_root.AssignShortcut(slot)` while mouse-wheel handlers call `_root.SetShortcutSelection(slot)`. These are slot/assignment UI operations and do not establish ability activation.
7. Read the controller exec table at `0x012E51B8`, also registered by `FUN_00A0DBF0` under `DishonoredPlayerController`. It contains 47 native-entry pairs before its null terminator. The targeted entries are `OnShowPowerMenu → 0x009EEC40`, `Dis_SelectPower → 0x009EE630`, keyboard `Use/Select → 0x009EDE90/0x009EDE30`, gamepad `Use/Select → 0x009EDDD0/0x009EDD70`, mouse next/previous → `0x009F4100/0x009EDEF0`, wheel close/open → `0x009EDD00/0x009EDC90`, and `OnTeleport_Native → 0x009EDC30`. The previously recorded wrapper decompilations map these to receiver slots: `Dis_SelectPower +0x560`; keyboard `Use/Select +0x510/+0x50C`; gamepad `Use/Select +0x508/+0x504`; mouse next/previous `+0x518/+0x514`; wheel close/open `+0x500/+0x4FC`; `OnTeleport_Native +0x4F8`. This establishes separate native entry points on the controller class, not calls among them.
8. Re-decompiled `FUN_009EE630`, `FUN_009EDE90`, `FUN_009EDE30`, `FUN_009EDDD0`, and `FUN_009EDD70` through `dishonored_static` in read-only mode. Each parses one DWORD argument and dispatches it to the offsets listed above. This rechecks that `Dis_SelectPower` and all four shortcut `Use`/`Select` wrappers accept the same scalar shape, while leaving their semantic interpretation and method targets unknown.

## Findings

- `WheelItems.as` defines `blink = 24` (line 16). This is the wheel item's semantic `itemIndex`, not its position in the visual content array.
- `WheelHandler.setItemFocus(idx, isPower)` assigns `_selItemIdxEnum` from `powersContent[idx].itemIndex` when the focused item is a power (line 520), and calls `flash.external.ExternalInterface.call("onSelectionChanged", this._selItemIdxEnum)` (line 534). Therefore a focused Blink power sends the integer 24 through the Scaleform external callback interface.
- Clearing a selection has a separate `onSelectionChanged(0)` call (`WheelHandler.as`, line 486). The callback argument is thus also used for the cleared/no-selection case; do not interpret zero as a Blink index.
- The exact-build native exec table maps `UDisGFxMoviePlayerPowerWheelexecOnSelectionChanged` to wrapper `FUN_009F8290`. The wrapper parses one integer and dispatches it through receiver slot `+0x1F0`. The ActionScript external callback name and argument shape strongly correlate with this registered native method; the name resolution was not dynamically traced, so classify the UI-to-wrapper edge as a strong static inference rather than an observed runtime call.
- The exact-build class-registration routine `FUN_00A0DBF0` associates the native entry table at `0x012E4728` with `DisGFxMoviePlayerPowerWheel`. The table's `+0x18` pair directly stores the `OnSelectionChanged` exec name and wrapper address. This corroborates the class-specific native boundary. EXP-0021 subsequently resolves the separate C++ instance vtable and its `+0x1F0` target.
- The same native exec table contains four registered callbacks—`OnClosed`, `ConsumeManaPotion`, `ConsumeHealthPotion`, and `OnSelectionChanged`—then terminates. No power-use/activation callback appears in this class's exec table. The extracted PC shortcut script forwards slot operations such as assignment/visual selection, but does not call an activation function. This narrows the next search toward the PlayerController shortcut `Use`/`Select` handlers or the unresolved native callback targets; it does not exclude native calls initiated outside the ActionScript source.
- The controller has a separate native exec-registration table containing `Dis_SelectPower`, keyboard/gamepad shortcut `Use` and `Select`, wheel open/close, and teleport callback entry points. Their wrappers and receiver slots remain separate interfaces; table proximity or common ownership does not establish a call edge or an argument conversion.
- A repository-wide text search of the 85 exported ActionScript files for `Dis_SelectPower` / `SelectPower` returned no matches. This is bounded negative evidence about the exported UI scripts only; native code may dispatch indirectly or through another callback.

## Evidence classification

**Confirmed:** the exported wheel script assigns Blink item value 24 and passes the focused power's `itemIndex` to a Scaleform external callback named `onSelectionChanged`; the exact-build PowerWheel registration table contains a case-matching `OnSelectionChanged` native exec entry pointing to `FUN_009F8290`; that wrapper parses an integer and calls receiver slot `+0x1F0`. The controller's separate registration table contains the selection/use wrappers and `Dis_SelectPower`. PC shortcut script paths shown here pass shortcut slot indices to UI operations, not item IDs to an activation routine.

**Strong static inference:** the Scaleform callback resolves to the registered `DisGFxMoviePlayerPowerWheel.OnSelectionChanged` native exec based on class-specific registration, case-matching name, and argument shape. No runtime call trace confirms the resolution.

**Hypothesis to test:** the controller shortcut handlers receive a slot index, read a shortcut record containing a wheel `itemIndex`, and convert that item ID into the active-power/UI selection identifier before selecting or using the ability. The package-side shortcut data model and the native wrapper signatures make this a useful trace target; no code currently proves any of those conversions or calls.

**Not established:** runtime resolution of the Scaleform callback; the concrete target at PowerWheel slot `+0x1F0`; any call from that target to `DishonoredPlayerController.Dis_SelectPower`; conversion between wheel item value 24, UI selection enum value 2, and Blink's active-array index 0; meaning of the native shortcut `Use`/`Select` indices; ability activation; or any teleport/position change. The UI tutorial package `UI_Tuto_Blink_SF.upk` was found to contain texture exports, not an identified ActionScript bridge, and was not used as evidence for runtime behavior.

## Reproduction

From the workspace root, the extraction command used was:

```powershell
.tmp/UEViewer-source/umodel.exe -export -3rdparty -game=dis -path="Dishonored RHCP/DishonoredGame/CookedPCConsole" -out="assets/extracted/ui_powerwheel" UI_PowerWheel_SF.upk powerwheel
```

ActionScript was exported with FFDec 26.4.0:

```powershell
java -jar .tmp/ffdec-26.4.0/ffdec.jar -cli -format script:as -export script .tmp/ffdec-26.4.0/powerwheel-scripts assets/extracted/ui_powerwheel/UI_PowerWheel_SF/SwfMovie/powerwheel.gfx
```

The original package and binary hashes are from the workspace package manifest; the extracted GFX and ActionScript source hashes are provided above so derived artifacts can be checked independently. The native address/table assertions are backed by the read-only Ghidra pseudocode for `FUN_00A0DBF0` and `FUN_009F8290` and the corresponding raw EXE bytes.

## Next step

Resolve the actual method-table owner and target at PowerWheel receiver offset `+0x1F0`, then trace its integer argument into controller selection state or `Dis_SelectPower`. Keep `24`, UI enum `2`, and active-array index `0` separate until a concrete native dataflow joins them.
