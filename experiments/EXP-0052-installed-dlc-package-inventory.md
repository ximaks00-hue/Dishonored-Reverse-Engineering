---
id: EXP-0052
title: All-install UPK metadata census including DLC packages
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can UModel produce package metadata for every installed UPK in the recorded manifest, including nested DLC folders, and which packages return parser warnings?"
---

# EXP-0052 — All-install UPK metadata census including DLC packages

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: run UModel package-info parsing on all 904 UPKs in the current build manifest, including the 434 packages nested under DLC05/DLC06/DLC07; retain per-path manifest identity, package version, engine value, name/export/import counts, and warning/error counts.
- Exclusions: no package export, game launch, runtime attach, or binary modification; `_excluded_coop_project/` was not accessed. The local manifest is a workspace snapshot, not independent proof of Steam depot provenance.
- Tools: UModel x86, 1,026,048 bytes, SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`, built from upstream commit `a0bfb468d42be831b126632fd8a0ae6b3614f981`; Python 3 standard library.

## Procedure

1. Re-read the current research status, Blink activation graph, and build record; confirmed build ID and executable hash.
2. Used UModel wildcard `-pkginfo '*.upk'` separately in `DishonoredGame/CookedPCConsole` and nested directories DLC05, DLC06, and DLC07. This avoids the Assets MCP limitation to its CookedPCConsole manifest index.
3. Added `tools/umodel_pkginfo_census.py` to run those four read-only wildcard queries, join package summaries to the full build `files.csv` by exact relative path, and emit a package-level CSV.
4. Generated [installed-upk-pkginfo-census.csv](../research/packages/installed-upk-pkginfo-census.csv).
5. Checked row count, package load statuses, package warnings/errors, and engine-version distribution.

Reproduce from the repository root:

```powershell
python tools/umodel_pkginfo_census.py `
  --umodel "third_party/ueviewer-gildor/umodel.exe" `
  --game-root "Dishonored RHCP" `
  --manifest "research/builds/BUILD-STEAM-10256413/files.csv" `
  --output "research/packages/installed-upk-pkginfo-census.csv"
```

## Observations

- The full install manifest contains 904 UPKs: 470 under CookedPCConsole and 434 under DLC/PCConsole (DLC05: 160, DLC06: 113, DLC07: 161). Every package path, byte size, and SHA-256 in the DLC inventory matches the current full-install manifest.
- UModel returned a package summary for 904/904 packages. The census has 887 `loaded` rows and 17 `loaded_with_warnings` rows; zero package errors and zero packages missing from the census.
- The 17 warned packages produced 210 warning lines. Inspected examples report UModel replacing accented/non-ASCII characters in package name entries (for example, `Soirée` or `Matinée`); they are warnings on successfully loaded packages, not package-open failures.
- All package summaries report package version `801/30`. UModel's engine metadata groups are 461 packages at `9098` and 443 at `9411`. Game metadata value is `800033`.
- The census records per-package names, exports, imports, version, engine, warning count, and error count, joined to manifest size/hash. It contains metadata summaries only; it does not include full object listings or recovered script bodies.
- Assets MCP health is ready, but its package index remains limited to CookedPCConsole and does not resolve nested DLC package paths through the package-info interface.
- The installed package named `DishonoredGameFull_P.upk` in CookedPCConsole was reported at engine value 9098 in EXP-0011; the distinct `DLC06_DishonoredGameFull_P.upk` is reported at 9411. The difference is observed; its cause is unknown.

## Interpretation / claims

- **Confirmed for the current local snapshot:** UModel `-pkginfo` produced a metadata summary for all 904 manifest-listed installed UPKs; the package-level census reconciles to every UPK path.
- **Observed:** 17 packages load with name-fixing warnings; no package error was reported.
- **Unknown:** complete export/object-list coverage, script bytecode decompilation success, asset dependency relations, and local installation provenance against Steam depots remain unestablished.

## Reproduction and limitations

- Re-run the script above. It reads package files through UModel and writes only the metadata census CSV.
- UModel's `-pkginfo` success establishes package-summary parsing only. It does not establish that every export can be decoded, that all script bodies are recoverable, or that package assets are used at runtime.
- Preserve warning counts and exact package paths when diagnosing the 17 name-repair cases.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- CookedPCConsole inventory: [EXP-0011](EXP-0011-cookedpcconsole-inventory.md)
- Full-install revalidation: [EXP-0050](EXP-0050-workspace-build-inventory-revalidation.md)
- DLC UPK inventory: [installed-dlc-upk-inventory.csv](../research/packages/installed-dlc-upk-inventory.csv)
- Metadata census: [installed-upk-pkginfo-census.csv](../research/packages/installed-upk-pkginfo-census.csv)
- Census tool: [umodel_pkginfo_census.py](../tools/umodel_pkginfo_census.py)
- Package archaeology: [README](../research/packages/README.md)
- Project completion contract: [roadmap](../docs/roadmap.md)
