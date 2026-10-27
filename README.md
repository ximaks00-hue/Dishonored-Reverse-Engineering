# Dishonored Reverse Engineering

Community-oriented, evidence-led research into **Dishonored (Windows)**, covering installation and configuration, Unreal Engine 3 packages, runtime behavior, gameplay systems and selected native functions.

> **Project status:** research infrastructure and community workflow are available; the audited GitHub repository does **not yet contain verified build-specific experiments or function records**. See [research status](docs/research-status.md). Local work discussed outside the repository is not automatically published evidence.

## Why this project exists
Build a searchable, reproducible account of how selected game systems work, with documented uncertainty and independent behavioral models. **This is not a claim of recreating the complete game.** The project does not distribute game data and is not affiliated with the rights holders.

## Participate
**New contributor?** Start with [onboarding](docs/onboarding.md) and [CONTRIBUTING](CONTRIBUTING.md). You can help with documentation, verification, synthetic test cases and code without owning the game. Propose a [research question](https://github.com/ximaks00-hue/Dishonored-Reverse-Engineering/issues/new/choose) or improve an existing issue.

## Navigation
| Goal | Document |
| --- | --- |
| Learn what has actually been verified | [Research status](docs/research-status.md) |
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

Use `python tools/validate_repo.py` and `python -m unittest discover -s tests -v` (Python 3.11+) before proposing changes. GitHub Actions runs the same checks on pull requests.

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
