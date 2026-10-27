---
id: EXP-0004
title: UModel package metadata and Blink object triage
experiment_status: done
claim_status: observed
build: "10256413"
question: "What Blink-related class/object names does UModel report in DishonoredGame.upk?"
---
# EXP-0004 — UModel package metadata and Blink object triage

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`
- Tool: UModel x86, 1,026,048 bytes, SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; locally built from the UEViewer upstream revision recorded in the configured environment.
- Question: What package-level object metadata can be established for a first gameplay-system slice?

## Procedure

Run the UModel executable directly (read-only package inspection):

```powershell
& 'E:\Dishonored REVERS\third_party\ueviewer-gildor\umodel.exe' `
  -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\CookedPCConsole' `
  -pkginfo DishonoredGame.upk

& 'E:\Dishonored REVERS\third_party\ueviewer-gildor\umodel.exe' `
  -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\CookedPCConsole' `
  -list DishonoredGame.upk
```

The full outputs were written to temporary files and filtered for the summary and candidate names. No asset export or game/mod execution was performed.

## Observations

UModel reports for the package:

- package version `801/30`;
- engine value `9411` and game value `800033` as printed by this UModel build;
- 24,432 names, 30,049 exports, and 652 imports;
- class statistics include 2,008 `Class`, 981 `Function`, 665 `ScriptStruct`, and 528 `Enum` entries.

The object list includes the following Blink-related entries:

- `Enum EBlinkMode`;
- `ScriptStruct PowerAttributes_Blink`;
- `Class DisTweaks_Blink` and a `Default__DisTweaks_Blink` object;
- `Class DishonoredActivePowerComponent_Blink` and a `Default__DishonoredActivePowerComponent_Blink` object;
- typed objects named `PowerBlink` and `Twk_Blink`.

The list also contains property entries with names including `m_nBlinkStepsTaken`, `m_BlinkMode`, `m_fTimeBetweenBlinks`, `m_fTimeToNextBlink`, `m_fBlinkStepDistance`, `m_fBlinkDistanceMax`, `m_pPowerAttributes`, and `m_Levels`. UModel lists `Function BlinkShowRange` and `Function BlinkShowRangeFull` elsewhere in the package; the list output alone does not establish their owning class or behavior.

## Interpretation and limits

These observations establish that the package contains typed object entries and names consistent with a Blink-related subsystem. They do not establish runtime behavior, parameter values, object ownership/instantiation relationships, state transitions, or which logic runs in native code. UModel's object-list offsets are package locations, not executable RVAs.

## Follow-up

- Find a read-only way to inspect default-object property values and script bytecode.
- Verify object outers/ownership before drawing a dependency graph.
- Compare package-level fields with repeatable in-game observations only after defining a clean runtime baseline.
