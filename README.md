# Dishonored Reverse Engineering

Community-oriented, evidence-led research into **Dishonored (Windows)**, covering installation and configuration, Unreal Engine 3 packages, runtime behavior, gameplay systems and selected native functions.

> **Project status:** the research corpus includes 155 build-scoped experiments, a recorded Steam build and file manifest, reproducible analysis tools, and static native-function review catalogs. These records preserve their evidence level and limitations; they do not claim runtime verification of all findings. See [research status](docs/research-status.md) and the [published evidence index](docs/published-evidence.md).

## Why this project exists
Build a searchable, reproducible account of how selected game systems work, with documented uncertainty and independent behavioral models. **This is not a claim of recreating the complete game.** The project does not distribute game data and is not affiliated with the rights holders.

## Research progress dashboard

Progress is tracked by research direction, not by one project-wide completion percentage. Each direction has its own denominator, evidence model, and open questions.

> See the [visual progress dashboard](docs/progress-dashboard.md) for the current snapshot and detailed workstream pages.

| Direction | Status | Current evidence |
| --- | --- | --- |
| Build and installation baseline | Established for recorded snapshot | Steam x86 build identified; 904/904 UPKs reconciled |
| Packages and file formats | Broad static coverage | Package catalogs and selected format parsers cover large cohorts |
| Config and path analysis | Candidate evidence established | Filesystem candidates recorded; runtime resolution remains open |
| Blink and gameplay | Active | Conditional static paths documented; runtime bridge remains open |
| Native code | Selective semantic review | 72,437 indexed; 47 manual body reviews; portable export has 54 analysis records |
| Audio and media | Broad corpus parsing | PCK/WEM, AKPK, HIRC, and Bink cohorts have scoped coverage |
| Tooling and automation | Reproducibility improving | Validators, CI, schemas, tests, and portable coverage export |
| Collaboration and review | Contributor path documented | Tasks, onboarding, templates, and independent-review process |

Inventory or parser coverage does not imply semantic understanding. See the dashboard for denominators, evidence boundaries, and linked source records.

## Participate
**New contributor?** Pick a [small task](docs/contributor-tasks.md), then read [onboarding](docs/onboarding.md) and [CONTRIBUTING](CONTRIBUTING.md). The [contributor playbook](docs/contributor-playbook.md) includes worked examples and the independent review process. You can help with documentation, verification, synthetic test cases and code without owning the game. Propose a [research question](https://github.com/ximaks00-hue/Dishonored-Reverse-Engineering/issues/new/choose) or improve an existing issue.

## Navigation
| Goal | Document |
| --- | --- |
| View research progress by direction | [Progress dashboard](docs/progress-dashboard.md) |
| Learn what has actually been verified | [Research status](docs/research-status.md) |
| Browse published experiments, build identity and native-function records | [Published evidence index](docs/published-evidence.md) |
| Understand project organization | [Handbook](docs/index.md) and [architecture](docs/architecture/overview.md) |
| Choose valuable work | [Research backlog](docs/backlog.md) and [roadmap](docs/roadmap.md) |
| Record reliable evidence | [Evidence policy](docs/methodology/evidence.md) and [claim policy](docs/methodology/claims.md) |
| Run experiments | [Experiment template](templates/experiment.md) and [workflow](docs/methodology/workflow.md) |
| Analyze functions selectively | [Function triage](docs/methodology/function-triage.md) |
| Contribute safely | [Community guide](CONTRIBUTING.md), [security](SECURITY.md), [licensing notice](LICENSE-NOTICE.md) |

## Basic workflow
1. Identify an exact build and a bounded research question.
2. Define competing explanations and design a discriminating test.
3. Record original observations, prerequisites, hashes and tools.
4. Separate observed behavior from inferred implementation.
5. Link stable EXP/OBS/HYP/FIND records and update the appropriate subsystem.
6. Have another contributor reproduce or review the claim.

Install validator dependencies with `python -m pip install -r requirements-dev.txt`, then run `python tools/validate_repo.py` and `python -m unittest discover -s tests -v` (Python 3.11+) before proposing changes. GitHub Actions runs the same checks on pull requests.

## Research principles
- The build, environment, file hash and method constrain every claim.
- **Observed**, **confirmed**, **inferred**, **unknown**, **planned** and **superseded** mean different things.
- Pseudocode is not original source; a filesystem match is not proof of runtime use.
- RVAs are module-relative and meaningful only with binary identity.
- Preserve contradictory results, limitations and negative findings.
- Keep all copyrighted game content, private analysis databases and local installations out of Git.

## Repository layout
`docs/` contains research policy, status and synthesis; `experiments/` holds actual studies; `templates/` offers reusable report formats; `schemas/` describes machine-readable records; `tools/` and `tests/` enable reproducible validation; `.github/` handles contributor workflows. Empty areas do not imply research coverage.

**Licensing:** no project-wide open-source license has been selected yet; see [license notice](LICENSE-NOTICE.md) before substantial contributions.
