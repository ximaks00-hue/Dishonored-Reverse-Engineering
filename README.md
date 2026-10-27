# Dishonored Reverse Engineering

Community-oriented, evidence-led research into **Dishonored (Windows)**, covering installation and configuration, Unreal Engine 3 packages, runtime behavior, gameplay systems and selected native functions.

> **Project status:** the research corpus includes 155 build-scoped experiments, a recorded Steam build and file manifest, reproducible analysis tools, and static native-function review catalogs. These records preserve their evidence level and limitations; they do not claim runtime verification of all findings. See [research status](docs/research-status.md) and the [published evidence index](docs/published-evidence.md).

## Research progress dashboard

Progress is tracked by research direction, with explicit denominators and evidence limits. There is no single project-wide completion percentage. See the [visual progress dashboard](docs/progress-dashboard.md) for measured coverage, open questions, and next milestones.

| Direction | Status | Snapshot |
| --- | --- | --- |
| Build and installation | Established | Steam x86 build `10256413`; 13,623-path install snapshot; 904/904 UPKs reconciled |
| Packages and formats | Strong | 904 UPKs cataloged; 4,056/4,056 non-empty localized AKPK containers parsed |
| Config and paths | Active | EXP-0114 reports 63 syntactic candidates from 76 directives; runtime resolution remains open |
| Blink and gameplay | Active | Conditional static edges documented; dynamic caller and runtime bridge remain open |
| Native code | Early-to-mid | 72,437 functions indexed; 47 manual body reviews through EXP-0155; runtime-verified functions: 0 |
| Audio and media | Strong | 503 PCKs cataloged; 1,908 WEM and 76 Bink files decoded with scoped limits |
| Tooling and automation | Strong | Validators, schemas, CI, and repository research tools are in place |
| Collaboration and review | Active | Contributor guidance and review process exist; independent reproduction is still scaling |

Inventory and parser coverage do not imply semantic understanding. Static analysis, independent review, and runtime confirmation are separate evidence outcomes.

## Why this project exists
Build a searchable, reproducible account of how selected game systems work, with documented uncertainty and independent behavioral models. **This is not a claim of recreating the complete game.** The project does not distribute game data and is not affiliated with the rights holders.

## Participate
**New contributor?** Pick a [small task](docs/contributor-tasks.md), then read [onboarding](docs/onboarding.md) and [CONTRIBUTING](CONTRIBUTING.md). The [contributor playbook](docs/contributor-playbook.md) includes worked examples and the independent review process. You can help with documentation, verification, synthetic test cases and code without owning the game. Propose a [research question](https://github.com/ximaks00-hue/Dishonored-Reverse-Engineering/issues/new/choose) or improve an existing issue.

## Navigation
| Goal | Document |
| --- | --- |
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
