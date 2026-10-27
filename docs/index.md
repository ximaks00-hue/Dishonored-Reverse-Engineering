# Research handbook

This handbook explains the evidence process and points to the current primary records. It does not claim that uninspected builds, local caches, or connected services have been analyzed.

## Start with your task

| If you want to… | Start here |
| --- | --- |
| Join or review a contribution | [Contributing guide](../CONTRIBUTING.md) |
| See what is established and open | [Research status](research-status.md) and [coverage](coverage.md) |
| Choose the next project question | [Roadmap](roadmap.md) |
| Understand a gameplay claim | The relevant page in [findings](findings/README.md) and linked EXPs |
| Repeat or extend an experiment | [Experiment workflow](methodology/workflow.md), [template](../templates/experiment.md), and [checklist](tooling/session-checklist.md) |
| Analyze a native function | [Function evidence model](methodology/function-evidence-model.md), [executable index](../research/executable/README.md), and linked EXPs |
| Use project tools | [MCP and path setup](tooling/mcp.md) and [MCP server overview](../mcp_servers/README.md) |

## Research method

- [Evidence and provenance policy](methodology/evidence.md)
- [Research workflow](methodology/workflow.md)
- [Function coverage and L0–L4 evidence gates](methodology/function-evidence-model.md)
- [Architecture map](architecture/overview.md)
- [Glossary](glossary.md)

## Research record

- [Current status](research-status.md)
- [Measured coverage](coverage.md)
- [Completion scope and work order](roadmap.md)
- [Findings index](findings/README.md)
- [Session changelog](changelog.md)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
- [Experiment archive](../experiments/)
- [Research record schema](../schemas/research-record.schema.json)

## Subsystems

Create or extend subsystem pages only when evidence exists. Use the [subsystem template](../templates/subsystem/overview.md); do not create pages that imply coverage before it has been established.

- [Blink overview](gameplay/blink/overview.md)
- [Blink activation evidence graph](gameplay/blink/activation-graph.md)

## Audit history

Repository-wide documentation and contributor-readiness reviews belong under [`reviews/`](reviews/). Each audit must state the commit/scope inspected, checks actually run, exclusions, and unresolved risks.
