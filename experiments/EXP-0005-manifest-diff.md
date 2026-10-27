---
id: EXP-0005
title: Current copy differential against recorded Steam manifest
experiment_status: done
claim_status: observed
build: "10256413"
question: "Which paths differ between the previous and current local Steam inventories, and do shared paths match by hash?"
---
# EXP-0005 — Current copy differential against recorded Steam manifest

> Historical inventory snapshot: the 13,746-file copy described below was later changed. [EXP-0050](EXP-0050-workspace-build-inventory-revalidation.md) records the current 13,619-file workspace tree and supersedes those counts as the current inventory.

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Question: Does the copied game directory match the previously recorded Steam install, and what differs?
- Inputs: the generated local inventory and the existing reference manifest `E:\Dishonored REVERS\game\manifests\files.sha256.csv`.

## Procedure

1. Compare relative paths case-insensitively after normalizing separators to `/`.
2. Compare SHA-256 values for every shared path.
3. Report added/removed paths and summarize additions by top-level directory and file type.
4. Do not execute copy-only binaries or scripts.

## Observations

- Reference manifest: 13,607 paths.
- Current copied installation: 13,746 paths.
- Shared paths: 13,603; all 13,603 hashes match; zero mismatches.
- Reference-only paths: four — `Binaries/Win32/d3d9.dvr_backup.dll`, `Binaries/Win32/Dishonored_d3d9.log`, `Binaries/Win32/dvr_vp0_l5_threshold_samples_PREPLACE.txt`, and `Binaries/Win32/dvr.ini`.
- Current-copy-only paths: 143 — 136 under `Binaries`, four under `Mods`, one under `DishonoredGame`, one under `Engine`, and one root-level ZIP.
- Notable copy-only entries include `Binaries/Win32/dinput8.dll` (146,944 bytes; SHA-256 `77EC48CA6402A508807C832A9E1476990286DC6D648BD8DA0784F7D8BD7C1EF0`), `Binaries/Win32/CoopCharacterPreviews` with nine 20-byte `.cmd` files, and a Ghidra project tree under `Binaries/Win32`.

## Interpretation and limits

The matching shared hashes support that the copied directory has the same content as the reference for every shared path. This does not attribute the 143 additions or prove their runtime effects. They remain unexecuted and are treated as modifications or analysis artifacts until investigated.
