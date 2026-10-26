# Research handbook

This handbook describes how the project gathers, records, and connects evidence about Dishonored. It does not claim that uninspected local files or builds have been analyzed.

## Research layers

1. **Digital archaeology:** identify installations, files, package metadata, resources, and dependencies.
2. **Behavior and binary research:** document repeatable in-game observations and analyze script/native structures against a known build.
3. **Independent reconstruction:** specify and implement selected behavior only after its observable contract and evidence are documented.

The layers can overlap, but conclusions at one layer must not be presented as proof about another. For example, an exported package object name does not establish runtime behavior.

## Navigation

- [Current status and initial questions](research-status.md)
- [System architecture map](architecture/overview.md)
- [Evidence and provenance policy](methodology/evidence.md)
- [Research workflow](methodology/workflow.md)
- [Long-term roadmap](roadmap.md)
- [Glossary](glossary.md)
- [Research record schema](../schemas/research-record.schema.json)

## Subsystem documentation

Create subsystem pages when evidence exists. Use [the subsystem template](../templates/subsystem/overview.md) as a starting point; do not create empty pages that imply coverage.
