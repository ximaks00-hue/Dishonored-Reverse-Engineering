---
id: EXP-0058
title: DLC06 Transversal class declaration and serialized tweak instance
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What declarations and serialized values do the main package and DLC06_DaudBase_Script expose for the Transversal power and tweak objects?"
---

# EXP-0058 — DLC06 Transversal class declaration and serialized tweak instance

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Package identity: main `DishonoredGame.upk` is 5,928,252 bytes, SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`; DLC `DLC06_DaudBase_Script.upk` is 18,674,760 bytes, SHA-256 `62E46C0F78E5C7D2FFC4EBAB6006A557D9B444AD964A7818AA8DBB6AD602D306`, decompressed size 47,423,795 bytes.
- Scope: inspect the DLC06 Transversal active-power class/default objects in decompressed `DishonoredGame.upk` and the named DLC06 tweak instance in decompressed `DLC06_DaudBase_Script.upk` with Eliot.UELib 1.13.3; compare identity against the all-install UModel export catalog.
- Exclusions: package metadata and decompiler-emitted values only; no runtime behavior, config merge, upgrade path, or class-to-tweak consumer is established. No game launch or binary modification; `_excluded_coop_project/` was not accessed.
- Tools: Gildor `decompress.exe` SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE`; Eliot.UELib 1.13.3; UModel export catalog from EXP-0053.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable hash.
2. Query the UModel export catalog for `DisDLC06ActivePowerComponent_Transversal`, its default object, the tweak class/default, and `DLC06_Pwr_Transversal` in the exact package paths.
3. Load the existing decompressed `DishonoredGame.upk` copy read-only with UELib; inspect the class declaration, superclass, default-object archetype, and decompiled defaults.
4. Decompress `DLC06_DaudBase_Script.upk` to ignored `assets/extracted/` and inspect the exact `DLC06_Pwr_Transversal` object path, runtime object class, and decompiled property values.
5. Record parser diagnostics and distinguish values emitted by UELib from unparsed or malformed fields.

## Observations

| Package | Export index | UModel class label | Object name | Serialized size |
|---|---:|---|---|---:|
| `DishonoredGame/CookedPCConsole/DishonoredGame.upk` | 27446 | `Class` | `DisDLC06ActivePowerComponent_Transversal` | 143 |
| same | 27447 | `DisDLC06ActivePowerComponent_Transversal` | `Default__DisDLC06ActivePowerComponent_Transversal` | 124 |
| same | 28144 | `Class` | `DisDLC06Tweaks_Transversal` | 167 |
| same | 28145 | `DisDLC06Tweaks_Transversal` | `Default__DisDLC06Tweaks_Transversal` | 40 |
| `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DaudBase_Script.upk` | 8990 | `DisDLC06Tweaks_Transversal` | `DLC06_Pwr_Transversal` | 1,463 |

- UELib resolves the class path as `Class'DishonoredGame.DisDLC06ActivePowerComponent_Transversal'`; its superclass is `Class'DishonoredGame.DishonoredActivePowerComponent_Blink'`.
- The emitted declaration is `class DisDLC06ActivePowerComponent_Transversal extends DishonoredActivePowerComponent_Blink`, marked `native(DLC06Transversal)`. The explicit class/default values include `m_PowerName="Transversal"` and `m_UIInteraction_Cancel=EDisUIInteraction.DUI_DLC06_Context_CancelTransversal`.
- The class default object's archetype is `DishonoredActivePowerComponent_Blink'DishonoredGame.Default__DishonoredActivePowerComponent_Blink'`; its emitted object block repeats the Transversal power name and cancel enum.
- UELib resolves the DLC object as `DisDLC06Tweaks_Transversal'DLC06_Twk_Powers_Transversal.DLC06_Pwr_Transversal'`.
- Its emitted `m_Levels` values include:
  - `[0]`: horizontal distance `1100`, vertical distance `600`, bend-down time `0`, bend-up time `0.5`.
  - `[1]`: horizontal distance `1600`, vertical distance `800`, bend-down time `0`, bend-up time `0.5`.
  - Both entries reference `Snd_Pwr_Transversal_Start` and `Snd_Pwr_Transversal_Stop`; `m_pFizzleSoundEvent` references `Snd_Pwr_Transversal_Cancel`.
- Other emitted fields include ground/mantle/low-fall/high-fall particle references, target-test extent `(20,20,20)`, `m_ManaCost=20`, `m_RuneCosts[1]=4`, Blink rumble waveform references, `m_VersionNum=13`, and `m_TweakNameCooked="DLC06_Twk_Powers_Transversal+++DLC06_Pwr_Transversal DisDLC06Tweaks_Transversal"`.
- UELib reported parse problems for `m_AnimStates`, `m_UsePowerAction`, `m_BaseClassVersions`, `m_FallbackSkip`, and `m_FallbackChainCooked`. For `m_UsePowerAction`, an enum value parse failed on `m_bCanMove`; the fallback arrays did not acquire array types. Those values are not reconstructed by this probe.

## Interpretation / claims

- **Observed:** the main package declares the Transversal active-power class as a native subclass of the Blink active-power component; the DLC06 package contains a tweak-class instance with the exact name/path and values listed above.
- **Inferred, limited:** the class/default and named DLC tweak instance are related by naming, class family, and serialized tweak-name data. These observations make a Transversal configuration join plausible, but do not show which native/runtime code consumes it.
- **Unknown:** whether the class's inherited power-tweak pointer resolves to this exact DLC06 instance at runtime, how the two level entries are selected, and what the fields mean in gameplay after native/config initialization.
- **Not established:** that these serialized values are effective runtime values, that the omitted/malformed fields are defaults, or that the emitted class declaration recovers original source.

## Reproduction and limitations

- Query the local UModel catalog `knowledge/database/umodel-package-objects.sqlite` for the exact package paths and export indices above; EXP-0053 documents catalog provenance.
- Use the decompressed main package from EXP-0009. Decompress `DLC06_DaudBase_Script.upk` with [the recorded tool](../tools/ue-package-decompressor/README.md) into an ignored output folder and load it with Eliot.UELib 1.13.3.
- UELib output is decompiler text. Its property-tag errors limit the fields listed above; inspect raw package data or another parser before relying on the affected arrays/enums.
- This records serialized metadata only and does not modify the Blink activation graph or establish an activation edge.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Blink superclass/default data: [EXP-0009](EXP-0009-blink-decompression-and-uelib.md)
- DLC package/function-label census: [EXP-0055](EXP-0055-uelib-dlc-script-package-boundary.md), [EXP-0056](EXP-0056-standalone-function-export-distribution.md)
- Full package export catalog: [EXP-0053](EXP-0053-all-install-upk-object-catalog.md)
