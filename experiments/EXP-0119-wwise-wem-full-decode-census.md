---
id: EXP-0119
title: Full embedded WEM decode census
experiment_status: done
claim_status: observed
build: "10256413"
question: Can all embedded WEM ranges in the EXP-0065 PCK catalog be read from hash-verified PCKs and decoded by vgmstream?
---

# EXP-0119 — Full embedded WEM decode census

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: verify all PCK inputs and the bounds/non-overlap of every EXP-0065 embedded-entry range; temporarily copy each catalogued WEM byte range to a `.wem` file, decode the stream once with vgmstream, and remove the temporary file.
- Exclusions: no retained media extraction, perceptual quality or synchronization review, Wwise event-to-payload semantic claim, independent reparse of the PCK table, or runtime playback observation.
- Tools: vgmstream CLI r2023, binary SHA-256 `0EE2626CD5D470CCE5980AB010D36B08F9C97C9480E56BBACEB11475628232FF`; Python 3.
- Durable outputs: [per-entry decode catalog](../research/builds/BUILD-STEAM-10256413/wwise-wem-decode-audit.csv), [summary](../research/builds/BUILD-STEAM-10256413/wwise-wem-decode-summary.json), and [reproduction tool](../tools/wwise_wem_decode_audit.py).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify the build 10256413 executable SHA-256.
2. Read the 2,411 embedded-entry rows captured by EXP-0065. Verify all 503 source PCK paths match the build manifest and current size/SHA-256.
3. Check each saved entry offset/size against its source PCK size and count overlaps among all entry ranges. Select the 1,908 `.wem` rows.
4. For each WEM, read exactly the captured byte range, write it to a unique temporary `.wem` under `.tmp`, hash the extracted bytes, run `vgmstream-cli -O -i`, capture the exit code/log, and remove that temporary file.
5. Run `python tools/wwise_wem_decode_audit.py` to regenerate the CSV/JSON and verify build identity and the PCK/entry/WEM denominators.

## Observations

- The current game executable matched the build record and manifest. All 503 PCK source files matched manifest size/SHA-256; those PCKs contain 2,411 catalogued embedded-entry rows.
- Every catalogued entry range was in bounds; no overlaps were found among the 2,411 ranges.
- The catalog contains 1,908 WEM entries across 194 PCK files, totaling 1,534,189,108 bytes. The smallest entry is 8,023 bytes and the largest is 10,599,650 bytes.
- vgmstream CLI r2023 returned exit code 0 for all 1,908 WEM entries with `-O -i`; no timeouts or decode errors were recorded. The extracted WEM byte total for successful entries is 1,534,189,108 bytes.
- Each temporary payload file was removed after decode; no WEM output corpus was retained.

## Interpretation and claim limits

- **Observed:** all catalogued WEM byte ranges in the exact hash-verified PCK sources were in bounds and accepted by vgmstream's decode path when played once with loop metadata ignored.
- **Inferred, limited:** the captured entry offsets/sizes form a useful index for decoder-accessible WEM payload candidates in this install. This does not independently validate how QuickBMS found the ranges.
- **Unknown:** perceptual correctness, event/name-to-WEM identity, whether each decoded payload is used by a particular HIRC path, and runtime bank/track selection.
- **Limit:** input ranges derive from the EXP-0065 QuickBMS list-only output. Hashes and bounds establish source identity and range safety, but there was no independent parser comparison for the PCK table.

## Reproduction

```powershell
python tools/wwise_wem_decode_audit.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --pck-catalog research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --game-root "Dishonored RHCP" `
  --output research/builds/BUILD-STEAM-10256413/wwise-wem-decode-audit.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/wwise-wem-decode-summary.json `
  --jobs 2
```

## Links

- [EXP-0065 PCK entry census](EXP-0065-wwise-pck-and-bink-media-census.md)
- [PCK entry catalog](../research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv)
- [EXP-0077 Wwise bank/HIRC census](EXP-0077-wwise-bank-hirc-and-media-link-census.md)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [Decode audit tool](../tools/wwise_wem_decode_audit.py)
