---
id: EXP-0055
title: UELib and standalone Function exports in selected DLC packages
experiment_status: done
claim_status: observed
build: "10256413"
question: "Do selected DLC05/06/07 packages named *_Script.upk contain standalone Function-class exports, and what does UELib initialize after decompression?"
---

# EXP-0055 — UELib and standalone Function exports in selected DLC packages

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: compare UModel-listed export class labels with Eliot.UELib's initialized object types on selected DLC05, DLC06, and DLC07 packages whose filenames end in `_Script.upk`.
- Exclusions: original UPKs and game executable were read only; decompressed outputs are local ignored copies under `assets/extracted/umodel_uc_probe*`; no game launch, runtime attach, or file modification; `_excluded_coop_project/` was not accessed.
- Tools: UEViewer `decompress.exe` SHA-256 `A724FFD162C1D14D167FE0DA32769EFD15486A7DB96AB4CA8CD1C2FFF8CECBFE` (source commit `a0bfb468d42be831b126632fd8a0ae6b3614f981`); Eliot.UELib 1.13.3 via the existing UE Explorer MCP project; UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the exact executable hash.
2. Use the local UModel object catalog to select packages labelled `*_Script.upk` from DLC05, DLC06, and DLC07; record original package hashes, total export counts, and counts of standalone `Function`-class exports.
3. Run the recorded Gildor package decompressor into separate ignored output directories; do not overwrite source UPKs.
4. Load each decompressed copy with `UnrealLoader.LoadPackage(path, FileAccess.Read)`, call `InitializePackage()`, and count `UClass`, `UFunction`, and total initialized objects; also record `IsScript()` and runtime object-type distribution.
5. Compare to UModel class-label counts from the already generated catalog, and run the same UELib probe against the existing decompressed main `DishonoredGame.upk`.

## Observations

| Input package | Original bytes | Original SHA-256 | UModel exports / imports | UModel `Function` labels | Decompressed bytes | UELib objects | `UClass` | `UFunction` | `IsScript()` |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| `DishonoredGame/DLC/PCConsole/DLC05/L_DLC05_ChainKill_Script.upk` | 1,102,208 | `77B7915B111D36E798BE02523F6A28DDF3B0C3B843F6CE72C362B7411DCF532C` | 2,868 / 352 | 0 | 3,801,137 | 3,220 | 222 | 0 | false |
| `DishonoredGame/DLC/PCConsole/DLC05/L_DLC05_OilRain_Script.upk` | 1,425,606 | `DD19A49F52ED7B47CF242AC463BEA50AC561ADCFF3EF7125D9BCDA7270562858` | 4,640 / 348 | 0 | 6,137,328 | 4,988 | 204 | 0 | false |
| `DishonoredGame/DLC/PCConsole/DLC06/DLC06_DaudBase_Script.upk` | 18,674,760 | `62E46C0F78E5C7D2FFC4EBAB6006A557D9B444AD964A7818AA8DBB6AD602D306` | 28,111 / 1,953 | 0 | 47,423,795 | 30,064 | 905 | 0 | false |
| `DishonoredGame/DLC/PCConsole/DLC07/L_DLC07_Endgame_Script.upk` | 11,285,971 | `7415BCA95511328BA7C94F42924E230E1D828806761F6280758DC1AE346FAD03` | 11,025 / 780 | 0 | 20,165,470 | 11,805 | 416 | 0 | false |
| `DishonoredGame/CookedPCConsole/DishonoredGame.upk` (comparison) | 5,928,252 | `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2` | 30,049 / 652 | 981 | 17,320,971 | 30,701 | 2,284 | 1,097 | true |

- UModel and the decompressor read all four DLC source packages successfully and reported matching export/import table counts before and after decompression.
- UModel's generated object catalog contains zero rows with `object_class='Function'` for each of the four DLC inputs; the comparison main package has 981 such rows. These are UModel class labels, not proof of complete object deserialization.
- UELib initialized the reported export/import object totals for all four DLC copies, but exposed zero `UFunction` objects; `UClass` and `UStruct` counts were equal (222/222, 204/204, 905/905, and 416/416). It classified each DLC package as `IsScript() == false`; the comparison main package is `true`.
- In the DLC06 copy, `pkg.Objects` included 27,510 `UnknownObject`, 905 `UClass`, 647 `UPackage`, 385 `UTexture2D`, and other typed objects. Thus UELib did not fully map every object to a known runtime type.
- The comparison main package initialized 1,097 `UFunction` objects with the same library version and probe.
- UModel CLI `-help` documents `-uc` as “create unreal script when possible”. `-export -uc` on a selected DLC `Class` and a selected main-package `Function` reported `Unknown class` / “no supported objects”; no script output file was produced in the inspected output directory.

## Interpretation / claims

- **Observed:** UModel's export-label catalog reports zero standalone `Function`-class exports in these four selected DLC packages; UELib likewise returns zero `UFunction` objects. The selected main-package comparison reports 981 UModel `Function` labels and 1,097 UELib `UFunction` objects.
- **Observed:** UELib classifies the four selected DLC packages as non-script packages and maps many DLC06 exports to `UnknownObject` despite successful initialization.
- **Unknown:** whether the DLC class exports embed bytecode, whether other DLC packages or package families contain standalone functions, and whether UELib's `UnknownObject` exports contain relevant function/property data.
- **Not established:** absence of script bytecode from these packages, a UELib incompatibility with standalone DLC `Function` exports (none were observed), or direct decodability of raw export ranges.
- UModel's `-uc` wording and tested selection failures are scoped to the exact CLI/package/class combinations; they do not establish the limits of other UE3 tooling.

## Reproduction and limitations

- Reproduce decompression using [the recorded decompressor procedure](EXP-0009-blink-decompression-and-uelib.md) with each package's containing folder and a new ignored `assets/extracted/` output directory.
- Reproduce UELib counts through the existing `tools/ueexplorer-mcp` dependency (`Eliot.UELib` 1.13.3), call `InitializePackage()`, and count `pkg.Objects.OfType<UClass>()`, `OfType<UFunction>()`, and `pkg.Objects.Count`.
- Original package SHA-256 values are recorded in [the package metadata census](../research/packages/installed-upk-pkginfo-census.csv).
- This is a four-package probe across DLC05/06/07. It measures standalone export labels and UELib runtime object types, not bytecode coverage or package-wide property/reference recovery, and it does not establish that all DLC packages behave the same way.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior decompression and UELib check: [EXP-0009](EXP-0009-blink-decompression-and-uelib.md)
- All-install package metadata: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- All-install export catalog: [EXP-0053](EXP-0053-all-install-upk-object-catalog.md)
- UELib probe project: [ueexplorer-mcp.csproj](../tools/ueexplorer-mcp/ueexplorer-mcp.csproj)
