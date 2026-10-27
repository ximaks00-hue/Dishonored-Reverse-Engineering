---
id: EXP-0006
title: Core.upk package metadata
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "Do UModel and package-header triage agree on Core/DishonoredGame package version and engine metadata?"
---
# EXP-0006 — Core.upk package metadata

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package: `DishonoredGame/CookedPCConsole/Core.upk`
- Tool: UModel x86, SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.

## Procedure

```powershell
& 'E:\Dishonored REVERS\third_party\ueviewer-gildor\umodel.exe' `
  -game=dis `
  '-path=E:\Dishonored Reverse Engineering\Dishonored RHCP\DishonoredGame\CookedPCConsole' `
  -pkginfo Core.upk
```

## Observations

UModel reports package version `801/30`, engine value `9411`, game value `800033`, 720 names, 1,356 exports, and 18 imports. Class statistics include 9 `Class`, 272 `Function`, 52 `ScriptStruct`, and 10 `Enum` entries.

## Interpretation and limits

This is a second successfully parsed package from the same copied build. Its counts are parser-reported metadata; they do not establish that all function entries are gameplay code or that the package contains a particular runtime behavior.
