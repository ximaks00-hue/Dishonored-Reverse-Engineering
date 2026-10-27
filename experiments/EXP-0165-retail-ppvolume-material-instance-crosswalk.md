---
id: EXP-0165
title: Retail PPVolume material-instance crosswalk
experiment_status: done
claim_status: mixed
build: "10256413"
question: Does the editor archive's PPVolumeMaterialInstance lead have a matching catalog-level object in retail Startup.upk, and what does the match establish?
---

# EXP-0165: Retail PPVolume material-instance crosswalk

- Experiment status: done
- Claim status: mixed
- Build ID: Steam RHCP 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`
- Question: Compare read-only package/export summaries for the June editor EngineMaterials package and exact-build retail Startup package.
- Scope and exclusions: UModel `-pkginfo` / `-list` only. No property dump, object decompilation, payload extraction, runtime launch, or package modification. This tests catalog identity and serial-size coincidence, not equivalent serialized fields or behavior.
- Prerequisites / starting state: June source package and retail Startup package available read-only; retail manifest and June archive record provide expected package hashes.
- Tools and versions: UModel/UEViewer binary `third_party/ueviewer-gildor/umodel.exe`, SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; invoked as `-game=dis -path=<package-directory> -pkginfo` and `-list`.

## Procedure

1. Verify the retail executable identity against [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
2. Verify both package SHA-256 values before parsing:
   - June editor `EngineMaterials.upk`: `4E48317026152CBF44B44ECB42225254A0977AF471994D906929BC7FE35918BF`.
   - Retail `DishonoredGame/CookedPCConsole/Startup.upk`: `7B82FF1C3560F9B867D57EF5219F0FE9D10378DE705EE92A68FB9B2D1877BBBA`.
3. Run UModel `-pkginfo` and `-list` directly on each verified file. Filter the full listing for `PPVolumeMaterial` and preserve only matching rows and package counters.
4. Compare package version, engine version, package counts, object class/name, and the serial size printed in the export row. Do not infer property equivalence from size.

## Observations

All observations below are parser output for the hash-pinned package files.

| Package | SHA-256 | UModel header | `PPVolumeMaterial` row | `PPVolumeMaterialInstance` row |
|---|---|---|---|---|
| June editor `EngineMaterials.upk` | `4E483170…E35918BF` | 801/30, Engine 9014, 970 names, 674 exports, 76 imports | `125 21704 145 Material PPVolumeMaterial` | `364 2DC84 29C MaterialInstanceConstant PPVolumeMaterialInstance` |
| Retail `Startup.upk` | `7B82FF1C…1877BBBA` | 801/30, Engine 9098, 8,782 names, 8,378 exports, 899 imports | `3707 589BBF 145 Material PPVolumeMaterial` | `4304 5ACD6B 29C MaterialInstanceConstant PPVolumeMaterialInstance` |

`0x145` and `0x29C` are serial sizes in hexadecimal: 325 and 668 bytes respectively. Both UModel `-pkginfo` and `-list` runs returned exit code 0 on both packages. The retail list contained 118 `MaterialInstanceConstant` rows. The June editor task record separately reports the June instance's serialized parent as `EngineMaterials.PPVolumeMaterial`; UModel `-list` itself does not expose that parent relation.

## Interpretation

- **Observed:** Both package listings contain same-named exports with the same classes and serial sizes for `PPVolumeMaterial` and `PPVolumeMaterialInstance`.
- **Observed:** The packages are not identical build artifacts: their engine versions, package names, counts, and export offsets differ (June Engine 9014 vs retail Engine 9098).
- **Inferred, weak:** The same class/name/size pair is a useful candidate for a field-level crosswalk. Identical size alone does not establish identical serialized properties, array layout, parent reference, or shader-map contents.
- **Unknown:** Retail `PPVolumeMaterialInstance` parent, tagged properties, expression arrays, shader-map IDs, package import references, runtime load/use, and any relation to the editor's Expressions/PostLoad failure.
- **External-source boundary:** The June parent relation and editor failure are reported by editor TASK-0230, not independently reproduced here and not retail runtime evidence.
- **Confidence:** High for package identity and the UModel export-list rows; low for semantic equivalence because no object payload was decoded.
- **Falsification:** A reparse of either exact-hash input that yields different package counters or export rows would invalidate the catalog comparison. A future authorized field-level parse showing different parent/property structure would reject structural equivalence while leaving this catalog observation intact.

## Reproduction

- Reset/cleanup steps: None; UModel was run read-only and no output files were written.
- Repeat count and variation: One `-pkginfo` and one `-list` run per package after SHA verification.
- Known sources of variance: UModel listing indices are zero-based in the displayed rows; the editor audit describes the June slot as one-based export slot 365 (UModel row 364). MCP output is truncated at 200,000 characters; the retail row at 4304 must be located from a complete listing or filtered during direct invocation.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Files/functions/objects: retail `Startup.upk`, exports 3707 and 4304; June `EngineMaterials.upk`, UModel rows 125 and 364.
- Related experiments: none.
- Open questions: A separately permitted and validated read-only property parser is needed for field-level comparison. Continue to treat compressed packages as summary/search-only under the current repository instructions.
- External comparison source: `D:\Dishonored\10_EDITOR_RESTORATION\Dishonored_ED_Recovery_Kit\tasks\TASK-0230.md`, section “offline June MIC-free EngineMaterials slice”; editor archive is not retail evidence.
