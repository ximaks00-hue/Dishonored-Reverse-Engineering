---
id: EXP-0063
title: Install file family census and config/localization profile
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What non-UPK file families are present in the recorded install manifest, and what structure and declared paths can be measured in config and localization text?"
---

# EXP-0063 — Install file family census and config/localization profile

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: classify every row in the recorded 13,619-file manifest by path/extension; re-hash config/localization text and selected diagnostic/project subtrees in the present local tree; profile section/key structure in text files; extract configuration inheritance and path-like directives.
- Exclusions: this does not refresh every hash in the 15-GB install tree; suffix and directory labels are inventory categories, not format proof; config directives are not resolved as runtime dependencies; no game launch or modification; `_excluded_coop_project/` was not accessed.
- Tools: Python 3; [non_upk_inventory.py](../tools/non_upk_inventory.py); recorded full-tree manifest from EXP-0050; PowerShell `Get-FileHash` spot check for the build executable.

## Procedure

1. Read `docs/research-status.md`, `docs/gameplay/blink/activation-graph.md`, and the build record; verify the local EXE hash against build `10256413`. The current hash is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
2. Classify each row of `research/builds/BUILD-STEAM-10256413/files.csv` by a transparent path/extension rule and write a family/extension count-and-byte table.
3. For all manifest paths under `DishonoredGame/Config`, `DishonoredGame/Localization`, and `Engine/Config` / `Engine/Localization`, check current presence, file size, and SHA-256. Parse BOM-aware UTF-16/UTF-8 text using a line lexer for section headers and key/value assignments; retain unclassified non-comment lines rather than treating them as valid entries.
4. Normalize locale file stems (locale extension differs by folder), compare each CZE/HUN/POL/RUS section/key set with INT within game and engine localization trees, and report file-set and key-set differences.
5. Extract `BasedOn` and path-like key assignments from config text to a separate CSV. Treat values as recorded declarations; do not resolve them to runtime-loaded assets.
6. Optionally re-hash all manifest entries under `Binaries/Win32/dvr_cb`, `dvr_cc`, `dvr_vp0`, `dvr_traces`, and `ghidra_projects`; compare both size and SHA-256 to the saved manifest.

Reproduce from repository root:

```powershell
python tools/non_upk_inventory.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --game-root "Dishonored RHCP" `
  --summary-output research/builds/BUILD-STEAM-10256413/file-family-extension-census.csv `
  --text-output research/builds/BUILD-STEAM-10256413/config-localization-profile.csv `
  --config-reference-output research/builds/BUILD-STEAM-10256413/config-path-directives.csv `
  --localization-parity-output research/builds/BUILD-STEAM-10256413/localization-structure-parity.csv `
  --verify-text-hashes `
  --verify-dvr-ghidra-hashes
```

## Observations

- The input manifest contains 13,619 files totaling 15,062,334,363 bytes. It records 904 `.upk` files separately from other content.
- Path/extension classes include: 904 Unreal packages; 1,345 other CookedPCConsole files; 2,731 other DLC-tree files; 508 audio/WWise-named files; 90 movie files; 12 `.tfc` texture-cache files; 164 redistributable files; 36 executable/library files; 42 config-tree files; and 3,342 localization-tree files (3,282 game, 60 engine). Remaining families and extension counts are in [file-family-extension-census.csv](../research/builds/BUILD-STEAM-10256413/file-family-extension-census.csv). The categories use the helper's path/extension precedence; they do not certify file format or game use.
- All 3,384 current config/localization candidates (42 config plus 3,342 localization) exist and match the manifest SHA-256. Their sizes also match. Decoding selected by BOM/UTF-8 detection: 3,138 UTF-16-with-BOM, 245 UTF-8, and one CP1252 fallback.
- The lexer counted 9,789 config lines, 606 section headers, and 7,818 assignments; it encountered 79 non-comment non-section non-assignment lines in three config files. It counted 3,599 repeated section/key pairs; repeated keys may be intentional Unreal config merge/array syntax and are not parser errors.
- Game localization: 3,282 files across INT (658), CZE/HUN/POL/RUS (656 each). Each non-INT locale shares 656 filename stems with INT; INT has two additional stems and there are no locale-only stems. Exact section/key-pair sets match in 496/656 CZE, 510/656 HUN, 652/656 POL, and 644/656 RUS files. Pair-difference totals are retained in the parity CSV.
- Engine localization: 12 files in each of INT/CZE/HUN/POL/RUS, with identical filename stems. Seven of 12 files per locale have identical section/key-pair sets to INT; each comparison reports 151 INT-only and 43 locale-only pairs. This structural comparison does not assess translation correctness or runtime fallback behavior.
- The parser emitted 76 config inheritance/path-like directive rows, including 14 `BasedOn` rows. The rows include an explicit parent-relative `DefaultEngine.ini` reference to Engine `BaseEngine.ini`, repeated in a backup file. These are declarations only; runtime resolution and which config values are consumed remain unknown.
- The saved manifest has 4,290 files under `dvr_cb`/`dvr_cc`, 108 under `dvr_vp0`, four under `dvr_traces`, and nine under `ghidra_projects`. All 4,411 current files in those path groups match manifest size and SHA-256. Their directory names identify capture/project data in this local tree; their provenance relative to a clean depot install is not established.

## Interpretation / claims

- **Confirmed for this saved manifest and re-hashed subset:** file-family aggregate counts sum to the manifest's 13,619 rows; the 3,384 config/localization files and 4,411 selected `dvr_*`/Ghidra paths match current local size/hash.
- **Observed:** config and localization use BOM-marked UTF-16 predominantly, with UTF-8 also present; a section/key lexer can derive structural profiles and compare locale key sets.
- **Observed:** configuration text contains 76 inheritance/path-like declarations, including 14 `BasedOn` rows.
- **Inferred, limited:** `dvr_*` and `ghidra_projects` paths are local diagnostic/capture and analysis artifacts based on their directory names and contents. Matching the saved manifest does not prove they belong to the original game depot.
- **Unknown:** actual engine path-resolution semantics for the directives, runtime-loaded configuration subset, resource-to-package dependency graph, audio/video payload structure, and completeness/provenance of the local installation snapshot.

## Reproduction and limitations

- CSV artifacts: [family/extension counts](../research/builds/BUILD-STEAM-10256413/file-family-extension-census.csv), [per-file config/localization lexer profile](../research/builds/BUILD-STEAM-10256413/config-localization-profile.csv), [config path declarations](../research/builds/BUILD-STEAM-10256413/config-path-directives.csv), and [locale structure comparison](../research/builds/BUILD-STEAM-10256413/localization-structure-parity.csv).
- The helper hashes only the text and optional DVR/Ghidra subsets specified above. Other file-family counts come from the saved EXP-0050 manifest; their current hashes were not all recalculated in this experiment.
- Family labels are reproducible classification buckets, not authoritative parser compatibility labels. `.int`/`.rus` extensions outside the localization directories can be cooked assets, so the helper identifies localization by path first.
- The section/key lexer does not implement Unreal config merging, quoting, escaping, localization fallback, or runtime package loading. Repeated keys and the small set of unclassified non-comment lines are preserved as coverage caveats.
- No sound bank, movie, texture cache, executable/library, or redistributable content parser was validated package-wide here.

## Links

- Build record: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior manifest revalidation: [EXP-0050](EXP-0050-workspace-build-inventory-revalidation.md)
- Package inventory: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- Config/localization artifacts: [BUILD-STEAM-10256413 generated CSVs](../research/builds/BUILD-STEAM-10256413/)
- Project completion contract: [roadmap](../docs/roadmap.md)
