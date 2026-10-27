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
