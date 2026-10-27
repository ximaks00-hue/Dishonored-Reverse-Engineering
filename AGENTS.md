# Agent notes for this repository

Evidence-led Dishonored research. Prefer reading over inventing. Never promote a tool suggestion to fact.

## Before changing research notes

1. Read [docs/research-status.md](docs/research-status.md) and [docs/gameplay/blink/activation-graph.md](docs/gameplay/blink/activation-graph.md).
2. Confirm build `10256413` / EXE SHA-256 in [research/builds/BUILD-STEAM-10256413/build.md](research/builds/BUILD-STEAM-10256413/build.md).
3. Use **claim** labels on findings: confirmed / observed / inferred / unknown / superseded / rejected (hypothesis-scoped).
4. Keep PowerWheel item `24`, UI enum `2`, active-array index `0`, and `_iPower` distinct.
5. Source of truth is the EXP body. Findings/status/DB are summaries — if they disagree with EXP, fix the summary.

## Where to write

| Artifact | Path |
| --- | --- |
| New procedure/results | `experiments/EXP-NNNN-slug.md` with YAML frontmatter |
| Short status / next actions | `docs/research-status.md` (keep short) |
| Session narrative | `docs/changelog.md` |
| Durable summaries | `docs/findings/` |
| Blink subsystem | `docs/gameplay/blink/` |

Frontmatter fields: `experiment_status` (`planned|in_progress|done|superseded`) and `claim_status` (`confirmed|observed|inferred|unknown|superseded|mixed|rejected`). Do **not** run `tools/normalize_experiment_status.py` (disabled; corrupted labels).

Template: [templates/experiment.md](templates/experiment.md). Checklist: [docs/tooling/session-checklist.md](docs/tooling/session-checklist.md).

## Tooling

- MCP matrix: [docs/tooling/mcp.md](docs/tooling/mcp.md). Deep RE → `user-ghidra-re-mcp`; offline index → `mcp_servers/static/server.py`.
- Path defaults: `mcp_servers/_paths.py`.
- Compressed UPK: summary/search only. Decompile against `assets/extracted/dishonored-blink/` (ignored).
- After EXP edits: `python tools/validate_experiments.py` then optionally `python tools/knowledge/sync_from_experiments.py`.

## Do not

- Commit game binaries, `.upk`, extracts, saves, or Ghidra lock files.
- Launch or patch the game solely to “verify” tooling unless the user asked for a runtime experiment with a recorded baseline.
- Merge rejected evidence graphs (e.g. Pawn manager ABI reject vs known UsePower) back into Blink activation without new discriminating evidence.
- Treat `FUN_00C0CA70` as rejected — it is open/weakened.
- Treat decompiler pseudocode as original source.
- Reinflate `docs/research-status.md` into a findings dump.
