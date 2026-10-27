---
id: EXP-0084
title: Selected real UModel exports across seven fake-export resource classes
experiment_status: done
claim_status: mixed
build: "10256413"
question: "For one fake-selected object from each resource class observed in EXP-0082, does real UModel export produce files, and what output formats/dependencies are emitted?"
---

# EXP-0084 — Selected real UModel exports across seven fake-export resource classes

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: select one exact object from each of the seven fake-export classes in EXP-0082, confirm the same object is selected by `-testexport`, then invoke actual UModel `-export` and inventory every file written beneath ignored extraction storage.
- Exclusions: no claim that these samples represent every object/package, no pixel/mesh/animation semantic correctness claim, no runtime loading/use, and no source package modification. `_excluded_coop_project/` was not accessed.
- Tools: pinned UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`; Python 3 standard library; [sample runner](../tools/umodel_targeted_export_samples.py).
- Inputs: [selected-object rows](../research/packages/umodel-real-export-samples/selected-objects.csv), EXP-0082 fake-export census and current exact-build manifest.
- Outputs: [per-object results and file hashes](../research/packages/umodel-real-export-samples/per-object.csv), [summary](../research/packages/umodel-real-export-samples/summary.json), and ignored files under `assets/extracted/umodel-real-class-samples/`.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify the executable SHA-256 and pinned UModel SHA-256.
2. For each selected package, verify current size/SHA-256 against the exact-build file manifest and confirm the expected class has at least one fake-export request in EXP-0082.
3. Rerun `-testexport` for that package and require an exact class/object match before attempting the real export.
4. Run actual `-export` for one named object, directing results to a fresh per-sample directory under ignored `assets/extracted/`.
5. Record return codes, warnings/errors, every output path/size/SHA-256; validate the RLE packet streams of TGA outputs and the leading chunk tags of PSK/PSKX/PSA files.

Reproduce from the repository root in PowerShell (use a new output root and remove/rename prior report outputs first):

```powershell
python -u tools\umodel_targeted_export_samples.py `
  --umodel third_party\ueviewer-gildor\umodel.exe `
  --game-root 'Dishonored RHCP' `
  --manifest research\builds\BUILD-STEAM-10256413\files.csv `
  --fake-census research\packages\umodel-testexport-census\summary.json `
  --samples research\packages\umodel-real-export-samples\selected-objects.csv `
  --output-root assets\extracted\umodel-real-class-samples `
  --report-dir research\packages\umodel-real-export-samples
```

## Observations

- The runner re-hashed each source package and confirmed the exact requested object/class appeared once in `-testexport` output before actual export. All seven real `-export` invocations returned exit code 0 with zero real-export error lines. Six had zero real-export warnings; the AnimSet export had one warning and still emitted files.
- All seven selected objects produced output files. Across the seven isolated sample directories, UModel wrote 33 files totalling 31,352,732 bytes, including dependent textures/materials as selected by UModel. Per-object counts, warning counts, file paths, sizes, and hashes are in the CSV.

| Fake-export class | Selected object | Files written | Bytes written |
| --- | --- | ---: | ---: |
| `Texture2D` | `LevelMap_Ext_Boyle` | 1 | 1,192,609 |
| `MaterialInstanceConstant` | `Moon_HUB_Night_INST` | 7 | 2,236,924 |
| `StaticMesh3` | `Stm_SunDome` | 2 | 5,006 |
| `LightMapTexture2D` | `DirectionalMaxComponent0_145` | 1 | 1,692 |
| `SkeletalMesh3` | `Skm_Player` | 15 | 26,512,465 |
| `Material3` | `Moon_PMAT` | 4 | 1,162,472 |
| `AnimSet` | `Npc_TallBoy_Empty_as` | 3 | 241,564 |

- The 16 TGA outputs use RLE true-color encoding; their packet streams account for the declared image dimensions and consume each file exactly. PSK/PSKX outputs begin with the ActorX `ACTRHEAD` chunk tag; the PSA begins with `ANIMHEAD`. The AnimSet sample also emitted a zero-byte `.config` file, alongside a non-empty PSA and properties text.
- UModel emitted `.mat` and `.props.txt` files for the selected material objects and emitted texture files alongside selected material and skeletal-mesh objects. For example, `Moon_PMAT`'s formatted property text names `Texture2D'Vfx_Materials.Textures.Moon'` and `Texture2D'Skies02.FLOODED.Sky_Flooded_Rafinery_d'`; actual asset dependency ownership/use remains a separate question.

## Interpretation and claim limits

- **Observed:** one selected object from each of the seven EXP-0082 fake-export classes produced at least one real file with the pinned UModel build. The listed output formats and hashes are directly reproducible.
- **Observed:** selected object exports can emit additional files for materials/textures, so output-file count is not equivalent to the number of requested objects.
- **Unknown:** semantic correctness of image/mesh/animation content, whether the four-byte-drop note in EXP-0083 affects output, completeness of dependencies, and the general export behavior of untested objects/packages.
- **Limit:** this is seven objects from five packages, not package-wide or all-install real-export compatibility. Passing container signatures/RLE structure does not validate rendered game behavior.

## Links

- [EXP-0082 all-UPK fake-export compatibility census](EXP-0082-umodel-fake-export-census.md)
- [EXP-0083 single Texture2D export and MCP comparison](EXP-0083-umodel-single-texture-real-export.md)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [Sample runner](../tools/umodel_targeted_export_samples.py)
