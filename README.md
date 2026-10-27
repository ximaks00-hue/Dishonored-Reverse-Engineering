# Dishonored Reverse Engineering

An evidence-led project to reconstruct Dishonored's files, UE3 packages, native code, and selected runtime behavior. The project is active and incomplete; see the [research status](docs/research-status.md), [coverage snapshot](docs/coverage.md), and [full-scope roadmap](docs/roadmap.md).

## Research progress dashboard

Progress is tracked by research direction, not by one project-wide completion percentage. Each direction has its own denominator and evidence limits. The [visual dashboard](docs/progress-dashboard.md) gives the full snapshot, source links, and next milestone priorities.

| Direction | Status | Snapshot |
| --- | --- | --- |
| Build and installation | Established | Steam x86 build `10256413`; 13,623-path install manifest; 904/904 UPKs reconciled |
| Packages and formats | Strong | 904 UPKs cataloged; 4,056/4,056 non-empty localized AKPK containers parsed |
| Config and paths | Active | 63 path-shaped candidates from 76 directives; runtime resolution remains open |
| Blink and gameplay | Active | Several conditional static edges confirmed; dynamic caller and runtime bridge remain open |
| Native code | Early-to-mid | 72,437 functions indexed; 49 manual body reviews; L0–L4 counts remain separate |
| Audio and media | Strong | 503 PCKs cataloged; 1,908 WEM and 76 Bink files decoded with scoped limits |
| Tooling and automation | Strong | Validators, schemas, CI, and repository research tools are in place |
| Collaboration and review | Active | Contributor guidance and review process exist; independent reproduction is still scaling |

Inventory and parser coverage do not imply semantic understanding. Static analysis, independent review, and runtime confirmation are separate evidence outcomes.

## Join the work

Start with [Contributing](CONTRIBUTING.md) for task selection, evidence rules, local checks, data handling, and pull request guidance. Repository-only documentation work does not require a game installation. Binary and runtime work has stricter build and baseline requirements.

## Read in this order

1. [Current research status](docs/research-status.md)
2. [Evidence and provenance policy](docs/methodology/evidence.md)
3. [Project roadmap and completion contract](docs/roadmap.md)
4. [Research handbook](docs/index.md)
5. [Experiment catalog](experiments/)

## Research principles

- Tie executable addresses and behavior claims to a named build and file hash.
- Separate observation from interpretation; label claims as confirmed, observed, inferred, unknown, superseded, or rejected within a stated hypothesis scope.
- Treat EXP bodies as the primary research record. Status pages, findings, and the SQLite database summarize EXP evidence.
- Keep analysis coverage separate from semantic understanding, dataflow, and runtime verification. Decompiled pseudocode is an analysis output, not original source.
- Keep game binaries, UPKs, extracted assets, saves, local caches/databases, and machine-specific configuration out of Git.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/` | Status, methodology, findings, architecture, roadmap, and tool guidance |
| `experiments/` | Primary methods, observations, interpretations, and limits, indexed by EXP ID |
| `research/builds/` | Build identities and file manifests |
| `research/executable/` | Function index, compact evidence catalogs, scripts, and triage |
| `research/packages/` | Package inventories and parser-derived catalogs |
| `schemas/` | Machine-readable research schemas |
| `templates/` | Build, experiment, and subsystem templates |
| `tools/`, `mcp_servers/` | Reproducible analysis tools and local MCP services |
| `assets/extracted/`, `knowledge/cache/` | Local generated data; ignored by Git |

## Build scope

The current reference record is Steam x86 build `10256413`, executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`. See the [build record](research/builds/BUILD-STEAM-10256413/build.md) for provenance and installation limits. GitHub `main` may lag the active research corpus; contributors should use the branch named by the maintainer and read [branch guidance](CONTRIBUTING.md#pull-requests).
