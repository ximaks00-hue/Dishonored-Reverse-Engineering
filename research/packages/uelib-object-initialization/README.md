# All-install UELib object initialization profile

The 4,846 properties in EXP-0070 are initialization-only. EXP-0088 explicitly loads flagged objects across all 904 packages and records the expanded property output, failures, and diagnostics in the [on-demand coverage bundle](../uelib-on-demand-coverage/summary.json). This is still UELib parser output and needs independent payload validation.

Compact outputs from [EXP-0070](../../../experiments/EXP-0070-all-install-uelib-object-initialization-profile.md), covering all 904 UPKs in the build 10256413 manifest using Eliot.UELib 1.13.3.

- [`uelib-object-initialization-summary.json`](uelib-object-initialization-summary.json): aggregate object states/types, default-property and formatted reference-mention counts, group totals, and global console diagnostic counts.
- [`uelib-object-graph-summary.json`](uelib-object-graph-summary.json): derived-catalog row counts and equality checks against the source initialized-edge JSONL.
- [`uelib-object-initialization-by-group.csv`](uelib-object-initialization-by-group.csv): aggregate coverage by CookedPCConsole/DLC group.
- [`uelib-object-initialization-by-package.csv`](uelib-object-initialization-by-package.csv): per-package denominator, hashes/count reconciliation, object/default counts.
- [`uelib-unknown-object-export-class-counts.csv`](uelib-unknown-object-export-class-counts.csv): UELib `UnknownObject` rows grouped by package area and export-class label. Labels do not imply payload interpretation.
- [`uelib-class-object-catalog.csv.gz`](uelib-class-object-catalog.csv.gz): 133,660 package/object-type/class-label/class-path groups with examples and default-property row counts.
- [`uelib-inheritance-relations.csv.gz`](uelib-inheritance-relations.csv.gz): 5,355 UELib `Super` relations across package objects.
- [`uelib-initialized-object-relations.csv.gz`](uelib-initialized-object-relations.csv.gz): all 6,413,586 UELib-initialized object-field relation rows.
- [`uelib-property-type-reference-catalog.csv`](uelib-property-type-reference-catalog.csv): 3,896 object-type / parsed property-type reference groups, representing 13,138 source rows.
- [`uelib-default-property-reference-mentions.csv`](uelib-default-property-reference-mentions.csv) and [`uelib-unmatched-default-reference-mentions.csv`](uelib-unmatched-default-reference-mentions.csv): formatted-text reference mentions and the subset with no same-package object-path hit. They are parser-text mentions, not structured reference proofs.

Full generated JSONL and the run log live under ignored `assets/extracted/uelib-object-init-full/` and `assets/extracted/uelib-object-init-full-run.log`; the source corpus is not checked in.

Selected material property-view coverage was independently rechecked for `Moon_PMAT` and `Moon_HUB_Night_INST` in a fresh UELib initialization of exact-hash `L_Pub_Night_P.upk`. UELib emitted zero default-property rows; UModel `-dump` emitted a populated `Moon_PMAT` view and loaded two named textures. See [EXP-0086](../../../experiments/EXP-0086-uelib-material-property-payload-recheck.md). This is a parser-view discrepancy for two exports, not a conclusion about which decoder is complete or runtime dependency use.
