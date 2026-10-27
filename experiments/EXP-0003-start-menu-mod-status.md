---
id: EXP-0003
title: StartInMenu configuration status
experiment_status: done
claim_status: observed
build: "10256413"
question: "Does the current game configuration contain the changes described by the bundled StartInMenu installer?"
---
# EXP-0003 — StartInMenu configuration status

- Status: observed
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Question: Does the current game configuration contain the changes described by the bundled StartInMenu installer?
- Tools: read-only inspection of `Mods/StartInMenu/README.txt`, `Mods/StartInMenu/Install.ps1`, and `DishonoredGame/Config/DefaultEngine.ini`.

## Procedure

1. Read the mod README and installer as text; do not execute either installer.
2. Inspect the `[FullScreenMovie]` section of the current `DefaultEngine.ini`.
3. Compare only the documented changes: set `bForceNoStartupMovies=true` and remove `.StartupMovies` entries.

## Observations

- The mod README says the installer skips startup logo/legal/intro movies.
- The installer script edits `DefaultEngine.ini`, setting `bForceNoStartupMovies=true` and removing `.StartupMovies` entries.
- The current file has `bForceNoStartupMovies=false` and retains the startup movie entries.

## Interpretation and limits

The mod's documented configuration changes are not present in the inspected `DefaultEngine.ini`. This does not rule out other independent changes elsewhere in the installation.
