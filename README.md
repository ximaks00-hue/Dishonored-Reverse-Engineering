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

The local workspace has a hash-identified Steam x86 executable record, package inventory, Blink UPK metadata, and read-only Ghidra analysis. See [research status](docs/research-status.md) for confirmed findings and open questions. The connected GitHub `main` branch may lag behind this local evidence set; compare its contents before treating it as the complete research record.
