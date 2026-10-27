# AUDIT-2026-10-27 — Research corpus, documentation, and reproducibility

> **Scope and limits.** Repository inspection against `codex/research-corpus-sync`
> commit `d672b73aa9849fdfb45fcbae29b19c64d95a666a` (EXP-0147), with a
> separately proposed documentation/CI patch. This audit inspects checked-in
> text, Python, SQL and GitHub PR metadata. It **does not** independently run
> Ghidra, UModel, UELib, the game, local MCP hosts, hash 15 GB of installation
> files, or verify ignored extraction outputs. Experimental numerical results
> below are *reported by checked-in EXP evidence*, not remeasured in CI.

## Executive assessment

The project has a strong evidence-first foundation: build identity, 147
nonduplicated EXP records, build-hash-linked resource catalogs, an indexed
72,437-internal-function universe, explicit rejected/open Blink hypotheses,
an L0–L4 function-evidence model, and reproducible helper scripts. It does
**not** have full semantic/native or runtime coverage. The most immediate
risk is not insufficient catalogs; it is documentation drift, missing
repository-wide CI gates, ambiguous active-vs-source MCP versions, and stale
tool caches being mistaken for fresh evidence.

The earlier eight EXP-number collisions are **resolved in this snapshot**:
the repository tree has one `experiments/EXP-*.md` path per ID from EXP-0001
through EXP-0147. Do not renumber these records again.

## Findings and proposed action

| Priority | Finding / source evidence | Correction / acceptance test | This patch |
| --- | --- | --- | --- |
| P1 | [Research workflow](../methodology/workflow.md) documented legacy `status` despite [validator](../../tools/validate_experiments.py) requiring `experiment_status` and `claim_status`. | Update the template instructions; validate all 147 EXP frontmatters in CI. | Fixed + CI |
| P1 | Existing [research-evidence CI](../../.github/workflows/research-evidence.yml) checked only the EXP-0014 derived report, not the full EXP validator. Other two workflows target older REV tests. | Add `python tools/validate_experiments.py` to PR CI; preserve dedicated REV tests. | Fixed |
| P1 | Markdown documentation links were broken: nine `../../` paths in [changelog](../changelog.md) escape the repo; two more changelog targets used nonexistent relative locations; [roadmap](../roadmap.md) pointed to nonexistent `docs/gameplay/activation-graph.md`. Two MCP READMEs linked ignored `.cursor/mcp.json` as though committed. | Fix targets; add a lightweight repository-local documentation link checker to PR CI. External URLs and anchor existence remain outside this checker. | Fixed + CI |
| P1 | [Research status](../research-status.md) still said the localized AKPK table had *no QuickBMS cross-check* in a row based on EXP-0130/0131, despite elsewhere acknowledging EXP-0134. The movie-metadata row could be read as denying the earlier EXP-0118 full decode. | Explicitly distinguish the original experiment's scope from later EXP-0134 and EXP-0118 results. | Fixed |
| P1 | [MCP readme](../../mcp_servers/README.md) identified v2.1 without distinguishing assets source v2.2.0 and the running host still observed as 2.1.0 in EXP-0122; [MCP configuration](../tooling/mcp.md) linked an ignored local file. | Describe source vs connected process separately; require live `health` after reload; show `.cursor` path as local text. | Fixed |
| P1 | [MCP decompile cache](../../mcp_servers/common/decompile_cache.py) validates build/EXE SHA but uses only normalized address as filename and **does not validate Ghidra/tool version, tool options, or project-analysis revision** on load; see `cache_path()`, `load()`, `store()`. This is narrower than [function-evidence-model](../methodology/function-evidence-model.md)'s DB analysis-key contract. | Design a versioned cache key including exact binary, address, tool+version/options and analysis-project revision (when accessible). Add regression tests for invalidation. Do **not** silently mark existing pseudocode invalid or rewrite claims. | Open |
| P1 | [Knowledge sync](../../tools/knowledge/sync_from_experiments.py) requires local, hash-verified `Dishonored.exe` and `functions.csv` for L0 imports, while `knowledge/database/*.sqlite` is deliberately gitignored. GitHub CI cannot independently reproduce all function-level metrics from this repository alone. | Split metadata-only validation from exact-build re-indexing; publish a compact provenance/count summary and a reproducible offline-build command; never commit EXE/UPK/copyrighted assets to enable CI. | Open |
| P1 | PR #13 targets `research/rev-0012-blink-warmup-dispatch`, itself atop a long chain of open draft PRs. `main` is not a complete mirror of the research corpus. | Plan one reviewed integration/rebase strategy with safeguards for provenance; compare branch ancestry, archive superseded helper docs, avoid merging duplicated historical EXPs. No automated merge. | Open |
| P2 | [research-status](../research-status.md) is a long narrative with several repeated denominators; manual overlays are updated every EXP. Future status drift is likely. | Generate a small machine-readable coverage snapshot and render tables from it, keeping narrative interpretations and caveats hand-written. | Open |
| P2 | [Validator](../../tools/validate_experiments.py) uses a line-split frontmatter parser and a simple Markdown-link regex, not a complete YAML/Markdown parser; statuses and basic relative-path existence are checked, but evidence cross-document consistency is not. | Add focused fixtures for quoted/multiline YAML, duplicate keys, escaped links, root escape, and missing evidence refs. Introduce schema validation only if it preserves existing valid records. | Open |
| P2 | [Assets object cache](../../mcp_servers/common/package_cache.py) and runtime host were linked to observed summary/list divergence (EXP-0083) and DLC path rejection (EXP-0122). Code presence or manifest coverage is not proof a connected host is using the new object index. | Add per-tool self-test reporting version, package-root, object-index commit/generation and exact package path; run after host restart; distinguish source bug from stale process/cache. | Open |
| P2 | Script/package/native catalogs are extensive, but runtime-verified function count remains **zero**. The L0–L4 model already correctly separates this. | Establish a clean user-started matching-process baseline, versioned runtime captures and finite vertical test cases; never infer runtime execution from direct callgraph links. | Open |

