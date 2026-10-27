---
id: EXP-0118
title: Full-stream Bink decode census
experiment_status: done
claim_status: observed
build: "10256413"
question: Can FFmpeg decode every mapped video and audio stream in all manifest-listed Bink files to completion?
---

# EXP-0118 — Full-stream Bink decode census

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: run FFmpeg to decode the first video stream and every optional audio stream in each of the 76 manifest-listed `.bik` files, writing to the null muxer; capture per-file exit status, elapsed time, and decoder error text.
- Exclusions: no rendered frame or audio quality review, no semantic verification of tracks, no test of the game's movie/track selection, no file output, and no game launch.
- Tools: FFmpeg `9.0.1-full_build-www.gyan.dev`, binary SHA-256 `57C56E369D5B4873B4D93FC1A1D833CB7CD8BC9325C14B05C34CE60B22842D8A`.
- Durable outputs: [per-file decode results](../research/builds/BUILD-STEAM-10256413/bink-full-decode-audit.csv), [summary](../research/builds/BUILD-STEAM-10256413/bink-full-decode-summary.json), and [reproduction tool](../tools/bink_full_decode_audit.py).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify build 10256413 and the current executable SHA-256.
2. Select all `.bik` rows from the build manifest. Require 76 paths and verify each current file's size and SHA-256 against the manifest before decoding.
3. Record FFmpeg version and binary SHA-256. Decode with `-v error -xerror -threads 1`, mapping `0:v:0` and all optional `0:a?` streams to `-f null -`.
4. Run at most two files concurrently; preserve the per-file exit code, timeout, elapsed time, and stderr in the output catalog.
5. Run `python tools/bink_full_decode_audit.py` to regenerate the CSV and JSON. The tool verifies the build executable and all Bink input hashes/sizes and asserts the 76-file denominator.

## Observations

- The current FFmpeg binary reports version `9.0.1-full_build-www.gyan.dev` and SHA-256 `57C56E369D5B4873B4D93FC1A1D833CB7CD8BC9325C14B05C34CE60B22842D8A`.
- All 76 manifest-listed Bink inputs matched their recorded size and SHA-256 before decode. Their manifest sizes sum to 1,954,620,912 bytes.
- FFmpeg returned exit code 0 for all 76 files while mapping the first video stream and every optional audio stream to the null muxer. There were zero timeouts and zero nonzero exit codes; the output catalog contains no decode error text.
- The mapped streams covered 1,954,620,912 input bytes. No media output file was written.
- EXP-0065's metadata census reports one Bink video stream per file; it reports no audio stream in 50 files, one in 12 files, and five in 14 files. The `0:a?` mapping therefore includes the complete audio-stream cohort reported by that census.

## Interpretation and claim limits

- **Observed:** this exact FFmpeg build decodes the mapped Bink video/audio streams of all 76 current manifest files to completion without reporting a decode failure.
- **Unknown:** decoded audiovisual quality, whether each track is semantically correct or synchronized, and which tracks or files the game selects in each context.
- **Limit:** successful decoder completion is compatibility evidence for these files and this FFmpeg build. It is not proof of visual/audio correctness or game-runtime use.

## Reproduction

```powershell
python tools/bink_full_decode_audit.py `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --game-root "Dishonored RHCP" `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --output research/builds/BUILD-STEAM-10256413/bink-full-decode-audit.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/bink-full-decode-summary.json `
  --jobs 2
```

## Links

- [EXP-0065 PCK and Bink metadata census](EXP-0065-wwise-pck-and-bink-media-census.md)
- [Bink metadata catalog](../research/builds/BUILD-STEAM-10256413/bink-ffprobe-census.csv)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [Decode audit tool](../tools/bink_full_decode_audit.py)
