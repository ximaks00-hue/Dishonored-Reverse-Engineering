# Research workflow

1. **Identify scope.** Name the build and exact question. If build identity is unknown, make that the first task.
2. **Capture baseline.** Record file identity, tool versions, and relevant configuration before changing anything.
3. **Write a procedure.** Include prerequisites, steps, inputs, expected observable outputs, and cleanup/reset steps.
4. **Collect observations.** Preserve raw output or stable references. Avoid interpretive language in the observation field.
5. **Analyze.** Compare alternatives and state what evidence would falsify each explanation.
6. **Record and link.** Give the experiment a stable ID and YAML frontmatter (`id`, `title`, `experiment_status`, `claim_status`, `build`, `question`); link the build, artifacts, findings, and open questions. Keep [research-status.md](../research-status.md) short; put detailed measures in [coverage.md](../coverage.md), session narrative in [changelog.md](../changelog.md), and durable claims in [findings/](../findings/).
7. **Review.** Re-run when practical, check scope and provenance, and update status without erasing history. Run `python tools/validate_experiments.py` and optionally `python tools/knowledge/sync_from_experiments.py`.

## File and package archaeology

Start with a read-only manifest: relative path, size, hash, detected type, and build ID. For package inspection, record tool/version and parser warnings. Keep package exports local and ignored. Never infer package compatibility solely from the engine family name.

## Behavioral research

Use a small vertical slice. Record starting state, inputs, timing, environment/settings, and visible result. Repeat trials when stochastic behavior or timing can affect outcomes. State explicitly what the result does not establish.

## Native code research

Tie names, signatures, and RVAs to a specific module hash. Mark analyst-assigned function names as provisional. Keep decompiler output as a derived view and retain links to the disassembly/function record used to interpret it.

## Tooling and parser checks

Prefer deterministic scripts for repeated inventory or comparison. Check repository links and experiment structure with `python tools/check_research_docs_links.py` and `python tools/validate_experiments.py`. When adding a parser or checker, include small synthetic valid and malformed examples with its tests. Keep generated data reproducible and avoid storing bulky or copyrighted input in source control.
