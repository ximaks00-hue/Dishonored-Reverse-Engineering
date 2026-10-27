---
id: EXP-0114
title: Config path declaration candidates against the exact install tree
experiment_status: done
claim_status: observed
build: "10256413"
question: Which path-like values from the EXP-0063 config lexer can be syntactically normalized to present files or directories in the recorded install tree under explicit candidate bases?
---

# EXP-0114 — Config path declaration candidates against the exact install tree

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: take the 76 config directive rows extracted by EXP-0063, select file/directory-shaped `BasedOn` and `*Path(s)` values, normalize candidate strings against four explicitly named roots, and check exact current file/directory presence plus manifest entries.
- Exclusions: no claim about Unreal config inheritance rules, path-resolution order, loaded config subset, generated/editor paths, or runtime dependencies. The `%GAME%` substitution is recorded as a candidate normalization only.
- Inputs: EXP-0063 [config directive catalog](../research/builds/BUILD-STEAM-10256413/config-path-directives.csv), saved file [manifest](../research/builds/BUILD-STEAM-10256413/files.csv), and [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Durable outputs: [per-declaration candidate audit](../research/builds/BUILD-STEAM-10256413/config-path-candidate-audit.csv) and [count summary](../research/builds/BUILD-STEAM-10256413/config-path-candidate-audit.json).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify build 10256413 and the recorded executable SHA-256.
2. Select file-like `BasedOn` declarations and path-like `*Path`/`*Paths` assignments from the 76 EXP-0063 rows. Exclude class-name values ending in `ClassPath` and section-name `BasedOn` values such as `SystemSettings`.
3. Normalize each value under `source_directory`, `install_root`, `game_root` (`DishonoredGame`), and `engine_root` (`Engine`). For `%GAME%`, retain the raw value and label the substitution to `Dishonored` as a candidate only. Keep rooted/wildcard/out-of-root values unresolved rather than coercing them to local paths.
4. Check each normalized in-root candidate against the current install tree and saved manifest. Do not infer load behavior from presence.
5. Run `python tools/config_path_candidate_audit.py` to verify the build executable hash and regenerate both outputs.

## Observations

- The EXP-0063 input has 76 directive rows. The filter retained 63 candidates: 10 `BasedOn` file candidates and 53 path-value candidates. Two `ClassPath` values, section-like `BasedOn` values, and non-path values were not treated as filesystem targets.
- Under either the `game_root` or `engine_root` basis, the same 10 candidates resolve to existing files recorded in the manifest. They are the nine game `BasedOn` rows pointing at Engine base INI files plus the repeated `DefaultEngine.ini` reference in the `.startinmenu.bak` file; these two bases produce the same normalized `Engine/Config/Base*.ini` targets for these values and therefore are not distinguished by the match.
- Under the `source_directory` basis, four rows resolve to existing directories: the game `Localization` directory in `DefaultEngine.ini` and its backup, and the Engine `Localization` directory in `BaseEngine.ini` and its line-feed backup. Each corresponding directory contains manifest-listed localization files (3,282 game files or 60 Engine files).
- Under the `source_directory` basis, one candidate normalizes outside the install root (`LinkedProjectOriginalPath`); two values are rooted `/Web` candidates and were left unresolved. The remaining candidates did not map to existing files/directories under that base. Several values include generated/editor-oriented or platform-template paths; their absence in this local tree does not establish a configuration error.
- The tool confirms the current `Dishonored.exe` hash matches both the build record and its manifest row before generating outputs.

## Interpretation and claim limits

- **Observed:** the exact install snapshot contains the ten Engine base INI files named by game `BasedOn` values under both `game_root` and `engine_root` candidate normalizations; this does not identify which base the engine uses. The four localization declarations, including the two backup copies, normalize from their source directories to present localization trees.
- **Unknown:** whether these candidate bases match the engine's actual resolution rules; which of the declarations the game reads; whether absent paths are generated, platform-conditional, virtual, or editor-only; and any dependency edge from a config declaration to runtime-loaded content.
- **Limit:** the result is a syntactic path-candidate/presence audit against one recorded build tree. It is not runtime tracing or a general Unreal Engine config parser.

## Reproduction

From the repository root:

```powershell
python tools/config_path_candidate_audit.py `
  --game-root "Dishonored RHCP" `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --config-directives research/builds/BUILD-STEAM-10256413/config-path-directives.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --output research/builds/BUILD-STEAM-10256413/config-path-candidate-audit.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/config-path-candidate-audit.json
```

## Links

- [EXP-0063 config/localization lexer and directive extraction](EXP-0063-install-file-family-and-text-resource-profile.md)
- [Project completion contract](../docs/roadmap.md)
- [Candidate audit tool](../tools/config_path_candidate_audit.py)
