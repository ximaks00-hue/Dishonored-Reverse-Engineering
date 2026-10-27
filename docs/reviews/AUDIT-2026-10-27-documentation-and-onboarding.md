# AUDIT-2026-10-27 — Documentation and contributor readiness

## Scope and limits

This review started from corpus commit `0f89a5e` on `codex/research-corpus-sync` (EXP-0155). It inventoried the tracked Markdown corpus, inspected the project entry points and current summary pages, and compared selected status/count claims against their cited EXP records and local source catalogs. Repository link and EXP checks were added and run after the edits in this review.

The review does not independently rerun Ghidra, UModel, UELib, QuickBMS, Wwise parsers, or the game. It does not validate every interpretation in 155 EXP bodies against primary game data. EXP records remain the source of truth; current numeric results are reported by those records. No runtime verification was added.

## Findings and changes

| Finding | Change | Evidence / boundary |
| --- | --- | --- |
| New contributors had no focused guide for task selection, evidence quality, build requirements, local checks, or game-data handling. | Added [Contributing](../../CONTRIBUTING.md), a research-task issue form, and a pull-request template. | Repository contribution process only; it grants no access to local game files or services. |
| The README and handbook did not provide a concise new-contributor route. | Reworked [README](../../README.md) and [handbook index](../index.md) around task-oriented navigation and current scope. | Link and structure checks; no game-dependent claims inferred. |
| `research-status.md` repeated a large coverage table and long narrative. | Reduced it to current evidence, next work, and navigation; moved 33 measure rows to [coverage](../coverage.md); condensed the roadmap into scope, completion gates, and a ranked work order. | Coverage remains a summary of the linked EXP records and retains per-row scope/limits. |
| Workflow documentation described legacy `status` frontmatter and the function evidence model still used a 44-review count. | Updated workflow instructions and the EXP-0155 snapshot in the L0–L4 page. | Current local sync reported 72,437 indexed functions: L0=72,383, L1=50, L2=4, L3=0, L4=0; 47 EXP-0155 manual body reviews. |
| Coverage text could imply that EXP-0129 performed Bink decoding and that the localized AKPK table lacked a QuickBMS cross-check. | Separated EXP-0118 full-stream decode from EXP-0129 metadata/cues, and the EXP-0134 container-table cross-check from WEM payload semantics. | These distinctions are based on the cited EXP scopes; decoder acceptance is not audiovisual correctness or runtime selection. |
| MCP documentation mixed current source and last-observed connected service versions and linked to ignored local config as if committed. | Documented source version `2.2.0`, last-observed connected version `2.1.0` in EXP-0122, and local ignored config paths as plain text. | A live `health` result after reload remains necessary to establish connected-service behavior. |
| Local Markdown links were checked only for experiment records; several historical changelog links escaped the repository or pointed to the wrong evidence path. | Added a repository-wide local-path checker, four fixture tests, CI steps, and corrected the reported paths. | The checker includes tracked and non-ignored untracked Markdown. It does not validate heading fragments, external URLs, or all Markdown syntax. |

## Validation performed

- `python tools/check_research_docs_links.py` — passed on all repository Markdown files in the working tree.
- `python tools/validate_experiments.py` — 155 experiment records, zero errors, zero warnings.
- `python -m unittest discover -s tests -p test_docs_links.py -v` — four checker tests passed.
- `git diff --check` — passed after edits.

These checks validate links and record structure. They do not certify research claims or reproduce game-dependent results.

## Open project risks

1. The headless decompilation cache is keyed by normalized function address and checks build ID / executable SHA, but it does not invalidate on Ghidra version, analysis options, or project-analysis revision. See `mcp_servers/common/decompile_cache.py` and [the function evidence model](../methodology/function-evidence-model.md).
2. The L4 progress view recognizes a replicated, confirmed runtime record but does not compare that record's `build_sha256` with the executable SHA joined to the indexed function. A future runtime importer should enforce identity before the view can count L4.
3. The knowledge sync needs the exact local executable and function index to rebuild function coverage. The derived SQLite mirror is ignored by Git; repository-only CI cannot independently reproduce L0–L4 counts.
4. `tools/validate_experiments.py` uses a small line-oriented frontmatter parser and path-link regex rather than a complete YAML/Markdown parser. It is adequate for current records but does not validate full YAML syntax or all link forms.
5. Runtime evidence remains zero; 47 of 72,437 indexed bodies have manual body reviews, and the exact-build function unknown bucket remains large. See [coverage](../coverage.md) and [roadmap](../roadmap.md).
6. The GitHub research corpus is carried on a long stacked draft-PR history. Branch integration still needs a reviewed rebase/merge plan; this review does not merge or retarget PRs.
7. The first hosted Actions run failed because the EXP validator treated four intentionally local-only paths (ignored extracted outputs and the local decompressor) as broken links. The validator now exempts only those path families; a successful hosted run is still required.
8. GitHub's API reports that branch protection is unavailable for this private repository on its current plan (HTTP 403: upgrade to Pro or make the repository public). The collaborator list currently contains only the owner. No protection was configured and no contributor access was granted.

## Follow-up order

1. Research branch `codex/research-corpus-sync` contains EXP-0001–0155, including EXP-0114. The current `main` branch has no experiment directory because the corpus is still in stacked draft PRs. Integrate that reviewed PR stack before saying the experiment corpus is available from the default branch; do not reconstruct any other historical sources that are not present.
2. Verify a successful GitHub Actions run for the corrected CI on the final commit; local validation alone is not CI evidence.
3. Upgrade the private repository plan or make the repository public before enabling and verifying `main` protection and required checks. Add collaborators only by explicit GitHub username and agreed permission.
4. Add an evidence-manifest format for generated catalogs (EXP/source hashes, build, tool/options, row count, and reproduction command) and adopt it for new outputs before migrating old artifacts.
5. Correct decompile-cache invalidation and L4 build matching with negative cross-build cases; do not relabel existing evidence automatically.
6. Publish a compact coverage export that can be regenerated from validated metadata without requiring game binaries; keep exact-build re-indexing as a separate local operation.
7. Continue priority-driven reverse engineering from the [roadmap](../roadmap.md). Preserve runtime and semantic gaps in the status instead of implying completion from inventory counts.
