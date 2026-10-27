# Research status

**Status:** This is an active, incomplete reverse-engineering project scoped to Steam x86 build `10256413`. The exact-build identity is recorded in [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md). The [roadmap](roadmap.md) defines the full project scope; detailed denominators are in [coverage](coverage.md).

## Current evidence

- Package metadata and structural catalogs cover all 904 installed UPKs; payload and bytecode completeness vary by parser and package. See [coverage](coverage.md) and the cited EXPs.
- The exact-build executable index contains 72,437 internal functions. The EXP-0156 local sync snapshot reports L0=72,382, L1=51, L2=4, L3=0, and L4=0. These gates are not counts of semantically recovered code, and the SQLite ledger remains a generated local view.
- The separate EXP-0139 catalog has 254 indexed class-table targets; 20 have body reviews, while all 254 remain subsystem-unassigned and 234 remain body-unreviewed. EXP-0158 maps the shared helper's key/value bucket structure. EXP-0159 shows `FUN_0046E5C0` resolving a pointer either from a nonzero selector in virtual `.data` or, for zero, through the name-based registry; its context lookup shares the static helper called by the indexed `GetStackOwnerClass` symbol. The returned node's type, selector identity, caller, target invocation, and runtime use remain unknown. The manual overlay now has 49 reviewed bodies; runtime-verified function count is zero.
- Blink's static evidence graph remains split: E1–E3, E5–E6 and conditional E5a–E5b are confirmed; E4, E7, E8 and E10 remain open; E9 is rejected only as a UsePower route. Keep UI enum `2`, PowerWheel item `24`, active-array index `0`, and `_iPower` distinct.

## Next work

1. Resolve high-value ownership/dataflow gaps in the native class-table and Blink paths. Choose candidates by connected evidence and class clusters, not by address order.
2. Expand function coverage without converting decompilation or pointer/name matches into semantic claims. Maintain separate L0–L4, subsystem, edge, and runtime records.
3. Continue finite package/resource and configuration slices, retaining parser warnings and independent-check limits.
4. Add runtime evidence only from a matching build with a recorded baseline and user-started process; no current L4 evidence is recorded.
5. Keep summaries synchronized with EXP source records and the generated/local knowledge view.

## Navigation

| Need | Location |
| --- | --- |
| Project scope and work order | [roadmap](roadmap.md) |
| Detailed denominators and limits | [coverage snapshot](coverage.md) |
| Build/package baseline | [baseline findings](findings/baseline.md) |
| Blink findings and open graph | [Blink findings](findings/blink-native.md), [activation graph](gameplay/blink/activation-graph.md) |
| Evidence method | [evidence policy](methodology/evidence.md), [L0–L4 model](methodology/function-evidence-model.md) |
| Experiment workflow | [workflow](methodology/workflow.md), [session checklist](tooling/session-checklist.md) |
| Tools and local configuration | [MCP matrix](tooling/mcp.md) |
| All experiments | [`experiments/`](../experiments/) |
| Narrative history | [changelog](changelog.md) |

This page is intentionally brief. Add evidence and caveats to the EXP first; update this page only for material changes to current status or next work.
