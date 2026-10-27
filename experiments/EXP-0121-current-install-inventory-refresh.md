---
id: EXP-0121
title: Current install inventory refresh
experiment_status: done
claim_status: mixed
build: "10256413"
question: Does the saved full-tree inventory still describe the current workspace install, and do exact-build identity and UPK package inventory still match?
---

# EXP-0121 — Current install inventory refresh

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; EXE SHA-256 checked against the build record.
- Scope: regenerate the deterministic full-tree SHA-256 inventory and compare current EXE and UPK rows with recorded build/package manifests.
- Exclusions: no game launch or modification; no claim that all files are pristine depot files; prior full-tree manifest contents were not retained in Git, so newly added/changed paths cannot be enumerated from the earlier snapshot.
- Tools: Python 3; [inventory.py](../tools/inventory.py); Python CSV comparison.

## Procedure

1. Re-read repository instructions, research status, Blink activation graph, and exact-build record.
2. Run `python tools/inventory.py "Dishonored RHCP" research/builds/BUILD-STEAM-10256413/files.csv`.
3. Compare the regenerated inventory totals and EXE identity with the recorded build. Compare all current `.upk` rows by exact path, size, and SHA-256 against `assets/manifests/packages.csv`.

## Observations

- The regenerated current inventory contains 13,623 files totaling 15,098,142,031 bytes. The previous recorded inventory in EXP-0050 had 13,619 files totaling 15,062,334,363 bytes: a net increase of four files and 35,807,668 bytes.
- The previous full-tree CSV was not present in Git history, so this comparison cannot identify path-level additions, removals, or modifications.
- `Binaries/Win32/Dishonored.exe` is 18,041,856 bytes with SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the build record and current inventory row.
- Current inventory and package manifest each contain 904 `.upk` paths. Every package path, size, and SHA-256 matches; there are zero missing, extra, or mismatched rows.
- Re-ran `tools/non_upk_inventory.py` against the refreshed manifest. It classified all 13,623 paths, found all 3,384 Config/Localization candidates present and hash-matched, and all 4,411 DVR/Ghidra candidate paths hash-matched. Current family counts include 1,346 other CookedPCConsole files, 2,734 other DLC files, and five mod-tree files.

## Interpretation / claims

- **Confirmed:** the regenerated `files.csv` records the current workspace tree at this collection point; exact EXE identity and the 904-UPK manifest remain consistent.
- **Observed:** aggregate inventory totals differ from EXP-0050 by +4 files and +35,807,668 bytes.
- **Unknown:** which individual files account for those net changes because EXP-0050's previous full-tree CSV was not retained in Git history. Aggregate differences do not imply exactly four additions, since additions and removals may offset.
- **Limit:** build identity is established by the executable hash. This does not establish the provenance or pristine status of every other install file.

## Reproduction

From repository root:

```powershell
python tools/inventory.py "Dishonored RHCP" research/builds/BUILD-STEAM-10256413/files.csv
```

Compare `files.csv` `.upk` records against `assets/manifests/packages.csv` by normalized relative path, byte size, and uppercase SHA-256.

## Links

- Build record: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior full-tree comparison: [EXP-0050](EXP-0050-workspace-build-inventory-revalidation.md)
- Package inventory: [EXP-0052](EXP-0052-installed-dlc-package-inventory.md)
- Project completion contract: [roadmap](../docs/roadmap.md)
