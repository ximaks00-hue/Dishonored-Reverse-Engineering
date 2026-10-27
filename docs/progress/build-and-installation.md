# Build and installation baseline

**Status: established for one recorded local snapshot.** The evidence identifies a specific executable and inventories the corresponding local installation. It does not certify every installed file as an untouched Steam depot file.

## What is recorded

- Steam app `217980`, build `10256413`, x86 `Dishonored.exe`, size 18,041,856 bytes; SHA-256: `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`. See the [build record](../../research/builds/BUILD-STEAM-10256413/build.md).
- The 2026-10-27 full-tree snapshot contains 13,623 paths / 15,098,142,031 bytes. The path-level difference from the prior snapshot cannot be reconstructed because the older manifest is absent from Git history (EXP-0121).
- All 904 installed UPKs (470 CookedPCConsole and 434 DLC) match the recorded package manifest by path, size, and SHA-256 (EXP-0011, EXP-0052, EXP-0121).

## Boundaries and open work

The install contains `Mods/StartInMenu` and `StartInMenu-Mod.zip`. The build record notes that the documented installer changes are not present in the current `DefaultEngine.ini` (EXP-0003). The executable hash pins the binary identity; it does not prove that all config, mod, or resource files are stock.

No general claim is made that all files were freshly rehashed in the same experiment: EXP-0121 refreshes the full inventory, while EXP-0063 revalidates scoped Config/Localization and selected DVR/Ghidra paths. A future clean-install comparison would need its own manifest and provenance.

## Useful next work

- Compare an unmodified installation against this recorded snapshot, preserving path/size/hash evidence.
- For any runtime experiment, record the exact executable SHA, relevant config/mod state, and a repeatable baseline.
- Keep game binaries, installs, saves, and extracted assets outside Git.

## Sources

[Build record](../../research/builds/BUILD-STEAM-10256413/build.md) · [EXP-0001](../../experiments/EXP-0001-build-inventory.md) · [EXP-0003](../../experiments/EXP-0003-start-menu-mod-status.md) · [EXP-0011](../../experiments/EXP-0011-cookedpcconsole-inventory.md) · [EXP-0052](../../experiments/EXP-0052-installed-dlc-package-inventory.md) · [EXP-0121](../../experiments/EXP-0121-full-install-inventory-refresh.md)
