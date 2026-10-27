---
id: EXP-0136
title: Config map and package declarations joined to the install package inventory
experiment_status: done
claim_status: mixed
build: "10256413"
question: Which package and map names declared by installed Unreal configuration files have exact or explicitly variant-matched UPK filenames in the recorded install manifest?
---

# EXP-0136 — Config map and package declarations joined to the install package inventory

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: Which explicit package-list, map-name, and mission-image package references in the installed configuration corpus have corresponding exact or `_SF`-variant UPK basenames in the recorded install manifest?
- Scope and exclusions: All `.ini` files under `DishonoredGame/Config`, `Engine/Config`, and `DishonoredGame/DLC/PCConsole` in the current exact-build manifest; selected `Package`, `SeekFreePackage`, startup-package, map-name, and mission-image package-property assignments; all 904 installed UPK basenames. Candidate name matching is syntactic. It does not establish config parser merge rules, declaration consumption, package resolution order, runtime load, or object identity for bare mission-image names.
- Prerequisites / starting state: Build 10256413 executable SHA-256 matches the build record and manifest. All 46 selected config files were size/SHA-256 checked against the manifest. UPK names are taken from the 904-file manifest and package inventory.
- Tools and versions: Python 3 standard library; current `files.csv`; current config text files.
- Durable outputs: `research/builds/BUILD-STEAM-10256413/config-map-package-candidates.csv`, `config-map-package-candidates-config-sources.csv`, and `config-map-package-candidates-summary.json`; reproducible parser: `tools/config_map_package_candidate_audit.py`.

## Procedure

1. Verify the exact executable identity and rehash every selected INI source against the build manifest.
2. Select all 904 manifest-listed UPKs and index their filename stems case-insensitively, preserving duplicate paths.
3. Parse line-oriented INI assignments while retaining source path, line, section, key, and raw value. Extract only declared package-list keys, package-suffixed object properties, URL map targets, `m_MapsToBarkProfile`, `m_MapHintBindings` map fields, and `m_MissionImages` values.
4. Join package/map names first by exact UPK basename. Report a separate candidate set for the observed name-plus-`_SF` filename variant; do not merge those statuses or infer runtime loading. For dotted object references, use only the prefix before the dot as a package-name candidate. Keep bare object names unresolved by package basename.
5. Emit one provenance row per source declaration and a summary with exact, variant, ambiguous, and unresolved counts.

## Observations

- Build 10256413 executable SHA-256 and inventory SHA-256 matched the build record and manifest. All 46 scoped INIs matched manifest size and SHA-256; the UPK denominator was 904 rows and 891 distinct case-insensitive basenames.
- The parser emitted 448 source-reference rows: 29 configured map names, 8 dotted object references, 76 map-hint names, 9 bare mission-image objects, 14 mission-image package/object references, 299 package-list declarations, 7 package properties, and 6 URL map targets.
- Across all kinds, 127 rows had a unique exact basename match and 11 had ambiguous exact matches. Another 260 rows had one `_SF`-suffixed candidate and 3 had ambiguous `_SF` candidates; exact and `_SF` groups overlap in none of the summary status rows. 38 named references had no UPK basename candidate and 9 bare mission-image object names lacked a package candidate by construction.
- Within map-specific rows, 24 configured map names had exact basename matches, and 74 of 76 map-hint names had exact basename candidates (two did not: `Default` and `L_Outro_P`). Five configured bark-profile map names had no exact candidate. URL map targets comprised three exact `DishonoredGameFull_P` rows and three unresolved `Entry` rows.
- The 299 package-list declarations yielded 14 exact basename rows, 256 `_SF` candidate rows, 22 with no basename candidate, four ambiguous exact rows, and three ambiguous `_SF` rows. The counts are declaration rows, not unique package names.
- Candidate-path records include each matched UPK's manifest path, byte size, and SHA-256 so duplicate basenames remain distinguishable.

## Interpretation

- - Finding and status: **Observed** — the installed configuration corpus contains the listed map/package names and the recorded filename joins. **Unknown** — whether engine config merging consumes a declaration, resolves its package, loads it, or resolves a bare object name.
- Confidence and rationale: High for the syntactic inventory and filename candidates because all source INIs were rehashed against the exact-build manifest and every candidate carries its manifest identity. The `_SF` relationship is reported only as a naming candidate.
- Alternative explanations: Duplicate basenames can refer to different package paths; config inheritance, platform-specific overrides, path search, generated packages, or runtime behavior may affect resolution beyond this static join.
- Evidence that would change the unknowns: build-matched engine config-consumption traces, package-load observations, or package/object reference evidence that links the bare mission-image names.

## Reproduction

- Reset/cleanup steps: None; outputs are deterministic derived catalogs and may be regenerated in place.
- Repeat count and variation: One complete run over all 46 selected INIs and 904 UPK manifest rows. Repeated source verification occurs on each invocation.
- Known sources of variance: A changed install/manifest, text encoding, or edits to the parser's deliberately narrow line-oriented extraction rules.
- Command: `python tools/config_map_package_candidate_audit.py`.
- Output detail: CSV contains source SHA-256, path/line/section/key, raw declaration, exact and `_SF` candidate path arrays, and candidate path/size/SHA-256 tuples. JSON records denominators, status counts, manifest hash, and limits.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related experiments: [EXP-0063 config/localization profile](EXP-0063-install-file-family-and-text-resource-profile.md), [EXP-0114 config path candidate audit](EXP-0114-config-path-candidate-audit.md), [EXP-0121 refreshed install manifest](EXP-0121-current-install-inventory-refresh.md)
- Open questions: Config consumption and merge behavior; package resolution and runtime loading; object lookup for bare mission-image names; map/package dependencies established from serialized package references or runtime traces.
