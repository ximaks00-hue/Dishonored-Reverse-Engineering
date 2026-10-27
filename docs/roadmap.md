# Roadmap

This roadmap defines the project scope and work order. Stages are evidence gates, not time estimates. The project is incomplete; see the [current status](research-status.md) and [coverage snapshot](coverage.md).

## Scope

The current reference build is Steam x86 `10256413`, identified in [the build record](../research/builds/BUILD-STEAM-10256413/build.md). Findings must name other builds explicitly. The goal is to reconstruct the game's systems and behavior from available evidence across files, packages, script/object metadata, native code, runtime observations, and selected independent implementations. A catalog, function count, or successful parser run does not by itself complete a system.

## Research stages

| Stage | Work | Evidence needed to advance |
| --- | --- | --- |
| 1. Build and files | Identify executable, modules, packages, resources, configuration, and provenance | Hash-bound manifests and documented exclusions |
| 2. Package and resource models | Inspect object tables, properties, scripts, audio, textures, video, and other resource families | Per-format methods, denominators, failures, and independent checks where available |
| 3. Native code and structures | Map functions, owners, fields, calls, virtual slots, and data structures | Build-scoped index and evidence-backed clusters, with unresolved buckets explicit |
| 4. Cross-system behavior | Connect script, native, resource, configuration, and gameplay observations | A documented chain for each claimed relationship, retaining alternative routes |
| 5. Runtime contracts | Reproduce selected behaviors under named starting state and inputs | Matching build, preserved baseline, repeatable observations, and stated limits |
| 6. Independent reconstruction | Implement selected behavior from its evidenced contract | Inputs/outputs, comparison cases, and explicit scope; no claim of original source recovery |

## Completion contract

The full-project objective remains open until these deliverables are evidenced for the named scope or explicitly marked unavailable with reasons:

1. **Provenance and files:** account for installation, DLC, localization, configuration, and modded files; preserve hashes and provenance limits.
2. **Packages and resources:** inventory all 904 installed UPKs and relevant non-UPK families; report parse/read/export coverage and failures by format/package.
3. **Script and object metadata:** provide searchable class, function, enum, struct, default-object, inheritance, and reference catalogs; distinguish missing, native-only, and unreadable bodies.
4. **Native executable:** reconcile the 72,437 indexed internal functions through evidence-backed subsystem/class clusters, named roles, or explicit unknown buckets. Retain exact-build addresses, ownership/dataflow evidence, and confidence; decompilation coverage alone is not semantic recovery.
5. **Runtime behavior:** define a finite set of important gameplay, UI, AI, and system behaviors; record repeatable experiments from a matching build and preserved baseline. Never infer runtime reachability from static edges.
6. **Cross-layer architecture:** connect package metadata, native paths, assets, configuration, and behavior only where evidence establishes each join. Keep contradictory and missing links visible.
7. **Independent reconstruction:** implement selected behaviors only after their observable contracts and comparison cases are documented. This does not imply source recovery.

Completion gates:

- Every reported number has a denominator, scope, source EXP, and known exclusions.
- Tool compatibility is measured by format and operation; metadata listing, property parsing, bytecode extraction, and asset export are separate claims.
- Function triage distinguishes indexed, analyzed, understood, connected, and runtime-verified levels. All unreviewed functions remain counted.
- Selected runtime behaviors have repeatable trials or a documented blocker and do not rely on static code alone.
- Open, weakened, rejected, and superseded hypotheses remain searchable and retain their evidence trail.
- Status and coverage summaries agree with their primary EXP records. Passing repository checks does not certify game-dependent results.

## Current work order

| Priority | Work package | Starting evidence | Next useful result |
| --- | --- | --- | --- |
| 1 | Recover owners and dataflow around shared native registration and dispatch | EXP-0066/0067/0075/0076, EXP-0137–0160 | Trace the owner/use of `FUN_0046E5C0` output `[EBX+0x9C]`; identify whether `[EBX+0x84]` maps to the selector table; trace startup reachability for the 33 statically matched Engine token registrations and extend the same audit to Core tokens; keep runtime claims separate; distinguish `NativeToken` declarations from `NativeFlag=true, NativeToken=0` class-table joins |
| 2 | Close high-value Blink activation gaps | [Activation graph](gameplay/blink/activation-graph.md), EXP-0027–0037, EXP-0043–0051 | Identify a discriminating caller/receiver or scheduler edge for E7; preserve E8 as open/weakened and E9 as rejected-as-UsePower |
| 3 | Expand native function understanding by connected clusters | [Coverage snapshot](coverage.md), EXP-0072 and current manual overlay | Rank candidates by missing relationships, repeated class edges, and falsifiable hypotheses; do not scan by address order |
| 4 | Continue package, resource, and configuration closure | EXP-0063–0105, EXP-0112–0136 | Resolve high-impact parser gaps and cross-layer candidates with independent checks and explicit parser limits |
| 5 | Establish runtime contracts | [Session checklist](tooling/session-checklist.md) and build record | Use a matching user-started process only with a recorded clean baseline and repeatable conditions |
| 6 | Reconstruct selected behavior independently | Stage 6 above | Begin only after the behavior contract and evidence limits are reviewable |

## Progress reporting

Use denominators such as files inventoried / manifest files, packages parsed / package files, functions analyzed / indexed functions, reviewed owners / selected candidate edges, and repeatable behaviors / behaviors selected. Keep these measures separate; do not summarize them as one completion percentage. Current measures and EXP links are in [coverage](coverage.md).

## Repository readiness

These project-delivery tasks remain open alongside reverse engineering:

- Recover the original local sources for EXP-0114 and other earlier records absent from the available GitHub corpus. Do not recreate experiment bodies from summaries.
- **Done on `6c6d055`:** repository evidence checks, REV-0004, and REV-0005 all passed on GitHub Actions. Enforcing them as required checks remains open until branch protection is available.
- Configure and verify `main` branch protection, required checks, a usable issue-label set, and collaborator access appropriate to the project's contributors.

## Experiment range

The current source corpus contains [EXP-0001 through EXP-0160](../experiments/). New experiments use the [template](../templates/experiment.md), and the repository validator checks IDs, statuses, and local references.
