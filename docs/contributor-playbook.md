# Contributor playbook

This page turns the research workflow into small tasks and reviewable evidence. Start with the [open contributor tasks](contributor-tasks.md); you do not need a game installation for every task.

## Worked examples from this repository

### A well-scoped experiment: EXP-0114

[EXP-0114](../experiments/EXP-0114-config-path-candidate-audit.md) is a useful model for an offline, build-bound audit:

- Its frontmatter identifies the record, title, lifecycle status, claim status, build and a single answerable question.
- The scope names the exact input catalog, manifest, candidate bases and exclusions.
- The procedure is reproducible, and the observed counts are separated from interpretation.
- The conclusion says what the filesystem matches show and explicitly leaves runtime config resolution unknown.
- The tool, inputs, outputs and build record are linked; the reproduction command uses a local game tree without committing it.

The core discipline is visible in its summary: ten present `BasedOn` candidates are an observation about one install snapshot, not proof of which base the engine loads. Follow this pattern when writing new EXPs. The [experiment template](../templates/experiment.md) is the starting point; the complete EXP body remains the source of truth.

### A testable hypothesis: Blink update scheduling

The [Blink graph](gameplay/blink/activation-graph.md#next-discriminating-checks) records Blink `+0x13C` dispatching to `+0x1B0` on the same receiver, while the engine caller remains unknown. The following is a worked proposal, not an adopted claim or assigned HYP ID:

```text
ID: reserve an unused HYP ID when the issue is accepted
Status: planned
Build: Steam x86 10256413, EXE SHA-256 in BUILD-STEAM-10256413
Question: Which outer dispatcher, if any, invokes Blink's +0x13C update on a Blink/Transversal receiver?
Hypothesis: An engine update scheduler invokes +0x13C on the component as part of its update path.
Alternative: A gameplay/event path invokes the slot, or the apparent generic dispatch candidate has a different receiver.

Predictions:
- Scheduler model: a caller/dataflow path reaches the slot with a receiver proven to be Blink or Transversal.
- Alternative model: the candidate call is event-driven or its receiver is another class. A bounded search that finds no scheduler path is inconclusive by itself.

Test: trace candidate outer dispatchers to the concrete vptr/class evidence; record the search coverage and rejected candidates.
Falsifier for a specific candidate: a complete path shows that candidate uses a non-Blink receiver; this rejects that candidate, not every possible scheduler path.
Limits: a failed static search does not prove the slot is never called; TickGroup metadata alone is not a caller.
Sources: EXP-0045, EXP-0046, EXP-0051; Blink activation graph E6b.
```

Use [the hypothesis template](../templates/hypothesis.md) for the submitted record. A hypothesis is **accepted for investigation** when it is scoped, has a meaningful alternative, and has a feasible test with distinguishing outcomes. That editorial decision does not accept the hypothesis as true. Keep it `planned` until evidence changes its claim status.

### A narrow finding: separate Blink and Swarm receivers

[EXP-0042](../experiments/EXP-0042-candidate-position-producer-consumer.md) is an example of evidence supporting a scoped conclusion. Its static evidence identifies the studied writer as a DevouringSwarm receiver and explicitly rejects the proposed same-instance join to Blink. It retains the shared-offset observation, separates the Blink consumer path, and names what remains unknown.

A durable FIND derived from this evidence should preserve that scope:

```text
Claim: The producer chain examined in EXP-0042 is a DevouringSwarm receiver path, not a same-instance Blink target writer.
Status: confirmed (static class-check and receiver provenance, limited to the examined chain)
Build: Steam x86 10256413; use the EXE SHA-256 recorded in BUILD-STEAM-10256413.
Scope: FUN_00BFAFD0 → FUN_00BF8C00 path and comparison with Blink's FUN_00BFC990 consumer.
Sources: EXP-0042, including the DevouringSwarm IsA descriptor, call-site ECX setup, and Blink/Swarm vtable slots.
Interpretation: the shared +0x60/+0x64/+0x68 offsets do not establish a shared object.
Limitations: does not exclude a different Blink target writer or establish input-to-Blink activation.
Falsifier: evidence that the examined producer chain passes a Blink receiver through its class check and same-instance call path.
Revision: supersedes the Blink-owner inference in EXP-0039; it does not erase EXP-0039's recorded raw observations.
```

This is a worked summary of the existing EXP, not a new assigned FIND record. Add the author/date from the actual contribution and preserve the exact source EXP wording when creating a record. See the [FIND template](../templates/finding.md) and current [Blink synthesis](findings/blink-native.md).

## Hypothesis and finding acceptance

There are two separate review decisions:

1. **Accept for investigation:** the question is bounded; the build or missing-build limitation is explicit; competing explanations predict distinguishable results; inputs, controls and a feasible procedure are named; and at least one result could weaken or falsify the favored explanation. Hypotheses do not need to be likely to be useful.
2. **Accept a research result:** the EXP records what was measured separately from interpretation; source identity and method are traceable; alternatives and search coverage are stated; and the result is reproducible to its stated scope. A null or contradictory result can pass this review. A separate contributor must perform the independent check before a result is described as independently reproduced or confirmed.

Do not use “accepted hypothesis” to mean “confirmed.” Assign status to each claim: `observed`, `inferred`, `confirmed`, `unknown`, `superseded`, or `rejected` with the rejection scoped to the tested hypothesis. Keep machine-readable confidence absent unless a calibration reference is defined.

## Independent confirmation

- The contributor who produced the evidence does not independently confirm their own result. A different contributor reviews the PR and records their GitHub identity in the review or research note.
- The reviewer starts from the linked source files and procedure. For an independent reproduction, do not merely inspect the original generated output or rerun the original generator; use a second implementation, a separately collected measurement, or an explicitly independent check appropriate to the claim.
- Match the same build and input hashes when the claim is build-scoped. Record commands, tool versions, environment, selected cases, result and discrepancies. If exact inputs are unavailable, classify the result as not reproduced or partially checked; do not silently substitute another build.
- For runtime claims, use the documented baseline and conditions. Do not launch or patch the game solely to check tooling. The reviewer should not request copyrighted files; hashes and safe summaries are enough.
- Use [the review template](../templates/review.md) for a durable independent check under `docs/reviews/`. A review can conclude `reproduced`, `partially reproduced`, `not reproduced`, or `blocked` and must say what it establishes. “Confirmed” remains limited to the reviewed scope.

The repository requires an approving review before changes merge to `main`. That protects the review step; it does not by itself make every research claim confirmed. Link the independent evidence and its limitations in the PR.
