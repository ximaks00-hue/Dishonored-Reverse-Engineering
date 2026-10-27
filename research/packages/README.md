# Package archaeology

## Inventory baseline

The local file manifest contains 904 `.upk` files overall: 470 under `DishonoredGame/CookedPCConsole` and 434 under `DishonoredGame/DLC/PCConsole` (DLC05: 160, DLC06: 113, DLC07: 161). Package paths, sizes, and hashes are recorded in the build manifest and the DLC-specific inventory. UModel `-pkginfo` and `-list` produced per-package metadata and count-matched export labels for all 904 UPKs; see [EXP-0052](../../experiments/EXP-0052-installed-dlc-package-inventory.md), [EXP-0053](../../experiments/EXP-0053-all-install-upk-object-catalog.md), and the [package metadata census](installed-upk-pkginfo-census.csv). The Assets MCP source/index now supports all 904 game-root-relative paths, including nested DLC; the connected server needs a reload before accepting those paths (EXP-0054). [CookedPCConsole inventory](cookedpcconsole-upk-inventory.csv) and [DLC inventory](installed-dlc-upk-inventory.csv) remain separately available.

| Package | Local size | Local SHA-256 | Raw prefix (first 8 bytes) | Parsed metadata |
| --- | ---: | --- | --- | --- |
| `DishonoredGame/CookedPCConsole/DishonoredGame.upk` | 5,928,252 | `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2` | `C1 83 2A 9E 21 03 1E 00` | parsed by direct UModel CLI; see below |
| `DishonoredGame/CookedPCConsole/Core.upk` | 45,534 | `F432ACD67890BB7B02D355543E2EBA2830B0FFDE5CC4F2416312769BB49981C9` | `C1 83 2A 9E 21 03 1E 00` | parsed by direct UModel CLI; see EXP-0006 |

The tag and following bytes were captured directly. For `DishonoredGame.upk`, UModel reports version `801/30`; the following two little-endian 16-bit values decode to 801 and 30. This matching correspondence supports, but does not independently specify, the field interpretation.

## `DishonoredGame.upk` parser summary

UModel reports package version `801/30`, engine value `9411`, game value `800033`, 24,432 names, 30,049 exports, and 652 imports. Its class statistics include 2,008 `Class`, 981 `Function`, 665 `ScriptStruct`, and 528 `Enum` entries. See [EXP-0004](../../experiments/EXP-0004-umodel-blink-triage.md) for provenance and limits.

UModel reports `Core.upk` as version `801/30`, engine value `9411`, game value `800033`, 720 names, 1,356 exports, and 18 imports. Its class statistics include 9 `Class`, 272 `Function`, 52 `ScriptStruct`, and 10 `Enum` entries. See [EXP-0006](../../experiments/EXP-0006-core-package-metadata.md).

The full UModel census in EXP-0052 reports version `801/30` for every package, with engine values `9098` (461 packages) and `9411` (443 packages). EXP-0053 lists all exports: 2,885,414 object rows across 904 packages, with each package row count matching the `-pkginfo` export count. The generated searchable SQLite catalog is local at `knowledge/database/umodel-package-objects.sqlite`; it is reproducible with `tools/umodel_object_catalog.py` and excluded from Git. The distinct CookedPCConsole and DLC06 packages named `DishonoredGameFull_P` have different engine values; the cause is not established.

EXP-0069 adds a package-table pass with UELib 1.13.3 across all 904 UPKs. It parsed 2,885,414 exports and 225,535 imports, with every source hash/size and per-package count matching the manifest and UModel census. Its 6,278,432 non-null table indices describe package-local outer/class/super/template/archetype fields. Import-root names matched a unique installed filename stem for 2,287 of 2,416 source-package/name pairs; this is a candidate file association only. See the [UELib relation summaries](uelib-package-relations/README.md). Serialized property references, bytecode operands, and runtime dependency loading remain open.

## Tool compatibility record

EXP-0087 combines the 904-package UELib initialization corpus with the UModel fake-export per-package matrix. Its [seven-class CSV](uelib-umodel-class-property-coverage/class-coverage.csv) reports UELib export counts, wrapper/state/default-property rows, UModel request counts, and package overlap. EXP-0088 adds explicit UELib on-demand loads for the same exact-build package set; see the [coverage summary](uelib-on-demand-coverage/summary.json) and package/class matrices. Its 904-package identity, count, and run-completion checks passed; parser outputs and values still require independent validation.

| Operation | Result |
| --- | --- |
| Search package index | Source index covers 904 full paths; search/reload state recorded in [EXP-0054](../../experiments/EXP-0054-assets-mcp-full-package-paths.md) |
| Assets MCP package info/object list | Workspace source resolves all 904 full paths and reads the generated catalog; connected server reload remains pending, see [EXP-0054](../../experiments/EXP-0054-assets-mcp-full-package-paths.md) |
| Direct UModel CLI package info/list | `-pkginfo` and `-list` covered all 904 UPKs; all per-package export counts match; 17 packages had name-fixing warnings, zero package errors; [EXP-0052](../../experiments/EXP-0052-installed-dlc-package-inventory.md), [EXP-0053](../../experiments/EXP-0053-all-install-upk-object-catalog.md) |
| UModel asset-export selection | `-testexport` processed all 904 hash-matched packages: 205,165 fake-export requests from 721 packages; 485 warning-bearing packages and 13 package errors; no files written, see [EXP-0082](../../experiments/EXP-0082-umodel-fake-export-census.md) |
| UModel real asset-file export | Seven selected objects (one per EXP-0082 fake-export class) returned exit 0 and wrote 33 files (31,352,732 bytes); TGA RLE, PSK/PSKX and PSA structures were checked; full export coverage remains open, see [EXP-0084](../../experiments/EXP-0084-umodel-real-export-class-samples.md) |

The source package index covers all 904 paths. Pass a full game-root-relative path when a basename occurs more than once; a bare filename is accepted only when unique. A current read-only health check still reports connected Assets MCP 2.1.0; a current `get_package_info` call rejects a nested DLC full path as invalid, so the endpoint has not picked up the source's path-aware implementation. Independent UModel `-pkginfo` and `-list` passes cover all 904 install UPKs and count-match every export listing. EXP-0082 measures UModel's no-file fake-export path across the same set; EXP-0083/0084 confirm selected real exports, including seven resource classes, and record the MCP object-list discrepancy. Broad real export, property/reference recovery, and script-body decoding remain open.

See [EXP-0002](../../experiments/EXP-0002-package-header.md) for the repeatable triage procedure.

## Wwise bank/object links

EXP-0077/0078 parse HIRC objects from all 503 PCK banks plus `Init.bnk`, with container child and event/action/Sound/media paths. EXP-0080 removes 1,007 zero `ulTargetID` values from the unresolved-reference denominator; of the 92 nonzero edges with no parsed HIRC `ulID` candidate, EXP-0112 finds other-field numeric matches for 57 edges (35 same-PCK, 22 only other-PCK; SetGameParameter targets matching RTPC IDs, and Stop/Mute targets matching switch-node IDs). These remain identifier-domain candidates only; 35 edges across 17 IDs had no other field-value match in the parsed XML. See the [field-domain experiment](../../experiments/EXP-0112-wwise-unmatched-action-target-field-domain-scan.md), its [per-edge catalog](../builds/BUILD-STEAM-10256413/wwise-action-target-unmatched-domain-edges.csv), and [reproduction tool](../../tools/wwise_unmatched_action_target_domains.py).
