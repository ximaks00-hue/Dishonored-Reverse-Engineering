# Contributing to Dishonored Reverse Engineering

Thank you for helping build a reproducible, evidence-led description of Dishonored. Contributions of any size are welcome: testing one configuration hypothesis, correcting a broken reference, reproducing a result, improving a parser, or documenting a native function.

## Quick start
1. Read [the research handbook](docs/index.md), [current status](docs/research-status.md), and [evidence policy](docs/methodology/evidence.md).
2. Browse issues tagged `good first issue`, `help wanted`, or `research-question`; if none exist, open an issue describing a small testable question.
3. Fork the repository, create a branch, and make a focused change. Never add game binaries, extracted copyrighted assets, saves, decompiler databases, secrets, or personally identifying paths.
4. Run `python tools/validate_repo.py` and `python -m unittest discover -s tests -v` with Python 3.11+.
5. Open a pull request using the template and link related issue, experiment IDs, evidence, and remaining uncertainty.

## Research contributions
A good report states **which build**, **what question**, **which inputs**, **what procedure**, **what output**, and **what remains unknown**. Record measurements separately from explanations. Link hypotheses to a test capable of distinguishing alternatives. If you lack a build, contribute a planned test, tooling improvement, or documentation correction without claiming runtime confirmation.

Use `experiments/EXP-NNNN-topic.md` for a repeatable experiment (reserve an unused ID via a pull request or issue). Use `docs/findings/FIND-NNNN-topic.md` for a durable conclusion with direct source references; create subsystem synthesis only when evidence warrants it. Record function RVAs only with module SHA-256 and build identity. Avoid copying decompiled source into the repository.

## Review standards
Reviewers verify traceability, scope, safety of committed material, reproducibility, terminology, tests, and whether conclusions overstate results. One approval is encouraged before merging; repository owners configure actual branch protection. A reproducible negative result is valuable. Preserve corrections and superseded findings rather than erasing their history.

## Community
Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report potential security issues privately as described in [SECURITY.md](SECURITY.md). GitHub issues are for research questions and publicly discussable bugs, not for sharing copyrighted game content.

## Attribution
Respect third-party licenses; link external references and tools, identify the author of new research, and distinguish original measurements from external statements. Contributions are subject to the repository's licensing decisions; see [LICENSE-NOTICE.md](LICENSE-NOTICE.md) before submitting substantial code or content.
