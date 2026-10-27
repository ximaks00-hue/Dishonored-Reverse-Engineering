---
id: EXP-0123
title: DLC06 Transversal tweak object UModel dump coverage
experiment_status: done
claim_status: observed
build: "10256413"
question: Does the pinned UModel dump path emit a property view for the DLC06 Transversal tweak instance when given its DLC directory and the owning DishonoredGame script package?
---

# EXP-0123 — DLC06 Transversal tweak object UModel dump coverage

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: request one named DLC06 export from UModel `-dump` with the DLC subtree and then the complete `DishonoredGame` directory searchable; repeat with `DishonoredGame.upk` explicitly added through `-pkg`.
- Exclusions: no game launch, package mutation, or claim that UModel can never parse the class under another workflow/version. UELib formatted fields are not independently validated by this test.
- Package: `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DaudBase_Script.upk`, 18,674,760 bytes, SHA-256 `62E46C0F78E5C7D2FFC4EBAB6006A557D9B444AD964A7818AA8DBB6AD602D306`.
- Tool: UModel SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.
- Durable prior object record: [EXP-0058](EXP-0058-dlc06-transversal-class-and-tweak-data.md) identifies `DLC06_Pwr_Transversal`, its export row, and UELib's serialized property view.

## Procedure

1. Verify build and source package identity against the current exact-build records.
2. Run UModel `-dump` on the named object with the DLC06 directory as `-path`.
3. Repeat with `DishonoredGame` as the search root, then add `DishonoredGame` as an explicit extra package using `-pkg=DishonoredGame`.
4. Capture exit codes, package-load messages, object selection, and class warnings. Inspect only the named export's result; package class statistics are not treated as an object dump.

Reproduce from the repository root:

```powershell
third_party\ueviewer-gildor\umodel.exe -dump -game=dis `
  "-path=Dishonored RHCP\DishonoredGame" `
  -pkg=DishonoredGame `
  DLC06_DaudBase_Script.upk DLC06_Pwr_Transversal
```

## Observations

- With the DLC06 folder as the search path, UModel loads the package (`801/30`, `Names=14381`, `Exports=28111`, `Imports=1953`), finds `DLC06_Pwr_Transversal`, reports `Unknown class "DisDLC06Tweaks_Transversal"`, and says there are no supported objects. Exit code: 0.
- With the complete `DishonoredGame` directory as the search path, UModel scans 924 files in four folders, loads the same DLC package, finds the named export, and reports the same unknown-class/no-supported-object result. Exit code: 0.
- With `-pkg=DishonoredGame` added, UModel also loads `CookedPCConsole/DishonoredGame.upk` (`Names=24432`, `Exports=30049`, `Imports=652`) before selecting the DLC export; it still reports the custom tweak class as unknown and emits no property dump for the target. Exit code: 0.
- EXP-0058 records the target as a `DisDLC06Tweaks_Transversal` export with serial size 1,463 bytes. Its UELib on-demand record uses package index 8991, state `Deserialized`, and reports 17 default-property rows. EXP-0058 separately records UELib parser errors for several fields, so its view is partial and remains unverified by UModel here.
- Current source package and UModel hashes match the values listed above. Captured UModel logs are under ignored `assets/extracted/`.

## Interpretation / claims

- **Observed:** on the pinned UModel build, adding the package that declares the custom tweak class does not make the named DLC object eligible for the `-dump` property path. UModel finds the object but does not emit a property view.
- **Unknown:** whether another UModel command/path, a newer build, or a different parser can decode this serialized object; whether the UELib field values match the raw serialized payload.
- **Limit:** this result is scoped to one object, one package, one UModel build, and `-dump`. Successful package loading and exit code 0 do not mean the target's properties were decoded.

## Links

- Prior serialized view and parser diagnostics: [EXP-0058](EXP-0058-dlc06-transversal-class-and-tweak-data.md)
- Exact-build package record: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- UModel compatibility census: [EXP-0082](EXP-0082-umodel-fake-export-census.md)
- Project completion contract: [roadmap](../docs/roadmap.md)
