# Research status

Updated: 2026-10-27. Scope: public GitHub repository as inspected during this audit, with the community overhaul proposed on a separate branch.

## Verified in the audited published repository
The initial commit contains methodology, templates, roadmap, architecture notes and a JSON schema. It contains **no committed build record, experiment report, native function record or research script**. New process files on the proposed branch do not constitute new facts about game internals.

## Reported local work, not yet imported
Previous project discussion reported `EXP-0114-config-path-candidate-audit.md` and `config_path_candidate_audit.py` in a local workspace. Reported counts: 63 of 76 directives examined, ten `BasedOn` candidate matches to Engine INI files and four localization directory matches. Two base-path candidates yielded the same `BasedOn` matches. This is a *reported*, unverified summary; **the game's actual runtime resolution rule remains unknown**. Obtain the original report, data provenance and script before presenting any of it as verified GitHub research.

## Immediate blockers
1. Inventory a legally accessible game build with hashes, architecture, edition and conditions; never upload the installation.
2. Reconcile locally held experiments and scripts with published material using source review and reproduction.
3. Establish traceable evidence chains and distinguish observations from claims.
4. Design a test that differentiates competing `BasedOn` path models.
5. Choose a license with rights-holder/contributor considerations before inviting substantial code contributions.

## Measurement policy
Progress is reported by well-scoped denominators and build IDs: examined files out of an explicitly defined manifest, repeatable experiments out of chosen questions and evidence-backed claims out of reviewed findings. Document volume is not completeness.

See [research backlog](backlog.md) and [onboarding](onboarding.md).
