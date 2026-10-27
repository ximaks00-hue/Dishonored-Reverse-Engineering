# Baseline inventory findings

Build: [BUILD-STEAM-10256413](../../research/builds/BUILD-STEAM-10256413/build.md).

## Confirmed

- Local EXE SHA-256 matches Steam app `217980`, build `10256413`, x86 (`EXP-0001`).
- Current workspace manifest: 13,623 files / 15,098,142,031 bytes, refreshed in EXP-0121. The previous full-tree snapshot recorded 13,619 files; its CSV is not retained, so path-level deltas are unknown. The older 13,746-file inventory and its 128 previous-only paths are documented in EXP-0001/0005/0010/0050. All 904 current UPKs (470 CookedPCConsole + 434 DLC) match the package manifest by path, size, and SHA-256 (EXP-0052/0121).
- `DishonoredGame.upk` / `Core.upk` package tag and UModel version `801/30`, engine `9411`, game `800033` (`EXP-0004`, `EXP-0006`).
- Full Ghidra auto-analysis of workspace EXE: 72,925 functions; sampled `.text` matches file bytes (`EXP-0013`).
- Compressed package: UELib/UE Explorer can read summary and names; object-table decompile needs the Gildor-decompressed copy (`EXP-0007`, `EXP-0009`).
- Earlier inventory snapshot included `dinput8.dll` and CoopCharacterPreviews files under `Binaries/Win32`; these 128 previous-only paths are absent from the current tree. Ghidra artifacts remain. The co-op project under `_excluded_coop_project/` was excluded (`EXP-0005`, `EXP-0010`, `EXP-0050`).
- StartInMenu mod present; documented ini changes absent from current `DefaultEngine.ini` (`EXP-0003`).

## Open

- Provenance/runtime role of remaining non-co-op copy-only paths.
- Clean runtime baseline (DLL set) for Stage 03 behavior experiments. The current tree has no `dinput8.dll`, but no process was running for loaded-module inspection (`EXP-0016`, `EXP-0050`).
- Language/DLC completeness without filename-only inference.
