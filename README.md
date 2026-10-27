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

1. Read [research status](docs/research-status.md), [evidence policy](docs/methodology/evidence.md), and [AGENTS.md](AGENTS.md) if you are an automated assistant.
2. Record the installed build using [the build template](templates/build.md). Do not assume a store version or architecture.
3. Create a repeatable experiment from [the experiment template](templates/experiment.md), or document a file/package observation.
4. Link observations to their sources; update [findings](docs/findings/README.md) or the subsystem page for confirmed bullets only.
5. Run `python tools/validate_experiments.py` before treating the session as closed. Experiment YAML uses `experiment_status` + `claim_status` (see [AGENTS.md](AGENTS.md)).

## Repository map

- `docs/` — method, architecture, findings, tooling notes, and short status.
- `docs/findings/` — durable confirmed summaries (not session narrative).
- `docs/gameplay/blink/activation-graph.md` — Blink evidence edges.
- `experiments/` — repeatable procedures and results, identified by stable IDs.
- `schemas/` — machine-readable formats for research records.
- `templates/` — consistent starting points for builds, experiments, and subsystem pages.
- `tools/` — project-owned scripts (`validate_experiments`, knowledge sync, inventory).
- `mcp_servers/` — workspace MCP servers; shared defaults in `mcp_servers/_paths.py`.
- [UE Explorer MCP](tools/ueexplorer-mcp/README.md) — read-only MCP access to UE3 package metadata and UnrealScript.
- `assets/` — local-only extracted data; ignored by Git.
- `third_party/` — local tool installs; binaries are gitignored (see [tooling/mcp.md](docs/tooling/mcp.md)).

## Current scope

The audited research corpus on `codex/research-corpus-sync` (EXP-0001–0147,
snapshot 2026-10-27) contains a hash-identified Steam x86 build record,
904-package structural inventories, catalogs of 72,437 internal executable
functions, extensive resource-format experiments, and selected static slices
of Blink, input, native registration, and Wwise/audio. These inventories
are **not** proof of full semantic recovery: the manual function-review
overlay covers 37 bodies at EXP-0147, and reproducible game-runtime behavior
remains unverified. See [research status](docs/research-status.md) and the
[completion contract](docs/roadmap.md) for the live denominator and remaining
gaps. GitHub `main` may lag the source research branch.

Documentation integrity and reproducibility were reviewed in the
[2026-10-27 repository audit](docs/reviews/AUDIT-2026-10-27-repository-integrity.md).
The GitHub-only CI checks validate research-record structure and local
documentation links; they do not independently rerun the game-dependent
experiments or verify the ignored local source binaries.