## Actual coverage — do not mix denominators

- **147** unique documented experiments, EXP-0001…EXP-0147, at the pinned audit commit. GitHub tree inspection; this is not a claim that all procedures independently passed on this runner.
- **904** UPK in the structurally inventoried installation, per EXP-0052/0069 and subsequent reconciliation.
- **72,437** internal function entries; indexing is L0, not semantic decompilation. The active manual-overlay snapshot is **37 body reviews** by EXP-0147; the automated baseline had 71,998 unknown-subsystem rows. The current overlay changes some candidate attribution, not the underlying function denominator.
- **0** runtime-verified functions and **0** clean-baseline behavior experiments, per current status. Deliberately keep these zero counts visible.
- **4,056** nonempty localized AKPK paths and **7,213** distinct decoded WEM payloads, per EXP-0130/0131; EXP-0134 adds a QuickBMS structural cross-check but not a vendor specification or game-runtime proof.
- API/type metadata, static graph edges, same-name candidates, and exact pixel comparisons are *different evidence kinds*: do not aggregate them into a single completion percentage.

## Required next work packages

1. **Evidence contract and CI (immediate):** merge the safe link/frontmatter/status changes after the new link/EXP checks pass; add a small test suite for the Markdown checker. Verify README/roadmap/status links on each PR.
2. **Evidence artifact manifest (next):** make every generated CSV/JSON declare source EXP ID, source paths and hashes, tool revision, options hash, build ID, row count, and re-run command. Compare regeneration using stable normalized ordering rather than timestamps or absolute workstation paths.
3. **Function cache correctness:** implement key invalidation for the MCP decompiler cache; test changed Ghidra version/options and reanalysis. Keep L1 analysis distinct from L2 semantic role claims.
4. **Knowledge coverage reporting:** derive `indexed/analyzed/confirmed-role/confirmed-dataflow/runtime` numbers from the verified DB with an exported JSON snapshot. Prefer an offline metadata mode in CI and an exact-build reproduction procedure on the developer machine.
5. **Priority-driven RE:** investigate callers/owners closing E7, audio queue identity and event-resource joins, missing Wwise media domains, and the ~254 indexed native-class-table targets. Accept a subsystem conclusion only with exact-build provenance and explicit static/runtime boundary.
6. **Version control:** keep primary EXP history immutable unless correcting it with traceable superseding evidence; close/rebase stacked PRs only after an integration plan is agreed. Preserve `_excluded_coop_project/` untouched.

## Verification commands

Repository-only (appropriate for GitHub-hosted CI):

```sh
python tools/validate_experiments.py
python tools/check_research_docs_links.py
python tools/check_exp0014_index.py
```

Exact-build work (local Windows installation + appropriate tools required):

```powershell
python tools/knowledge/sync_from_experiments.py
python -m pytest tests/mcp -q
python tools/mcp_smoke_test.py
```

Passing the repository-only checks **does not certify content accuracy,
native-function runtime behavior, game installation hash checks, or full
reproducibility of UModel/UELib/QuickBMS/Ghidra results**. Retain the original
EXP evidence links and all rejected/inferred/unknown labels.

## Revalidation scope

Review target: pull request against `codex/research-corpus-sync`.
The source branch may progress after this pinned audit. Reviewers should re-run
the two new checks and recheck the latest coverage snapshot before merging.
