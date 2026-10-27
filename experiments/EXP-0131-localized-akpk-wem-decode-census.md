---
id: EXP-0131
title: WEM payload decode audit for AKPK extension cohort
experiment_status: done
claim_status: mixed
build: "10256413"
question: Can every distinct WEM byte payload indexed from the EXP-0130 CookedPC/DLC AKPK cohort be read and decoded by vgmstream after exact-build source and range checks?
---

# EXP-0131 — WEM payload decode audit for AKPK extension cohort

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: Can every distinct WEM byte payload indexed from the EXP-0130 CookedPC/DLC AKPK cohort be read and decoded by vgmstream after exact-build source and range checks?
- Scope and exclusions: All sound-section rows in the 4,056 nonempty AKPK containers from EXP-0130; current EXE and source-file hashes, entry bounds/nonoverlap, payload SHA-256 deduplication, and full vgmstream `-O -i` decode once per distinct byte payload. No perceptual evaluation, HIRC/event-to-WEM interpretation, locale-selection rule, or runtime playback claim.
- Prerequisites / starting state: Build 10256413 executable SHA-256 checked against the build record and full-tree manifest. Every AKPK source used was rehashed and matched both the manifest and EXP-0130 package catalog.
- Tools and versions: Python 3 standard library; vgmstream CLI r2023, binary SHA-256 `0EE2626CD5D470CCE5980AB010D36B08F9C97C9480E56BBACEB11475628232FF`; EXP-0130 AKPK entry catalog.
- Durable outputs: [unique-payload decoder results](../research/builds/BUILD-STEAM-10256413/wwise-localized-wem-decode-unique.csv), [12,112 occurrence-to-payload mapping](../research/builds/BUILD-STEAM-10256413/wwise-localized-wem-decode-occurrences.csv), [summary](../research/builds/BUILD-STEAM-10256413/wwise-localized-wem-decode-summary.json), and [reproduction tool](../tools/wwise_localized_wem_decode_audit.py).

## Procedure

1. Verify the current executable against build record and manifest; verify all manifest-listed AKPK sources referenced by entries against their recorded size and SHA-256.
2. Validate every entry row range against its containing AKPK file and count overlaps.
3. For all 12,112 sound entries, read exact byte ranges, require the observed `RIFF` marker, and compute SHA-256. Deduplicate decoder jobs by `(SHA-256, byte size)` while retaining every occurrence mapping.
4. For one representative range per distinct payload, write a temporary `.wem` file under ignored `.tmp`, invoke vgmstream with `-O -i`, capture result/log, and remove the temporary file.
5. Save one decoder row per unique payload and map all source occurrences to the decoder status for their exact payload hash.

## Observations

- The current Dishonored executable matched build 10256413 and its manifest SHA-256. All 4,056 nonempty AKPK source files referenced by entries matched both the full-tree manifest and the EXP-0130 package catalog by size and SHA-256.
- The 16,168 entry ranges had zero out-of-bounds ranges and zero overlapping range pairs. The 12,112 sound ranges total 2,226,354,383 bytes and each begins with the observed `RIFF` marker.
- Those 12,112 sound ranges contain 7,213 distinct `(SHA-256, byte size)` payloads totaling 1,320,837,434 bytes. Every occurrence maps to one of those exact content keys.
- vgmstream r2023 returned exit code 0 for all 7,213 distinct payloads with `-O -i`; there were no decoder failures, timeouts, or read/launch errors. The occurrence catalog maps all 12,112 sound rows to `decoded`.
- Each temporary `.wem` file was removed after its decoder call; a post-run check found no `localized_wem_*.wem` temporary files. No extracted payload corpus was retained.
- The AKPK table offsets come from the EXP-0130 parser. This decode audit independently checks that the resulting sound byte ranges are accepted as complete decodable WEM streams, but does not independently validate the AKPK table parser against QuickBMS for this extension cohort.

## Interpretation

- **Observed:** all 7,213 distinct WEM byte payloads indexed by the EXP-0130 sound rows were accepted by vgmstream's decode path, and every one of the 12,112 catalogued occurrences maps to a successfully decoded content hash.
- **Observed:** source hashes, entry ranges, payload markers, and decoder outcomes reconcile for the named build's current local files.
- **Inferred, limited:** this supplies strong payload-level corroboration for the EXP-0130 offsets and sizes. It is not a separate table parser comparison; a consistently wrong table could still point to a different but decodable RIFF stream.
- **Unknown:** perceptual correctness, HIRC semantics, event/bank/media identity, extension-based locale policy, runtime file loading, and selection in a particular game state.
- Confidence: High for hash, range, deduplication, and decoder exit coverage; no perceptual/runtime claim.
- Alternative explanations: A vgmstream decode success proves the byte stream is supported by this decoder, not that Dishonored's middleware uses or renders it as expected.
- Evidence that would falsify this interpretation: A changed source hash/manifest, a corrected AKPK range table, or a rerun where the same payload keys fail the recorded decoder path.

## Reproduction

```powershell
python tools/wwise_localized_wem_decode_audit.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --game-root "Dishonored RHCP" `
  --packages research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-packages.csv `
  --entries research/builds/BUILD-STEAM-10256413/wwise-localized-akpk-entries.csv `
  --decoded-output research/builds/BUILD-STEAM-10256413/wwise-localized-wem-decode-unique.csv `
  --occurrences-output research/builds/BUILD-STEAM-10256413/wwise-localized-wem-decode-occurrences.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/wwise-localized-wem-decode-summary.json `
  --jobs 2
```

## Links

- Build: `research/builds/BUILD-STEAM-10256413/build.md`
- Related experiments: EXP-0065, EXP-0077–0081, EXP-0119, EXP-0130
- Open questions: Independent AKPK table cross-check and Wwise HIRC/event/runtime joins for this cohort.
