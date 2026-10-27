# Research session checklist

## Start

1. Confirm build: EXE SHA-256 matches [BUILD-STEAM-10256413](../../research/builds/BUILD-STEAM-10256413/build.md).
2. Skim [research status](../research-status.md) next actions and [activation graph](../gameplay/blink/activation-graph.md).
3. Note which MCP servers are live; workspace paths per [mcp.md](mcp.md).
4. Open a new `EXP-NNNN` from [templates/experiment.md](../../templates/experiment.md) with YAML frontmatter before changing notes mid-flight.
5. For native-function work, use the [function evidence model](../methodology/function-evidence-model.md): index/decompile coverage is separate from confirmed role, dataflow, and runtime claims.

## During

- Separate **Observations** from **Interpretation**.
- Label claims confirmed / observed / inferred / unknown / superseded; use `experiment_status` + `claim_status` in frontmatter.
- Keep wheel `24`, UI `2`, active index `0`, and `_iPower` distinct.
- Do not merge E9 (ABI reject vs UsePower) or treat E8 as rejected; update overview/graph if EXP changes.
- Keep copyrighted payloads out of Git; write under ignored `assets/extracted/` / `.tmp/`.

## End

1. Finish the EXP record (status, links, falsification notes).
2. Update [findings](../findings/README.md) or Blink overview **only** for new confirmed bullets / open questions.
3. Append a short note to [changelog.md](../changelog.md) if the session produced a narrative update.
4. Refresh [research-status.md](../research-status.md) next actions (keep it short).
5. Run `python tools/validate_experiments.py`.
6. Optionally `python tools/knowledge/sync_from_experiments.py` to refresh SQLite.
