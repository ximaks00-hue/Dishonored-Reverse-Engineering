---
id: EXP-0008
title: Blink script access through compressed package tools
experiment_status: superseded
claim_status: superseded
build: "10256413"
question: "Can Blink script/defaults be recovered from the compressed package without decompression?"
---
# EXP-0008 — Blink script access through compressed package tools

- Status: superseded by [EXP-0009](EXP-0009-blink-decompression-and-uelib.md)
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package: `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`
- Tools: UModel x86 (locally built upstream revision `a0bfb468d42be831b126632fd8a0ae6b3614f981`, SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`), Eliot.UELib 1.13.3.
- Question: Can the compressed package's script exports be read through currently installed tooling, to obtain Blink defaults and bytecode?

## Procedure and observations

1. Queried `ue_explorer.inspect_package`, `search_objects`, and `decompile_object`. The first two work on this package; decompilation returns the explicit compressed-package limitation. The listing exposes Blink candidates, classes, properties, and package-list offsets; see [EXP-0007](EXP-0007-ue-explorer-mcp.md).
2. Queried the installed Assets MCP for package info and export. Both operations returned generic execution errors. Its package index works, but the exact exception is unavailable.
3. Read the installed UModel command help. It documents `-dump` and `-uc`; package-specific calls found the Blink objects but reported `The specified package(s) has no supported objects.` This means UModel's game asset serializers do not handle these Dishonored UnrealScript object classes; it is not evidence that the objects are absent.
4. Ran UModel `-dump -all` against the package, capturing its console output under the OS temporary directory. It loaded and dumped supported package resources, confirming that UModel can process the compressed package, but output did not include Blink script classes/defaults/functions.
5. Read the installed Eliot.UELib 1.13.3 README/XML. The README documents `UnrealLoader.LoadPackage` then `InitializePackage` for script parsing; it notes compressed UE3 production packages may need decompression first. The library exposes `CompressedChunks` metadata but this version's current call path does not inflate these package tables.
6. Consulted Gildor's download page and forum instructions: the Unreal Package Decompressor is intended to turn compressed UE3 packages into separate uncompressed package files, preserving the source. The current download link on that page returned HTTP 404, and no `decompress.exe` is installed in the checked project/tool directories. Thus no decompression output was produced in this experiment.

## Result

- **Confirmed:** UModel can read/list the compressed package and dump supported resources; the supplied UModel build does not dump Dishonored script classes.
- **Confirmed:** the UE Explorer MCP's `decompile_object` path cannot read compressed object tables with the current UELib call.
- **Candidate workflow, not yet verified on this file:** use Gildor's UE3 package decompressor to make a separate uncompressed copy, then use UELib/UE Explorer to initialize exports, inspect class defaults, and decompile script functions. The official download page's current link is broken (404), so this workflow is not yet executable here.
- **Unknown:** whether the decompressed result will be accepted by UELib 1.13.3 for this exact package, and whether its Dishonored-specific script serializers/opcodes all decompile correctly.
- **Unknown:** Blink default property values, object outer chain, and script bytecode/source. No such values are inferred from the package-list names or offsets.

## Next step

Acquire a working copy of Gildor's Unreal Package Decompressor from an authoritative source (or build its open source `UEViewer/Tools/PackageUnpack` tool), decompress only `DishonoredGame.upk` to an ignored temporary/extracted directory, and validate the output with both UModel `-pkginfo` and UELib `InitializePackage`. If initialization works, inspect `Default__DishonoredActivePowerComponent_Blink`, `Twk_Blink`, `PowerAttributes_Blink`, and the class functions; preserve exact object paths and distinguish raw serialized values from decompiler output.

## Safety/scope

All commands above read the original package. Any future decompression/export must write only to an ignored extraction/temp directory; do not replace, patch, or otherwise modify game files.

## Follow-up

The official UEViewer `Tools/PackageUnpack` source was later built at the recorded upstream commit and successfully decompressed a copy of this package. UELib then initialized the object tables and decompiled Blink defaults. See [EXP-0009](EXP-0009-blink-decompression-and-uelib.md) for procedure, results, script findings, and parser caveats.
