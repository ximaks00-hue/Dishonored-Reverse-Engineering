# Research status

Updated: 2026-10-27. Scope: Steam x86 build `10256413`; see the [build record](../research/builds/BUILD-STEAM-10256413/build.md). The primary source is each EXP body; this page summarizes current coverage.

## Available evidence

- The corpus contains 155 EXP records, EXP-0001–0155. See the [published evidence index](published-evidence.md) and [coverage snapshot](coverage.md).
- The recorded build register binds Steam x86 build `10256413` to executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; the binary and game installation are not in Git.
- EXP-0114 and its analysis script report 63 syntactic path candidates from 76 config directives, ten Engine INI candidate matches, and four localization-directory matches against a hash-listed local manifest. This is **observed filesystem candidate matching**, not evidence for runtime config resolution.
- The exact-build native-function index contains 72,437 functions. The cumulative static body-review overlay through EXP-0155 has 47 entries; these are not runtime-verified, and role/owner claims retain their EXP-specific confidence.
- EXP-0139 has a 254-address class-table pointer/name candidate catalog; 19 received body reviews and 235 remain body-unreviewed. Pointer/name joins do not by themselves prove ownership or dispatch.
- No runtime-verified function count is recorded. Static edges do not establish runtime reachability.

## Immediate blockers
1. Close high-value native ownership/dataflow gaps using evidence that distinguishes candidate explanations.
2. Test competing `BasedOn` resolution models with a discriminating observation; current path presence does not establish runtime behavior.
3. Add runtime records only from the matching build and a documented baseline.
4. Keep experiment procedures and generated catalogs reproducible while leaving game files, extracted assets, and local databases outside Git.
5. Resolve licensing and contribution scope in the project notice before accepting substantial code contributions.

## Measurement policy
Progress is reported by well-scoped denominators and build IDs: examined files out of an explicitly defined manifest, repeatable experiments out of chosen questions and evidence-backed claims out of reviewed findings. Document volume is not completeness.

See [research backlog](backlog.md), [onboarding](onboarding.md), and the [roadmap](roadmap.md).
