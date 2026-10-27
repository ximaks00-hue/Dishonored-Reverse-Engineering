---
id: EXP-0182
title: Task-target record layout and save-data crosswalk
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do exact-build task-target offsets and records align with the versioned retail 2013 SDK layout and archive-associated call paths?"
---

# EXP-0182 — Task-target record layout and save-data crosswalk

- Date: 2026-10-27 (Europe/Kiev).
- Target build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Package anchor: installed `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`.
- External crosswalk: `dishonoredrecompiled`, commit `e7829390fa1c2fc7c200357e9de695ad4c613527`, whose README identifies retail 2013 / engine 9411 as the layout target and the symbolized 2012 QA build as a donor only.
- Portable evidence: [EXP-0182 crosswalk JSON](../research/executable/evidence/EXP-0182-task-target-layout-and-save-crosswalk.json).
- Scope: compare exact-build offsets and call/dataflow with reflected package names/types and a versioned external 2013 layout/source reconstruction. External fields are corroboration candidates, not target-binary ground truth.
- Exclusions: no Kismet node values/links, no runtime marker rendering or save/load observation, and no claim that external reconstruction code is original retail source.

## Procedure

1. Recheck the target executable identity against [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Read the exact-build `DisTaskTargetsSaveData`-associated functions and raw accessor evidence recorded in [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md).
3. Inspect the manifest-listed `DishonoredGame.upk` with package-summary/export-list tooling and retain only names/types and export identity; do not infer native offsets from compressed package data.
4. Compare offsets and sizes against the external 2013 SDK layout header and its static assertions; record the source commit and file hashes.
5. Review the 2012→2013 schema delta and the external save/load reconstruction for version and implementation caveats.
6. Treat disagreeing symbol matches as negative controls rather than forcing a name assignment.

## Observations

### Exact-build static evidence

- [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md) records exact-build accessor bytes `8D 41 68 C3` at `0x00B27E60`, which return `this+0x68`.
- The same experiment records `0x24`-byte records read/written through that descriptor and two functions (`0x00A0BA70`, `0x00A11780`) that resolve the exact UTF-16 literal `DisTaskTargetsSaveData` before a virtual call through slot `+0x138`.
- Exact-build code at `0x009C5AF0` is `mov eax,[ecx+0x64]; ret`; `0x00ACC160` scans task-like objects and returns the first whose DWORD at `+0x64` matches the supplied ID. The getter has two additional gameplay-logic callers that use its result as a nonzero gate, so its global semantic name is not established. The task-ID field interpretation is supported by the object scan and external layout, but not by the getter body alone.
- Exact-build `FUN_00BA84D0` reads action offsets `+0xFC`, `+0x100`, `+0x104`, and `+0x110`, while mutating selected `0x24`-byte rows at `+0x00`, `+0x04`, `+0x10`, `+0x1C`, and `+0x20` (EXP-0181). Names for these fields are not established by the instructions alone.

### Exact-build package export-list evidence

- The installed `DishonoredGame.upk` has package version `801/30`, EngineVersion `9411`, 24,432 names, 30,049 exports, and 652 imports in the local read-only package index. Its SHA-256 is recorded above.
- The package export-list artifact `dishonoredgame.list.txt` names `DishonoredTask_Base.m_Targets`, `DishonoredTask_Base.m_TaskID`, `DisTaskTargetsSaveData.m_TaskID`, `DisTaskTargetsSaveData.m_Targets`, and the `DisTaskTarget` members `m_pActor`, `m_TargetNameLocFile`, `m_TargetNameLocSection`, `m_VanishPreset`, and `m_bOptional`, with corresponding reflected property types.
- This establishes that the exact-build package contains those reflected names/types. The package is compressed; the available summary/export-list route does not expose serialized property values or prove native offsets. A decompile attempt was refused by the package tooling and is not treated as evidence.

### Versioned 2013 layout crosswalk

At external commit `e7829390fa1c2fc7c200357e9de695ad4c613527`, `DishonoredGameLayouts.h` carries retail-2013 static assertions matching the exact-build offsets:

| Exact-build observation | 2013 layout crosswalk | Match status |
| --- | --- | --- |
| task accessor returns `this+0x68` | `UDishonoredTask_Base::m_Targets` asserted at decimal 104 (`0x68`) | Strong offset/name crosswalk; external layout, not target-only proof |
| target rows stride `0x24` | `sizeof(FDisTaskTarget) == 36`; fields `m_pActor +0`, localization strings `+4/+16`, `m_VanishPreset +28` | Strong size and field-offset alignment |
| action fields `+0xFC/+0x100/+0x104/+0x110` | `m_TargetIndex` 252, `m_pTargetActor` 256, `m_TargetName` 260, `m_MarkerVanishPreset` 272 | Strong offset/name crosswalk; handler-to-class identity remains cross-source |
| exact-build task lookup uses DWORD `+0x64` | `UDishonoredTask_Base::m_TaskID` asserted at decimal 100 (`0x64`) | Strong offset/name crosswalk |
| local save-data record starts with ID then descriptor | `FDisTaskTargetsSaveData` size 16; `m_TaskID +0`, `m_Targets +4` | Layout agrees with the 0x10-byte temporary record pattern; archive serialization details remain inferred |
| row byte/bit at `+0x20` | external declaration has `m_bOptional:1` after `m_VanishPreset +28` | Candidate field alignment only; no separate static assertion for the bitfield offset was found |

The external header also places `m_bOptional` after `m_VanishPreset`; arithmetic/layout suggests byte `+0x20`, but this experiment does not upgrade that individual bitfield offset to a target-confirmed fact. The external layout is versioned to retail 2013 / engine 9411, while the target EXE and package record are independently identified by local hashes.

### Archive-associated path and version delta

- The 2013 crosswalk source `dissavegame.cpp` labels RVAs `0x611780` and `0x60BA70` as `UDishonoredMapInfo::GameSave` and `GameLoad`; its own comments state that the write-side target records are not implemented in this reconstruction, and that the load-side bytes are consumed without restoring targets. These labels are corroborative source crosswalks, not exact-build native symbols.
- The external matcher links target VAs `0x00A11780` and `0x00A0BA70` to those 2013 RVAs with imperfect similarity scores (`0.819`, `0.729`) and small size differences. This makes the save/load names plausible, not confirmed.
- Indexed exact-build direct-call counts are three for `FUN_00B27E60`, two for `FUN_00A08A90`, and two for `FUN_009FAD70`; this bounds the currently indexed direct paths only and does not rule out inline field access or indirect calls. `FUN_00BA6FA0`, called only by the update handler, removes a row range, shifts the tail, updates count, and may shrink capacity; this is array mechanics, not evidence for a separate target semantic.
- `script_delta_2012_2013.md` records that 2013 `DisTaskTargetsSaveData` uses `m_TaskID` where 2012 used object pointer `m_pTask`; the 2013 `FDisTaskTarget` is size 36 while the 2012 PDB layout was size 24, with localized target-name fields added. Thus 2012 structures cannot be substituted for the retail 2013 layout.

### Negative control: ambiguous `GetTargets` symbol

- An external matcher proposes `GetTargets` for target VA `0x00A42290`, but the exact-build body is `lea eax,[ecx+0x64]; ret`.
- The 2013 layout puts `m_TaskID` at `+0x64` and `m_Targets` at `+0x68`. The candidate name therefore conflicts with the layout and does not identify the `+0x68` array accessor. Keep this symbol association unresolved; do not use it to rename `FUN_00B27E60` or prove its class.

## Interpretation

- **Observed, exact-build:** the task-instance lookup compares a DWORD at `+0x64`, and the update handler accesses a per-instance descriptor at `+0x68`; it uses fields and records at offsets/sizes matching a 2013 retail layout. Exact-build package exports contain matching reflected names and types.
- **Strongly corroborated, cross-source:** the task lookup key at `+0x64` is likely `m_TaskID`; `+0x68` is likely `m_Targets`; the `0x24`-byte row is likely `FDisTaskTarget`; and action offsets map to `UDisSeqAct_UpdateTaskTarget` properties. These names are not independently embedded in the target native code. The standalone `+0x64` getter is reused elsewhere as a generic nonzero gate and is not itself proof of the field name.
- **Inferred:** the two archive-associated functions are likely GameSave/GameLoad paths. The matcher scores and reconstructed/partial source prevent treating the names or lifecycle behavior as confirmed.
- **Unknown:** target row `+0x20` optional-bit interpretation at the exact bit level, actual archive payload values, dynamic method identity at `+0x138`, runtime restoration behavior, marker display behavior, and the mapping from a concrete Boyle Kismet node to this handler.

## Reproduction

1. Verify the EXE and UPK SHA-256 values against the build/package manifests.
2. Recreate the accessor, row-stride, ID-lookup, and archive-string callsite observations in EXP-0181; inspect all direct callers of `FUN_009C5AF0` before assigning it a semantic name.
3. Check the external repository at the pinned commit and verify `DishonoredGameObjectivesClasses.h`, `DishonoredGameLayouts.h`, `script_delta_2012_2013.md`, and `dissavegame.cpp` against the hashes in the evidence JSON.
4. Compare only the 2013 layout assertions and explicit version delta; do not import 2012 PDB offsets as retail offsets.
5. Recheck VA `0x00A42290` directly before making any `GetTargets` naming claim.

## Links

- Exact build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Exact-build descriptor and archive-associated paths: [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md)
- Objective/task/Kismet/HUD cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
