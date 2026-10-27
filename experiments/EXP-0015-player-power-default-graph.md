---
id: EXP-0015
title: "Player pawn Blink default-object graph"
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "How is PowerBlink wired in player-pawn defaults, and where does the native/script boundary stop?"
---
# EXP-0015 — Player pawn Blink default-object graph

- Status: package object links confirmed; selection and movement path unresolved.
- Date: 2026-10-26.
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Package input: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`.
- Decompressed analysis copy: `assets/extracted/dishonored-blink/DishonoredGame.upk`, SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`.
- Parser: Eliot.UELib 1.13.3; 30,049 exports and 652 imports; `CompressionFlags=0`.
- Scope: read-only package object initialization, class/default decompilation, and outer/archetype-path inspection. Output is local-only at `.tmp/ue-readonly-dump/EXP-0015-class-path-recheck.log`. No game files were written; `_excluded_coop_project/` was not accessed.

## Question

What package-side object graph connects the player pawn's Blink power component to active powers, and what evidence links this package data to selection or movement?

## Confirmed package links

1. The class export `DishonoredPlayerPawn` has a default object `DishonoredGame.Default__DishonoredPlayerPawn`. Its emitted defaults include a nested component object with path `DishonoredGame.Default__DishonoredPlayerPawn.PowerBlink` and class `DishonoredActivePowerComponent_Blink`.
2. The same default block assigns that nested object to `m_pBlinkPower` and to `m_ActivePowers[0]`. Subsequent emitted array entries assign other named active-power objects at indices 1 through 5. This confirms package-default object associations and array order for this CDO; it does not establish the integer encoding accepted by `Dis_SelectPower`.
3. The Blink class extends `DishonoredActivePowerComponent` and is declared `native(Power)`. Its emitted declarations include state/movement-related fields (`m_OriginalActorLocation`, `m_OriginalActorVelocity`, `m_TargetingDisplayGroundPoint`, `m_BlinkMode`, `m_fTimeInMode`, among others), but UELib found no direct child `Function` exports for this class. These declarations do not reveal native field offsets or executable control flow.
4. The component class default object at `DishonoredGame.Default__DishonoredActivePowerComponent_Blink` has the class CDO as its archetype. It emits `m_fBlinkStepDistance=500`, `m_fLedgeCheckDistanceScale=1.2`, `m_fImpulseRadius=200`, angle/step parameters, `m_PowerName="Blink"`, `m_eUISelection=eDisUISelectionType_Blink`, `m_bSustainedCast=true`, and a `m_pPowerTweaks` reference to `Twk_Powers.Blink.Twk_Blink`.
5. Separate Blink component template objects exist under `Default__DisDLC06PlayerPawn` and `Default__DisDLC07PlayerPawn`. Their object paths and archetype links show that the DLC07 template inherits its archetype from the DLC06 template, which in turn refers to the base player-pawn `PowerBlink` template. This is an object-template chain only. UELib failed while deserializing these nested component properties at the value `2C_Enable_enable_2 colors_18920`; their complete serialized property values are therefore unknown.
6. `Twk_Powers.Blink.Twk_Blink` serializes `m_UsePowerAction=(m_AnimStates=("CastBlink"),m_bCanMove=true,m_bCanLook=true,m_bAllowSelfInterrupt=true)`. These are property values, not proof of the runtime timing or movement implementation.

## Selection and movement boundary

- In the same package, `DishonoredPlayerController.Dis_SelectPower(int _iPower)` is a native exec declaration with no script body. The exact-build EXE wrapper parses one DWORD and dispatches through receiver slot `+0x560`; its concrete target remains unidentified.
- The package distinguishes Blink's UI enum value `2`, the wheel item enum value `24`, and the default active-power array position `0`. No evidence in this pass connects those values to `_iPower` or to each other.
- Although Blink properties and enum members name movement states and target vectors, this pass did not identify a native consumer, call edge to teleport/relocation, or a position update. The fields are metadata, not a recovered behavior trace.

## Evidence classification

**Confirmed:** object paths, outer/archetype links, emitted default references, class declarations, and serialized property values listed above, within the UELib output scope.

**Unknown:** complete properties of the nested `PowerBlink` CDO due parser failure; in-memory field offsets; meaning of `_iPower`; relationship of the wheel/UI/array indices; native target selection; and Blink activation/teleport semantics.

**Not inferred:** no claim that the `ArkCpntType_Lookat` native type implements Blink movement, and no claim that `OnTeleport_Native` is called by Blink.

## Reproduction

The ignored local dumper source is `.tmp/ue-readonly-dump/Program.cs`; it was built with `dotnet build .tmp/ue-readonly-dump/Dump.csproj --no-restore` and run with:

```powershell
dotnet .tmp/ue-readonly-dump/bin/Debug/net8.0/Dump.dll `
  assets/extracted/dishonored-blink/DishonoredGame.upk `
  *> .tmp/ue-readonly-dump/EXP-0015-class-path-recheck.log
```

The parser reported deserialization errors for nested `ForceFeedbackWaveform.Samples` and the `PowerBlink` component's unrecognized serialized enum/string value; do not treat missing emitted property assignments as defaults.
