# Start contributing in 30 minutes

**No game installation required** for documentation review, synthetic parser tests, validation rules or triage.

1. Read [README](../README.md), [contribution guide](../CONTRIBUTING.md), and [current status](research-status.md).
2. Pick one of the [small contributor tasks](contributor-tasks.md), or open a bounded question using a GitHub issue template.
3. Read the [contributor playbook](contributor-playbook.md) for worked examples, hypothesis acceptance and independent review.
4. For an experiment, copy [the experiment template](../templates/experiment.md). Reserve a unique EXP ID through the issue or PR; state predicted distinguishing outcomes, inputs and build identity.
5. For code, use synthetic fixtures where possible. Install the documented dependencies and run `python tools/validate_repo.py` and `python -m unittest discover -s tests -v`.
6. Submit a focused PR linked to the task. Include evidence links, limitations, reproduction steps and a separate independent review for claims proposed as confirmed.

## Paths through the project
- **Writer/reviewer:** fix incorrect implications and links, add definitions, review provenance.
- **Python developer:** add deterministic inventories/parsers and synthetic tests.
- **Static analyst:** contribute module-hash-bound RVAs, types and calling relationships.
- **Gameplay tester:** perform repeatable, controlled observations without sharing game data.
- **Maintainer:** triage issues, resolve record-ID conflicts, enforce evidence and licensing policies.

Ask for help by commenting on the issue or opening one labeled `question`. All listed contributions must obey applicable law and rights.
