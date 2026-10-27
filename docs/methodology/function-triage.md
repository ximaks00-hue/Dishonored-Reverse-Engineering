# Native-function triage

Do **not** catalog every function before selecting a research question. First identify a gameplay, file-loader or subsystem behavior for which a function record would change the current explanation.

## Priority
Prefer functions that: (1) discriminate between hypotheses, (2) connect important subsystem boundaries, (3) reveal high-leverage types or call paths, (4) enable reproducible experiments. Defer generic library/thunk functions unless needed for call chain completeness.

## Minimum function record
- FUNC ID and narrowly descriptive provisional name;
- BUILD ID, module filename, SHA-256, architecture, RVA, analysis tool/version;
- discovery method and relevant callers/callees or cross-references;
- observed instructions/data accesses (summarized, not dumped), pseudocode caveats;
- hypothesis, supporting/contradictory evidence, unknowns and next distinguishing test.

Use [function template](../../templates/function.md). Names and inferred signatures are provisional until corroborated. Prefer focused call graphs to comprehensive low-value inventory.

## Accelerated neighborhood review

Use the [high-leverage review workflow](native-review-acceleration.md) and its reproducible native candidate queue to select clusters. A caller/callee discovered during one body's review is a lead, not an automatically analyzed function.
