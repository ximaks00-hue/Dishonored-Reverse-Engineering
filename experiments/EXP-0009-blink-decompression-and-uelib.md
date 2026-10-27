---
id: EXP-0009
title: Decompress DishonoredGame.upk and inspect Blink scripts/defaults
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "After Gildor decompression, what Blink class/default values does UELib emit?"
---
# EXP-0009 — Decompress DishonoredGame.upk and inspect Blink scripts/defaults

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Input package: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`, 5,928,252 bytes
- Tools: Gildor UEViewer `Tools/PackageUnpack` built from commit `a0bfb468d42be831b126632fd8a0ae6b3614f981`; Eliot.UELib 1.13.3; UModel x86 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.
- Question: Can the compressed package be decompressed to a separate copy that UELib can load, and what Blink defaults/decompiled script are available?

## Procedure

1. Sparse-cloned the official `gildor2/UEViewer` source and checked out the PackageUnpack project at the same commit recorded for the existing UModel build.
2. Generated the x86 NMake project from `Tools/PackageUnpack/decompress.project` using upstream `Tools/genmake` and built with installed Visual Studio 2022 Build Tools 14.44. Optional Oodle library files were absent and not enabled; built-in UE3 LZO/LZX/zlib sources were compiled.
3. Ran the resulting `decompress.exe` against the original `DishonoredGame.upk`, writing only to ignored `assets/extracted/dishonored-blink/DishonoredGame.upk`.
4. Used UModel `-pkginfo` on the decompressed output, then loaded it read-only with Eliot.UELib 1.13.3, called `InitializePackage()`, and decompiled the Blink class/default/tweak objects. UELib stdout diagnostics were captured separately. No game files were written or changed.

## Tool/build artifacts

- Built executable: [`tools/ue-package-decompressor/decompress.exe`](../tools/ue-package-decompressor/decompress.exe)
- Build provenance and command: [`tools/ue-package-decompressor/README.md`](../tools/ue-package-decompressor/README.md)
- Binary SHA-256: `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`
- Decompressed local-only package: `assets/extracted/dishonored-blink/DishonoredGame.upk` (17,320,971 bytes; SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`)
- The decompressed UPK and diagnostic logs are local-only artifacts and are not for Git.

## Observations

### Decompression and parser acceptance

- `decompress.exe` reported input metadata version `801/30`, engine `9411`, 24,432 names, 30,049 exports, 652 imports, game `800033`; output size was 17,320,971 bytes.
- UModel accepted the output and reported the same package version/table counts.
- UELib reported `CompressionFlags: 0`, 30,049 exports, and initialized 30,701 objects (exports plus imports/fake-import objects). This allowed object paths, outer links, defaults, and decompiled class text to be inspected.

### Blink class and default object

UELib identifies export index `6412` as `Class'DishonoredGame.DishonoredActivePowerComponent_Blink'`; its default object is index `6413`, path `DishonoredActivePowerComponent_Blink'DishonoredGame.Default__DishonoredActivePowerComponent_Blink'`.

The decompiled class declaration includes `native(Power)`, `config(Power)`, and enum `EBlinkMode` with `EBM_BlinkWarmup=0`, `EBM_BlinkMove=1`, `EBM_BlinkCooldown=2`, `EBM_BlinkCooldown_FromCancel=3`, and `EBM_MAX=4`. It declares `m_fBlinkDistanceMax` and `m_fBlinkStepDistance` as transient floats, along with timing/state fields and native `m_pPowerAttributes`.

The class default object's decompiled `begin object` block explicitly contains:

- `m_fBlinkStepDistance=500`
- `m_fLedgeCheckDistanceScale=1.2`
- `m_fImpulseRadius=200`
- `m_fMaxAngle_BigStep=30`, `m_fMaxAngle_SmallStep=90`
- `m_fStepLength_Big=200`, `m_fStepLength_Small=50`
- `m_fLensWobbleAmount=1`
- `m_PowerName="Blink"`, Blink UI selection/cancel values, `m_bSustainedCast=true`
- `m_pPowerTweaks=DisTweaks_Blink'Twk_Powers.Blink.Twk_Blink'`

`m_fBlinkDistanceMax` is present in the class property declarations but absent from this object's emitted default-property block. This records absence of an explicit value in this block; no numeric runtime value is inferred.

### Blink tweak/default attributes

- `PowerAttributes_Blink` is nested under `DisTweaks_Blink`. Its struct defaults include `m_Distance=2000`, `m_HorizDistance=1400`, `m_VertDistance=400`, `m_fDefaultBlinkStepDistance=300`, `m_fDefaultTimeBetweenBlinkSteps=0.01`, bend times `0.9` and `2.5`, warmup/cooldown `1.0`, `m_fMoveBlurMaxStrength=1.2`, `m_fMoveReachMaxAtPercentage=0.8`, and other serialized effect values. The full property list is available in the tool output/log.
- `Default__DisTweaks_Blink` serializes two `m_Levels` entries with the same values: distance `2000`, horizontal `1400`, vertical `400`, default step distance `300`, step interval `0.01`, bend-down/up `0.9/2.5`, warmup/cooldown `1.0`, wobble `0.2/0.4`, distortion `0.2/1.0`, blur `1.2`, reach percentage `0.8`, and wobble count `10`.
- The `Twk_Powers.Blink.Twk_Blink` instance serializes level 0 with horizontal/vertical distances `1100/500` and default step distance `100`; level 1 has `1600/500` and step distance `100`, plus move distortion `1.5`, blur `2.5`, and warmup distortion `0.35`. Both entries refer to Blink start/stop/empty sound events. Other omitted fields are not assigned values here.
- **Inferred, not confirmed:** the two `Twk_Blink` entries correspond to progression levels because they are an array named `m_Levels`, contain different range values, and the instance also serializes rune costs `[1, 3]`. Confirm the code path that consumes this array before describing gameplay effects.

### Bytecode/native boundary

- The decompiled Blink class is marked `native(Power)`. No `Function` exports whose direct outer is this class were returned by the UELib object query.
- UModel's complete object listing shows `Function BlinkShowRange` and `Function BlinkShowRangeFull`; UELib resolves them to `DishonoredCheatManager`, not the Blink component, and decompiles both as `native exec function` declarations. They have no UnrealScript body in the package.
- **Interpretation:** this package exposes Blink declarations/default data but no component-owned script function body in the parsed exports. The main implementation is likely in native executable code because of the native class marker; this is an inference and should be confirmed by inspecting the exact-build native function registrations/call paths.

## Limitations

- UELib logged `Couldn't acquire array type` and `PropertyTag value size error` for nested `Engine.ForceFeedbackWaveform.Samples` arrays in the Blink tweak's rumble objects. Those waveform arrays are not reconstructed correctly; the Blink distances/step/timing fields above were emitted without corresponding parser errors.
- UELib-generated source is decompiler output, not original source. Preserve exact paths and parser/version provenance.
- This experiment establishes package-serialized defaults and declarations, not runtime values after config loading, upgrades, or native initialization.

## Reproduction

From the repository root, run:

```powershell
tools\ue-package-decompressor\decompress.exe `
  -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\CookedPCConsole' `
  '-out=E:\Dishonored Reverse Engineering\assets\extracted\dishonored-blink' `
  DishonoredGame.upk
```

Then load the resulting decompressed UPK with UELib 1.13.3, call `InitializePackage()`, and decompile the class/default exports named above. The input remains unchanged; all output belongs under ignored `assets/extracted/`.
