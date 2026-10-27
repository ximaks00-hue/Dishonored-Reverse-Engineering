---
id: EXP-0053
title: All-install UModel export-object catalog
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "Can UModel list every export in all 904 installed UPKs, and does the per-package listing count match the package-info export count?"
---

# EXP-0053 — All-install UModel export-object catalog

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: stream UModel `-list` output for every installed UPK and create a local SQLite catalog of export index, package offset, serialized size, class label, object label, and package path; compare per-package row counts to EXP-0052 export counts.
- Exclusions: no export of game assets or script text, no game launch/runtime attach, no binary modification; `_excluded_coop_project/` was not accessed.
- Tools: UModel x86 SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, upstream commit `a0bfb468d42be831b126632fd8a0ae6b3614f981`; Python 3 standard library.

## Procedure

1. Re-read the current research status, Blink activation graph, and build record; confirmed exact build identity.
2. Confirmed UModel `-list` output on the main DishonoredGame package and DLC06's large DishonoredGameFull package. The records include ordinal, package offset, serialized size, class-like label, and object name.
3. Added [umodel_object_catalog.py](../tools/umodel_object_catalog.py). It runs streaming wildcard listings per package directory, uses full relative package paths, joins the manifest hash/size and EXP-0052 package counts, and writes a local SQLite database.
4. Generated the catalog at `knowledge/database/umodel-package-objects.sqlite`. This path is ignored by Git under the existing local analysis database rule.
5. Queried package and object row counts, exact export-count matches, and sample object names from DishonoredGame.upk and the package-wide class-label distribution.

Reproduce from the repository root:

```powershell
python tools/umodel_object_catalog.py `
  --umodel "third_party/ueviewer-gildor/umodel.exe" `
  --game-root "Dishonored RHCP" `
  --manifest "research/builds/BUILD-STEAM-10256413/files.csv" `
  --pkginfo-census "research/packages/installed-upk-pkginfo-census.csv" `
  --output "knowledge/database/umodel-package-objects.sqlite"
```

The script refuses to overwrite an existing catalog.

## Observations

- UModel listed exports for 904/904 manifest-listed UPKs across CookedPCConsole, DLC05, DLC06, and DLC07.
- The local SQLite catalog contains 2,885,414 object/export rows across 904 distinct package paths, with 3,077 distinct class-label strings.
- All 904 packages have `list_status=count_match`: every listed row count exactly matches that package's `-pkginfo` export count. No count mismatch or unlisted package was observed.
- The package metadata census reports 17 packages with 210 warning lines and zero errors. The list pass retained the per-package warning and error counts.
- Search queries return the expected package exports: `DisItemContext_UsePower` and `DishonoredActivePowerComponent_Blink` appear as class/default-object labels in `DishonoredGame/CookedPCConsole/DishonoredGame.upk`.
- The generated SQLite database is approximately 1.0 GB. It is local, reproducible metadata and is excluded from Git; the generator and compact package-info CSV are the portable artifacts.

## Interpretation / claims

- **Confirmed:** UModel `-list` returned a complete count-matched export listing for every UPK in the named local manifest.
- **Confirmed:** the generated catalog preserves package path identity, including nested DLC folders and repeated basenames.
- **Unknown:** a listed export row does not establish complete object deserialization, property/reference graph recovery, script bytecode decompilation, native behavior, or runtime use. Those require separate evidence and experiments.

## Reproduction and limitations

- Re-run the command above after removing or choosing a new output path for the generated local database.
- Query using SQLite; `objects.object_name` and `objects.object_class` are indexed case-insensitively, and `objects.relative_path` joins to the package table.
- `-list` counts matching `-pkginfo` export counts, but this count agreement is not an independent confirmation of how UModel maps every displayed label to the original package object model.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Package metadata census: [installed-upk-pkginfo-census.csv](../research/packages/installed-upk-pkginfo-census.csv)
- Census experiment: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- Package archaeology: [README](../research/packages/README.md)
- Generator: [umodel_object_catalog.py](../tools/umodel_object_catalog.py)
- Project completion contract: [roadmap](../docs/roadmap.md)
