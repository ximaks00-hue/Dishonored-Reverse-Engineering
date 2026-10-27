---
id: EXP-0050
title: Current workspace build inventory revalidation
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the saved build inventory still describe the current local game tree, and does the CookedPCConsole package index still match?"
---

# EXP-0050 — Current workspace build inventory revalidation

- Date: 2026-10-26 (Europe/Kiev).
- Build identity: Steam app `217980`, build `10256413`; current `Dishonored.exe` SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: read-only full-tree metadata inventory; compare the previous `files.csv` snapshot to the current game directory; independently compare CookedPCConsole package files with the package index.
- Exclusions: no game process launch or modification; `_excluded_coop_project/` was not accessed; no game file was changed.

## Procedure

1. Re-read `docs/research-status.md`, `docs/gameplay/blink/activation-graph.md`, and this build record; verified the EXE hash against the build identity.
2. Ran `python tools/inventory.py "Dishonored RHCP" research/builds/BUILD-STEAM-10256413/files.csv` to regenerate the current metadata-only inventory.
3. Compared the regenerated inventory to the prior 13,746-row `files.csv` snapshot before replacing it.
4. Independently hashed every top-level `.upk` in `DishonoredGame/CookedPCConsole` and compared path, size, and SHA-256 with `assets/manifests/packages.csv`.
5. Queried runtime health without attaching or launching; the configured exact-build EXE was ready and no Dishonored process was running.

## Observations

- Current tree: 13,619 files totaling 15,062,334,363 bytes. The previous manifest snapshot contained 13,746 files.
- Shared paths: 13,618. One current path was absent from the previous snapshot: `Binaries/Win32/ghidra_projects/Dishonored.exe.rep/versioned/~index.bak` (63 bytes; SHA-256 `AFED071B228A87FBBB18D8BF39667792D6912C1D1AD2EA2F4F41DAC320DB8B2F`).
- Previous-only paths: 128, all under `Binaries/Win32`. These include `dinput8.dll`, the `CoopCharacterPreviews` directory, and Ghidra backup/lock files. No file from `_excluded_coop_project/` was included.
- One shared Ghidra artifact changed: `Binaries/Win32/ghidra_projects/Dishonored.exe.rep/idata/~index.bak` changed from 63 bytes / SHA-256 `AFED071B228A87FBBB18D8BF39667792D6912C1D1AD2EA2F4F41DAC320DB8B2F` to 115 bytes / SHA-256 `86C7A3DD88FF73297D2B8E5409DB5ED775F2B3B40A8A629D452BD0E29ECCE41C`.
- The EXE still has the recorded build SHA-256. There are 904 `.upk` files in the full installation and 470 in CookedPCConsole. The package index contains exactly those 470 CookedPCConsole paths; all 470 sizes and SHA-256 values match, with no missing or extra rows.
- Runtime health reported `process_running=false`; no live DLL/module baseline or behavior trace was collected.

## Interpretation / claims

- **Confirmed:** the previous full-tree inventory no longer describes the current game directory. The regenerated manifest is authoritative for this workspace snapshot.
- **Confirmed:** the executable identity and CookedPCConsole package index remain consistent with the recorded build/package evidence.
- **Observed:** the 128 absent paths and the newly changed/created paths are Ghidra or other `Binaries/Win32` artifacts, including the previously noted `dinput8.dll` and co-op preview files. This does not establish who removed them, why they changed, or that every remaining installed file is an unmodified depot file.
- **Unknown:** whether the current DLL set constitutes a clean runtime baseline. There was no running process to inspect; directory inventory alone does not establish runtime-loaded modules.

## Reproduction and limitations

- Regenerate with the command in Procedure 2, then compare the resulting CSV with a separately retained prior snapshot.
- Recompute package hashes from the local CookedPCConsole directory and compare against `assets/manifests/packages.csv`.
- The deleted files are not available from the current game tree; this record describes their prior manifest metadata only.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior differential snapshot: [EXP-0005](EXP-0005-manifest-diff.md)
- Package inventory: [EXP-0011](EXP-0011-cookedpcconsole-inventory.md)
- Runtime binding: [EXP-0016](EXP-0016-runtime-mcp-executable-binding.md)
- Status: [research-status.md](../docs/research-status.md)
