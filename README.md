# Dishonored Reverse Engineering

An evidence-led research project for studying Dishonored on Windows, from files and UE3 packages to observed gameplay and native code.

## Research principles

- Treat each game installation as a distinct build. Record executable hashes and architecture before comparing addresses or behavior.
- Label statements as **confirmed**, **observed**, **inferred**, or **unknown**. An observed behavior does not prove a particular internal implementation.
- Keep a reproducible source for every claim: build, file and hash, tool/version, experiment, or external reference.
- Store function locations as module-relative RVAs tied to a specific binary identity. Decompiled pseudocode is a reconstruction, not original source.
- Preserve conflicting observations and explain their scope instead of silently choosing one.
- Keep copyrighted game data out of Git. Record metadata and hashes; put local extraction output under ignored paths.

## Start here

1. Read [research status](docs/research-status.md) and [evidence policy](docs/methodology/evidence.md).
2. Record the installed build using [the build template](templates/build.md). Do not assume a store version or architecture.
3. Create a repeatable experiment from [the experiment template](templates/experiment.md), or document a file/package observation.
4. Link observations to their sources and update the relevant subsystem page.

## Repository map

- `docs/` — project method, architecture, confirmed findings, and open questions.
- `experiments/` — repeatable procedures and results, identified by stable IDs.
- `schemas/` — machine-readable formats for research records.
- `templates/` — consistent starting points for builds, experiments, and subsystem pages.
- `tools/` — project-owned scripts only; third-party tools are documented, not vendored.
- `assets/` — local-only extracted data; ignored by Git.

## Current scope

This repository is at its foundation stage. No local game build has yet been recorded here, so build-specific package, class, function, address, or gameplay claims remain open until evidence is added.
