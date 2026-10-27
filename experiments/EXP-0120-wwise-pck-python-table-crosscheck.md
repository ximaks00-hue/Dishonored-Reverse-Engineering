---
id: EXP-0120
title: Wwise PCK Python table cross-check
experiment_status: done
claim_status: observed
build: "10256413"
question: Does a separate Python implementation of the AKPK section tables reproduce the QuickBMS catalog for every installed PCK entry?
---

# EXP-0120 — Wwise PCK Python table cross-check

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: independently implement the AKPK header, language table, bank/sound entry tables, block-offset rule, and embedded names in Python; compare every parsed source path, entry offset, entry size, and embedded name against the EXP-0065 QuickBMS catalog.
- Exclusions: no independent vendor specification, no Wwise event semantic claim, no decode quality or runtime playback inference, and no game launch.
- Inputs: all 503 manifest-listed PCK files and their recorded hashes; the 2,411-row catalog from EXP-0065. The pinned `wwise_pck_extractor.bms` hash recorded there is `4459C0A4C354A92DCAD335599C389E8296908BD8B38FB128BD4C505AEAEE6B5D` and was rechecked in the local retained file before this comparison.
- Durable outputs: [per-entry Python parser rows](../research/builds/BUILD-STEAM-10256413/wwise-pck-python-parser-entries.csv), [per-package summary](../research/builds/BUILD-STEAM-10256413/wwise-pck-python-parser-packages.csv), [aggregate summary](../research/builds/BUILD-STEAM-10256413/wwise-pck-python-parser-summary.json), and [parser tool](../tools/wwise_pck_table_crosscheck.py).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify the exact build ID and current executable SHA-256.
2. Check the retained QuickBMS script hash against EXP-0065. Load the full PCK entry catalog and reconcile its 503 source paths / 2,411 rows with the build manifest.
3. Hash all current PCK files. Parse each raw `AKPK` file's little-endian header, optional external-section size, relative language-name entries, bank and sound sections, 20/24-byte row layout, bank block-size offset rule, and bank version without calling QuickBMS.
4. Compare the generated path, offset, size, and entry name as a multiset against the saved QuickBMS catalog. Also check that table parsing ends no later than the first payload and that parsed payload ranges do not overlap.
5. Run `python tools/wwise_pck_table_crosscheck.py` to regenerate all three catalogs and assert the 503 / 2,411 denominators and exact comparison.

## Observations

- The current executable matched the build record and manifest. All 503 current PCK files matched their manifest size and SHA-256.
- The Python parser emitted 2,411 entry rows: 503 bank rows and 1,908 sound rows. All parsed bank versions were `65`; all 503 bank rows and 1,908 sound rows used 20-byte table entries. No external-section entries occurred in this corpus.
- The parsed headers cover 37 distinct header/section-size tuples, all with flag value `1` and a 4-byte external-section size field.
- All 2,411 Python rows exactly match the QuickBMS catalog on source PCK path, byte offset, byte size, and embedded name. There are zero missing rows, extra rows, or package parse errors.
- For every PCK, the parsed tables end at or before the first payload byte. None of the 2,411 payload ranges overlaps another parsed entry range.
- The second implementation reproduced the WEM-containing ranges used by EXP-0119; it did not write or retain any game payloads.

## Interpretation and claim limits

- **Observed:** the separate Python implementation reproduces the captured QuickBMS catalog exactly across all 503 current PCKs and all 2,411 bank/sound entries.
- **Inferred, limited:** agreement on names, offsets, and sizes from hash-verified source files increases confidence in this install's extracted PCK entry index. This is an implementation cross-check, not an independent vendor specification: the Python table layout was informed by the pinned QuickBMS script.
- **Unknown:** whether the listed banks and WEMs are loaded or played in any specific game state, whether event-to-payload links express semantic identity, and whether decoded audio is perceptually correct.
- **Limit:** the comparison validates the table/index interpretation used here. It does not independently validate QuickBMS itself against a vendor-supplied PCK specification or trace game runtime selection.

## Reproduction

```powershell
python tools/wwise_pck_table_crosscheck.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --pck-catalog research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --game-root "Dishonored RHCP" `
  --entries-output research/builds/BUILD-STEAM-10256413/wwise-pck-python-parser-entries.csv `
  --packages-output research/builds/BUILD-STEAM-10256413/wwise-pck-python-parser-packages.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/wwise-pck-python-parser-summary.json
```

## Links

- [EXP-0065 PCK entry census procedure and source script provenance](EXP-0065-wwise-pck-and-bink-media-census.md)
- [EXP-0119 full WEM decode census](EXP-0119-wwise-wem-full-decode-census.md)
- [PCK entry catalog](../research/builds/BUILD-STEAM-10256413/wwise-pck-entry-census.csv)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [Python parser tool](../tools/wwise_pck_table_crosscheck.py)
