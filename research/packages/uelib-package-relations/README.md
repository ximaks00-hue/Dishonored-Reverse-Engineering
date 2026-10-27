# UELib package table relation census

This directory contains compact, checked-in summaries derived from a read-only UELib 1.13.3 pass over the 904 installed UPKs for build 10256413. The run rechecked every source package's byte length and SHA-256 against `assets/manifests/packages.csv`; UELib export/import counts were compared per package with the independent UModel `-pkginfo` census. All 6,278,432 non-null indices in the generated edge rows resolve to a table row within the same package.

| File | Contents |
| --- | --- |
| [uelib-package-relations-summary.json](uelib-package-relations-summary.json) | All-install totals, per-package reconciliation result, relation counts, and limits |
| [uelib-package-table-coverage.csv](uelib-package-table-coverage.csv) | One row per UPK with hashes, UELib/UModel table counts, and non-null serialized index counts |
| [uelib-import-package-candidates.csv](uelib-import-package-candidates.csv) | Source package and import-root-name pairs with candidate target UPK paths by filename stem |

The full generated object and edge JSONL is reproducible under the ignored `assets/extracted/uelib-package-relations-full/` directory. It contains one row per export/import table item and one row per non-null `OuterIndex`, `ClassIndex`, `SuperIndex`, `TemplateIndex`, or `ArchetypeIndex` in export records (plus import `OuterIndex`), resolved against the same package's signed import/export table indices. It does not require UELib object initialization.

## Reproduction

From the repository root in PowerShell:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-package-relations -- `
  --game-root 'Dishonored RHCP' `
  --manifest research\builds\BUILD-STEAM-10256413\files.csv `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-dir assets\extracted\uelib-package-relations-full

python tools\summarize_uelib_package_relations.py `
  --relations-dir assets\extracted\uelib-package-relations-full `
  --manifest assets\manifests\packages.csv `
  --pkginfo-census research\packages\installed-upk-pkginfo-census.csv `
  --output-dir research\packages\uelib-package-relations
```

The extractor processes one package at a time, checks the input against the install manifest, writes only table metadata to JSONL, and deletes each temporary decompressed package copy after parsing. An optional `--only <game-root-relative-upk-path>` supports a one-package probe.

## Interpretation boundary

The package-table indices are direct parsed fields from UELib's import/export table model. Import-root name to filename-stem relations are candidate path joins; they do not prove package loading at runtime. This census does not recover property values, object references serialized inside asset payloads, bytecode object operands, or runtime reachability. UELib parser compatibility is evidenced by this measured pass, not by an assertion that every field interpretation is independently validated against original Unreal source.
