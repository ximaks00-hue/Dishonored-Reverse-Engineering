# Contributing

This repository is an evidence project. Contributions should make a research claim easier to verify, reproduce, challenge, or continue. A larger experiment count or a plausible interpretation is not, by itself, progress.

## Start here

1. Read the [project overview](README.md), [research status](docs/research-status.md), [roadmap](docs/roadmap.md), and [evidence policy](docs/methodology/evidence.md).
2. Check the [open work order](docs/roadmap.md#current-work-order) and existing [experiments](experiments/) before starting a new investigation.
3. Confirm the exact build in [BUILD-STEAM-10256413](research/builds/BUILD-STEAM-10256413/build.md) when work touches game files, addresses, or behavior. Its executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
4. Choose a contribution path below. Documentation and tooling work can be done without a local game installation. Package, binary, and runtime work has additional requirements.

## Ways to help

| Contribution | Useful starting point | Local requirements |
| --- | --- | --- |
| Documentation, link fixes, or evidence indexing | `docs/`, `experiments/`, this guide | Python 3.12; repository checkout |
| Research tooling or parsers | `tools/`, `schemas/`, `knowledge/database/` | Python 3.12; read the tool's README and requirements |
| UE3 package or resource analysis | `research/packages/`, relevant EXP | Matching package files and the recorded parser/tool versions |
| Native executable analysis | `research/executable/`, function evidence model | Matching executable, Ghidra project or approved static tool, and exact build identity |
| Runtime behavior research | `docs/gameplay/`, runtime EXPs | A clean baseline and a matching process started by the user for the experiment |

Select a task that resolves a documented question, tests a falsifiable hypothesis, or connects existing evidence. Prefer one high-value missing relationship over a sequence of arbitrary function addresses. A class name, offset, token, vtable index, or tool-generated label may identify a candidate; it does not prove ownership or behavior.

## Evidence and writing rules

- Record each new procedure or result in `experiments/EXP-NNNN-slug.md`, using `templates/experiment.md` and the required `experiment_status` and `claim_status` fields.
- Treat the EXP body as the primary record. Update the status, roadmap, findings, coverage snapshot, and knowledge mirror only as summaries of checked evidence.
- Separate measured observations from interpretation. Use `confirmed`, `observed`, `inferred`, `unknown`, `superseded`, and `rejected` precisely; a rejected label must name its hypothesis scope.
- State the build, hashes, paths/addresses, tools and versions, options, data source, method, limits, and a reproduction route when they apply.
- Distinguish function indexing, analysis, semantic understanding, cross-function dataflow, and runtime verification. See the [L0–L4 model](docs/methodology/function-evidence-model.md).
- Keep PowerWheel item `24`, UI enum `2`, active-array index `0`, and `_iPower` separate. Preserve the open/weakened status of `FUN_00C0CA70` and the scoped rejection of the Pawn-manager ABI hypothesis.
- Do not turn decompiler pseudocode into a source-code quote. Preserve raw-byte or parser evidence where a claim depends on it.

## Local setup and checks

The documentation checks use Python 3.12 and the standard library. A virtual environment is optional for these checks.

```powershell
python --version
python tools/validate_experiments.py
python tools/check_research_docs_links.py
python -m unittest discover -s tests -p "test_docs_links.py" -v
```

For exact-build work, configure local tool paths with environment variables or a private MCP host configuration. See [MCP and path setup](docs/tooling/mcp.md) and [session checklist](docs/tooling/session-checklist.md). Do not put machine-specific paths, credentials, or generated databases in tracked files.

`python tools/knowledge/sync_from_experiments.py` rebuilds the local SQLite mirror and requires the exact-build executable and function index. It is not a repository-only check and the database is intentionally gitignored.

## Game data and generated artifacts

Do not commit the executable, UPKs, extracted packages/assets, saves, local Ghidra projects or locks, decompilation caches, local SQLite databases, or copyrighted payloads. Keep local extraction under ignored `assets/extracted/`; commit only source code, compact permitted catalogs, schemas, and evidence documents. Check `git status` and the staged diff before committing.

## Pull requests

- Branch from the corpus branch named by the maintainer; GitHub `main` can lag the current research set. Do not silently rebase or merge stacked research branches.
- Keep a change focused and link its EXPs, source evidence, affected summaries, and validation output. Do not claim that repository-only CI re-ran game-dependent experiments.
- Use a draft PR while evidence or review is incomplete. Do not merge a stacked PR or alter the target branch without an agreed integration plan.
- Complete the [pull request template](.github/pull_request_template.md). Report unresolved evidence and practical reproduction limits directly.
