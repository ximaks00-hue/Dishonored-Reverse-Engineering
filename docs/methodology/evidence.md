# Evidence and provenance

Every durable finding must be traceable to the exact build and the method that produced it. Never promote a plausible explanation to fact because a tool or model suggested it.

## Record the scope

For each finding, include as applicable:

- build ID and executable/package hash;
- exact file path and relevant offset, export, object, or module-relative RVA;
- tool name, version, options, and parser limitations;
- procedure, inputs, environment, and observed output;
- source reference, capture, or generated artifact location;
- confidence/status and the next check that could falsify the interpretation.

## Separate observation from interpretation

Write what was directly measured first. Add interpretations separately and label them **inferred** until a test distinguishes them from alternatives. A runtime observation confirms behavior only in its documented conditions.

## Contradictions and revisions

Keep prior records. Mark a conclusion superseded, add the new evidence, and explain whether the difference came from build, environment, procedure, or an earlier mistake.

## Handling game data

Commit research notes, scripts, small synthetic test inputs, and permitted metadata. Do not commit game executables, package contents, extracted assets, saves, or other copyrighted payloads. Local exports belong in ignored `assets/extracted/`.
