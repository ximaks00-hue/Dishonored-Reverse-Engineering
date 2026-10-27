# Claims, uncertainty and conflicts

Each durable claim must answer: **what**, **where**, **how observed**, **under which conditions**, **what alternatives remain**, and **what test could disprove it**.

## Vocabulary
- **Observed:** a procedure produced a recorded result for specified inputs and conditions.
- **Confirmed:** a narrowly scoped conclusion supported by direct traceable evidence and/or independent repetition adequate for that conclusion; not a universal claim.
- **Inferred:** explanatory model consistent with evidence, still distinguishable from alternatives.
- **Unknown:** not measured or unresolved.
- **Superseded:** historical conclusion replaced by an identified later record.
- **Planned:** work proposed, no outcome yet.

Never convert a search hit, symbol name, file name, or decompiler pseudocode into proof of actual runtime use. Negative evidence is scoped to the search method and coverage. A status belongs to the precise claim, not to the whole subsystem.

## Evidence chains
Use `EXP` for procedure and outputs, `OBS` for measured observations, `HYP` for competing models, `FIND` for synthesized narrow conclusions, `BUILD` for environment identity and `FUNC` for native functions. Reference stable IDs and path anchors. If underlying raw data cannot be committed, store SHA-256, locally reproducible acquisition instructions, summary counts and validation steps; never fabricate availability.

## Confidence
Avoid arbitrary numerical confidence percentages. Explain why a conclusion is supported, what cases were covered and what could falsify it. If numeric confidence is used in a machine record, define the calibration model alongside it; do not treat analyst intuition as probability.

## Corrections
Do not silently rewrite an incorrect interpretation. Link the correcting record, note what changed and preserve superseded context. Contradictory observations may be caused by distinct builds, environments, or uncontrolled conditions.

## Hypothesis intake and independent confirmation
Accept a hypothesis for investigation only when the question is scoped, alternatives predict distinguishable outcomes, prerequisites and controls are explicit, and at least one result could falsify or weaken the model. This is an intake decision, not evidence that the hypothesis is true.

Use **confirmed** only for a narrow claim supported by traceable, scope-adequate evidence as defined above; direct evidence can be sufficient without a second implementation. When a result is described as **independently reproduced/confirmed**, the checker must be a different contributor from the evidence author. An independent reproduction starts from cited sources and uses a second implementation, a separately collected measurement, or another distinct check; merely rerunning the same generator is a repeat, not an independent implementation. Record reviewer, build/input identity, method, outcome, discrepancies and limits in a [review record](../../templates/review.md). If the reviewer cannot obtain the same build or inputs, mark the check partial, blocked or not reproduced and keep the claim status bounded. See the [contributor playbook](../contributor-playbook.md).
