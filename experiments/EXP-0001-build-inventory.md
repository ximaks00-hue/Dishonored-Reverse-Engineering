---
id: EXP-0001
title: Steam x86 build identity and file inventory
experiment_status: done
claim_status: confirmed
build: "10256413"
question: "Which executable build is in the local copy, and what files does the copy contain?"
---
# EXP-0001 — Steam x86 build identity and file inventory

> Snapshot note: the 13,746-file inventory recorded here was later changed. [EXP-0050](EXP-0050-workspace-build-inventory-revalidation.md) records the current 13,619-file tree; the executable identity and CookedPCConsole package coverage remain verified.

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Question: Which executable build is in the local copy, and what files does the copy contain?
- Tools: PowerShell `Get-FileHash`, .NET `FileVersionInfo`, Python 3, [`tools/inventory.py`](../tools/inventory.py), local build registry.

## Procedure

1. Hash `Binaries/Win32/Dishonored.exe` with SHA-256 and read its file/product version metadata.
2. Compare its hash and architecture with the local build registry.
3. Run `python tools/inventory.py "Dishonored RHCP" "research/builds/BUILD-STEAM-10256413/files.csv"`.
4. Preserve only relative paths, lengths, and hashes in the repository.

## Observations

- The executable is 18,041,856 bytes, has file and product version metadata `1.0.0.0`, and hashes to `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- The registry associates that hash with Steam app `217980`, build `10256413`, architecture x86.
- The inventory contains 13,746 files totaling 15,132,885,287 bytes.
- The install has `Mods/StartInMenu` and `StartInMenu-Mod.zip`; presence does not establish activation.

## Interpretation and limits

The executable hash matches the recorded build. This does not prove every other installed file is an unmodified depot file. The folder name and file version string are not used as build identifiers.

## Reproduction

Regenerate the CSV with the command above. The scan hashes every regular file under the chosen root.
