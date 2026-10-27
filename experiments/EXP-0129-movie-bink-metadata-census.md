---
id: EXP-0129
title: Bink movie metadata and text-sidecar census
experiment_status: done
claim_status: mixed
build: "10256413"
question: What Bink metadata and same-stem text sidecars can be measured across the installed Movies directories?
---

# EXP-0129 — Bink movie metadata and text-sidecar census

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: What Bink metadata and same-stem text sidecars can be measured across the installed Movies directories?
- Scope and exclusions: Inventory-driven metadata probing of all 76 `.bik` files and structural profiling of all 14 `.txt` files under movie paths. No full video/audio decode, perceptual validation, translation inspection, game playback, or proof of runtime reference is included.
- Prerequisites / starting state: Re-read research status, Blink graph, and build record; build 10256413 executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Tools and versions: Python 3 standard library; FFprobe 9.0.1 (`-show_entries` metadata probe); exact-build file manifest `research/builds/BUILD-STEAM-10256413/files.csv`.
- Durable outputs: [76-row Bink metadata probe](../research/builds/BUILD-STEAM-10256413/movie-bink-probe.csv), [14-row text cue profile](../research/builds/BUILD-STEAM-10256413/movie-subtitle-cue-profile.csv), and [reproduction tool](../tools/movie_bink_probe.py).

## Procedure

1. Select every manifest path under a `Movies` directory; do not infer coverage from one sample directory.
2. For each `.bik`, record four-byte magic, actual/manifest size, and FFprobe format/stream metadata. Compare FFprobe-reported format size to the manifest and local file size.
3. For each `.txt`, parse the first line as a retained raw header pair, then count later rows with three comma-separated fields and integer first and second fields. Match candidate sidecars by same-directory, same-stem `.bik` path.
4. Save both per-file catalogs and summarize failures and coverage without assigning time-unit or runtime semantics to text fields.

## Observations

- The current 13,623-file manifest contains 90 movie-path files totaling 1,954,624,540 bytes: 76 `.bik` and 14 `.txt` files.
- FFprobe returned successfully for all 76 `.bik` files. Each begins with the four bytes `BIKi`; FFprobe reports format `bink`, one `binkvideo` stream, and dimensions 1280×720. For all 76 files, manifest size, local size, and FFprobe-reported format size agree.
- The reported audio-stream count is 0 for 50 files, 1 for 12 files, and 5 for 14 files. Where present, the stream labels include `binkaudio_dct`; no audio payload was decoded or listened to.
- Reported duration ranges from 0.1 to 550 seconds. This is container metadata, not a completed playback or frame-integrity test.
- All 14 `.txt` files have an exact same-directory, same-stem `.bik` candidate in the manifest. Their first raw line is `1000,0`; the remaining 94 rows have three comma-separated fields with integer first and second fields and no malformed rows under this parser.
- One text sidecar, `DLC06_Monologue_Rothwild_LOC.txt`, has a maximum second numeric field of `105400`, while its paired Bink metadata reports 65.999934 seconds. If that field is interpreted as milliseconds, it exceeds the reported duration; the field's units, origin, and offset behavior were not established, so this is retained as an unresolved candidate discrepancy.

## Interpretation

- **Observed:** the local FFprobe metadata probe accepted all 76 installed `.bik` files and reported consistent file-size values; the probe exposes a uniform 1280×720 `binkvideo` stream and the listed audio-stream count distribution.
- **Observed:** all 14 text sidecars pair lexically with same-stem Bink paths and contain 94 structurally parseable three-field rows after a common first line.
- **Inferred, limited:** the same-stem text files are associated sidecars for the matching movie files. This is a filename/path relation, not a confirmed engine dependency or proof the game loads them together.
- **Unknown:** full media decode integrity, meaning and units of the text fields, language selection, cue-to-audio timing, playback callsites, and runtime asset selection.
- Confidence: High for manifest and FFprobe metadata counts; medium for lexical sidecar pairing; no runtime or perceptual claims.
- Alternative explanations: Text sidecars may be consumed by a subsystem or pipeline other than Bink playback, and same-stem naming alone does not prove the consumer relation.
- Evidence that would falsify this interpretation: A regenerated manifest that changes file scope, or a successful independent parser showing that the listed files do not contain the recorded Bink/text structures.

## Reproduction

From repository root with FFprobe 9.0.1 available on `PATH`:

```powershell
python tools/movie_bink_probe.py "Dishonored RHCP"
```

The script reads manifest-listed movie paths under the supplied install root and rewrites the two CSV outputs. It does not modify game files.

## Links

- Build: `research/builds/BUILD-STEAM-10256413/build.md`
- Files/functions/objects: 76 `.bik` media files and 14 `.txt` sidecars under `Movies`
- Related experiments: EXP-0063, EXP-0121
- Open questions: Bink decode coverage, subtitle field semantics, and runtime movie/sidecar references.
