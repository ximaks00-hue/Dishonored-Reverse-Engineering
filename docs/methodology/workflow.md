# Research workflow

Work in **small vertical slices**. A successful experiment reduces uncertainty about a useful question rather than maximizing documents or analyzed function counts.

1. **Frame one question.** Define scope and which decision the answer will enable.
2. **Identify build.** Record edition, environment, binary hashes, architecture and local installation provenance where relevant. If not known, restrict the claim.
3. **Collect baseline.** Capture read-only manifests, tools and versions, commands, settings and initial conditions; keep copyrighted content local.
4. **List competing models.** Predict a distinct result for each whenever possible.
5. **Design controls.** Predefine inputs, cleanup/reset steps, repeat counts, measurement points and expected outcomes.
6. **Run and preserve observations.** Record actual outcomes independent of the interpretation, including null/failed results and parser warnings.
7. **Interpret conservatively.** State alternatives, coverage, falsification tests and confidence rationale. Don't infer runtime resolution from file-name matches.
8. **Publish references.** Connect BUILD, EXP, OBS, HYP, FIND or FUNC records and update status, never overwrite conflicting evidence silently.
9. **Peer review and reproduce.** Prefer independent verification before assigning 'confirmed'; record exact limitations and build variance.

## File/package archaeology
Inventory relative paths, sizes and hashes. Document parser/tool version, warnings, known false positives and which percentage of a **defined denominator** was inspected. Avoid inferring package compatibility from engine-family labels.

## Gameplay behavior
Describe starting save/state without uploading saves, controls and timing, repeated trials, visible results and environmental variance. Observed output does not establish a specific code path.

## Native analysis
Prioritize functions with high discriminatory value per [function triage](function-triage.md), record RVAs tied to module SHA-256 and provisional naming, and retain source-to-interpretation links without committing third-party decompiler dumps.

## Completion criteria
A task is complete when readers can locate sources, repeat the safe measurement, understand alternative explanations and tell precisely what remains unknown.
