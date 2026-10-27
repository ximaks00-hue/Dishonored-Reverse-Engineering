# Published research evidence

This index points to source records and machine-readable outputs committed with the research corpus. EXP bodies contain procedures, observations, claim labels, and limitations; generated catalogs are subordinate outputs. The exact game executable and extracted content are not distributed here.

## Registered build

- [Steam build 10256413 record](../research/builds/BUILD-STEAM-10256413/build.md) records the x86 executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- The [file manifest](../research/builds/BUILD-STEAM-10256413/files.csv) records relative paths, sizes, and hashes for the reported local installation snapshot. It does not mean the original files are included in Git or independently available to CI.
- [Build inventory EXP-0001](../experiments/EXP-0001-build-inventory.md) explains identity and scope limits.

## EXP-0114 — config path candidate audit

- [Experiment procedure and results](../experiments/EXP-0114-config-path-candidate-audit.md) are labeled **observed** and test syntactic path candidates against the recorded install manifest. They do not establish Unreal runtime config-resolution behavior.
- [Analysis tool](../tools/config_path_candidate_audit.py) verifies the executable SHA against the build record and file manifest before producing the outputs.
- [Per-candidate rows](../research/builds/BUILD-STEAM-10256413/config-path-candidate-audit.csv) and [summary](../research/builds/BUILD-STEAM-10256413/config-path-candidate-audit.json) preserve candidate bases, match status, and counts.
- Its input is the [EXP-0063 directive catalog](../research/builds/BUILD-STEAM-10256413/config-path-directives.csv); the procedure is reproducible only when the matching local install is available.

## Native functions

- [EXP-0072](../experiments/EXP-0072-exact-build-internal-function-subsystem-triage.md) defines the 72,437-function exact-build index and conservative triage limits; [the catalog](../research/executable/evidence/function-triage/internal-function-triage.csv) keeps unknowns explicit.
- The portable [per-function coverage CSV](../research/executable/evidence/function-triage/function-coverage-EXP-0155.csv) and [provenance manifest](../research/executable/evidence/function-triage/function-coverage-EXP-0155.json) can be regenerated from committed inputs with `python tools/export_function_coverage.py`; CI checks them with `--check`. They do not require the game executable, Ghidra, or SQLite. L3/L4 are explicitly unpublished in this export.
- The seven source-backed semantic records are in the [curated claims registry](../research/executable/evidence/function-triage/curated-function-claims-EXP-0155.json), rather than embedded in importer code.
- [Cumulative manual review overlay through EXP-0155](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0155.csv) contains 47 build-scoped body-review records. Review means static body analysis, not runtime verification or automatic semantic recovery.
- [EXP-0139](../experiments/EXP-0139-native-class-table-zero-token-handler-join.md) documents a 254-address candidate catalog created from class-table pointer edges and exact UELib export joins. Those joins alone are not proof of native ownership or dispatch.
- [EXP-0140–0155](../experiments/) record selected native body reviews, owners/slots still unresolved, and inference limits.

## Reproduction and contribution

Start with the [onboarding guide](onboarding.md), [evidence policy](methodology/evidence.md), and [function triage policy](methodology/function-triage.md). Run `python tools/validate_repo.py`, `python tools/validate_experiments.py`, and the documented unit tests before proposing a change. Tool runs requiring a game installation must name its build and hash and keep the installation, extracted assets, and local analysis databases outside Git.
