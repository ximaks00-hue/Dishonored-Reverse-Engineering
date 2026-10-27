# Start contributing in 30 minutes

**No game installation required** for documentation review, synthetic parser tests, validation rules or triage.

1. Read [README](../README.md), [contribution guide](../CONTRIBUTING.md), and [current status](research-status.md).
2. Pick exactly one question in [the backlog](backlog.md), or open a GitHub issue using a template.
3. For a research experiment, copy [the experiment template](../templates/experiment.md). Assign a unique EXP ID, define expected distinguishing outcomes, and document inputs and build identity.
4. For an implementation change, add synthetic fixtures and tests; run `python tools/validate_repo.py` and `python -m unittest discover -s tests -v`.
5. Submit a narrowly scoped PR. Include evidence links, known limitations and reproduction instructions.

## Paths through the project
- **Writer/reviewer:** fix incorrect implications and links, add definitions, review provenance.
- **Python developer:** add deterministic inventories/parsers and synthetic tests.
- **Static analyst:** contribute module-hash-bound RVAs, types and calling relationships.
- **Gameplay tester:** perform repeatable, controlled observations without sharing game data.
- **Maintainer:** triage issues, resolve record-ID conflicts, enforce evidence and licensing policies.

Ask for help by opening an issue labeled `question`; labels require a maintainer to configure them. All listed contributions must obey applicable law and rights.
