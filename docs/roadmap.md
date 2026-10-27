# Roadmap

Stages are gates in the research process, not time estimates. Work can overlap when the necessary baseline exists.

The [progress dashboard](progress-dashboard.md) gives the current evidence maturity by direction. It complements this stage-based roadmap; it does not convert the stages into completion percentages.

| Stage | Focus | Exit evidence |
| --- | --- | --- |
| 00 Research foundation | Select build, establish provenance and repository conventions | Build record, hash manifest, research question, reproducible environment notes |
| 01 File and package archaeology | Inventory files and characterize package parsing | File manifest, tool compatibility notes tied to tested files, package map with coverage limits |
| 02 Script and object reconstruction | Inspect available script/object metadata | Catalog with source/build links, unresolved areas explicit |
| 03 Gameplay and AI | Study mechanics through repeatable vertical slices | Behavior specifications and experiments that can be repeated on a named build |
| 04 Native code | Map selected functions, types, and call relationships | Build-specific function records, evidence links, known analysis limitations |
| 05 Independent reconstruction | Reimplement selected, well-specified behavior | Independent module and comparison cases with documented scope |

## Progress measures

Report coverage with denominators and scope: files inventoried / files in manifest; packages parsed / packages in manifest; functions reviewed / indexed functions in the selected module; mechanics with repeatable procedures / mechanics selected for study; and findings with traceable evidence / findings recorded. Unknown areas remain visible.

For current source-linked counts and open blockers, see the [coverage snapshot](coverage.md) and the workstream pages linked from the [dashboard](progress-dashboard.md).

## Next milestone priorities

Use the ordered [dashboard priority list](progress-dashboard.md#next-milestone-priorities) for the next work cycle. The first gates are cache identity completeness and matching-build enforcement for runtime records. A narrow runtime experiment follows with its own recorded baseline; targeted native-cluster reviews, catalog provenance, and independent reproduction then expand the evidence base. These are priorities, not time estimates.
