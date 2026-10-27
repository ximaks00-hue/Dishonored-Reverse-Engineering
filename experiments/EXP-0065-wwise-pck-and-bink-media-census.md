---
id: EXP-0065
title: Wwise PCK extraction table and Bink media parsing census
experiment_status: done
claim_status: observed
build: "10256413"
question: "Can compatible tools enumerate embedded entries in the installed Wwise PCK files and parse metadata from the installed Bink movies?"
---

# EXP-0065 — Wwise PCK extraction table and Bink media parsing census

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: QuickBMS list-only parsing of every manifest-listed `.pck` (311 base + 192 DLC) and FFprobe metadata parsing of all 76 `.bik` files. One embedded BNK was extracted into ignored `assets/extracted/` and inspected with vgmstream; one Bink first frame was decoded to a null sink.
- Exclusions: no game launch or modification; no audio playback; no decoding/census of every embedded WEM/BNK; no HIRC/event/name reconstruction; no movie frame-by-frame decode; no TFC/AKMAP parser; `_excluded_coop_project/` was not accessed.
- Tools: QuickBMS 0.12.0; `wwise_pck_extractor.bms` from [wwiser-utils](https://github.com/bnnm/wwiser-utils/blob/master/scripts/wwise_pck_extractor.bms), downloaded for the experiment with SHA-256 `4459C0A4C354A92DCAD335599C389E8296908BD8B38FB128BD4C505AEAEE6B5D`; FFprobe/FFmpeg 9.0.1-full_build-www.gyan.dev; vgmstream CLI r2023 (May 14 2025); Python 3 and PowerShell.

## Procedure

1. Re-read research status, Blink graph, and build record; verify the local EXE SHA-256.
2. Confirmed that QuickBMS `-0 -L` on `Bank_AI_Assassin_Mvt_Land_01.pck` lists the embedded BNK path, offset, and byte size without extraction.
3. Used a temporary Python/PowerShell driver to run QuickBMS `-0 -L` once for each of the 503 manifest-listed `.pck` paths. Parsed the listing into [wwise-pck-entry-census.csv](../research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv). The driver and mutable third-party script are retained only under ignored `.tmp/`; exact tool/script versions and script hash are recorded above. PCK inputs were not modified.
4. Ran [bink_metadata_census.py](../tools/bink_metadata_census.py) against the build manifest and game root; results are in [bink-ffprobe-census.csv](../research/builds/BUILD-STEAM-10256413/bink-ffprobe-census.csv).
5. Extracted the single BNK from the example PCK using QuickBMS into ignored `assets/extracted/wwise-pck-probe-20261027/`; used `vgmstream-cli -m` on the extracted BNK. Ran FFmpeg to decode one Credits Bink frame with `-frames:v 1 -f null -`.

Reproduction for Bink metadata:

```powershell
python tools/bink_metadata_census.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --game-root "Dishonored RHCP" `
  --output research/builds/BUILD-STEAM-10256413/bink-ffprobe-census.csv
```

The PCK entry listing used the equivalent of:

```powershell
quickbms.exe -0 -L .tmp/quickbms-pck-current-list.txt .tmp/wwise_pck_extractor.bms <full-pck-path>
```

The current CSV is the captured result; reproduce it by iterating manifest rows with extension `.pck`, running the command once per path, and parsing `offset size filename` lines. The source extractor may change on upstream `master`; compare its SHA-256 before treating a rerun as tool-identical.

## Observations

- All 503 manifest-listed PCKs (311 base, 192 DLC) returned a parseable QuickBMS listing; the batch reported zero process/listing errors.
- The catalog contains 2,411 entries: 503 `.bnk` and 1,908 `.wem`. Every PCK yielded one BNK entry; 194 packages yielded at least one additional entry. The remaining PCKs had only the BNK row.
- For `Bank_AI_Assassin_Mvt_Land_01.pck` (10,082 bytes), QuickBMS listed one BNK at offset `0x50`, size 10,002 bytes: `Bank_AI_Assassin_Mvt_Land_01/1868512052.bnk`.
- Extracted BNK metadata: 44,100 Hz, mono, 31,504 samples (0.714 s), Custom Vorbis, stream name `994398131`; vgmstream identified an Audiokinetic Wwise RIFF header.
- FFprobe parsed all 76 Bink files and all current sizes matched the manifest. All 76 expose `binkvideo`, 1280×720. Fifty have no audio stream, 12 expose one `binkaudio_dct`, and 14 expose five. Reported durations total 3,239.26772 seconds (min 0.1 s; max 550 s).
- FFmpeg decoded the first frame of `DishonoredGame/Movies/Credits.bik` to the null sink and exited successfully; no derived media file was written.
- Direct FFprobe and vgmstream attempts on PCK containers failed to parse; extraction of the sample PCK's BNK enabled the vgmstream metadata probe.

## Interpretation / claims

- **Observed:** these exact local PCK files can be enumerated by this QuickBMS script and tool combination, and the resulting catalog covers all 503 manifest paths with zero parser/listing errors.
- **Observed:** FFprobe recognizes all 76 installed Bink files sufficiently to report stream metadata, and FFmpeg decodes one sample frame.
- **Observed, sample only:** vgmstream parses the extracted example BNK's audio metadata.
- **Inferred, limited:** the PCK catalog is useful as a package-to-embedded-file index. It does not show runtime loading, decode all media payloads, or recover Wwise event/HIRC semantics.
- **Unknown:** whether every BNK/WEM payload is individually decodable, which events reference each WEM, how PCK languages/banks are selected at runtime, Bink visual/audio correctness across full playback, and relationships to UPK/config assets.
- **Not established:** complete non-UPK resource support or complete game audio/video reverse engineering.

## Reproduction and limitations

- Catalog and FFprobe outputs are per-file data, including all PCK source paths, offsets/sizes/names and Bink parse errors/stream fields.
- The temporary QuickBMS driver and extractor script are not checked in; the upstream BMS URL tracks a mutable branch, so the recorded hash is part of the procedure identity.
- List-only QuickBMS validates extraction-table interpretation by the selected script, not cryptographic integrity or semantic correctness of each embedded entry.
- The example BNK was extracted under ignored `assets/extracted/`; no game payloads should be added to Git.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior header census: [EXP-0064](EXP-0064-non-upk-resource-header-signatures.md)
- Bink census helper: [bink_metadata_census.py](../tools/bink_metadata_census.py)
- Completion scope: [roadmap](../docs/roadmap.md)
