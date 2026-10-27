---
id: EXP-0203
title: Five compact callers converge through one target into a previously reviewed helper
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do five compact neighboring bodies share direct call edges to one unreviewed target and the previously reviewed helper at `0x00428B50`?
---

# EXP-0203 — Five compact callers converge through one target into a previously reviewed helper

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: body-review the 138-byte target `00594DE0` and five compact callers in the neighboring `0059BA90–0059BC50` range. The already body-reviewed target `00428B50` is used as a linked evidence node, not counted as a new review.
- Exclusions: these direct calls and repeated body shapes do not prove shared source-level semantics, ownership, or runtime execution. No method names are assigned.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; raw PE mapping, exact-build function index, and offline callgraph.
- Baseline: the EXP-0202 cumulative overlay held 228 unique reviewed bodies; all six newly reviewed starts were absent. `00428B50` was already reviewed in EXP-0196.

## Procedure

1. Verify the registered executable hash, resolve each new body to its exact indexed start and inclusive size, and confirm it is absent from EXP-0202.
2. Hash and fully decode all six bodies as x86-32. Record their direct call sites and normalize raw body bytes by zeroing only Capstone-marked immediate and displacement fields.
3. Compare normalized sequences only for the four 106-byte candidate bodies; preserve raw hashes as unique identities.
4. Query the offline caller index for `00594DE0` and compare returned call sites against raw instructions in the selected bodies. Confirm `00428B50` is an existing EXP-0196 review before using it as a linked node.
5. Keep the new function records at L1 and the direct call edges as static relations; do not infer dataflow or behavior.

## Observations

- All six new bodies are exact indexed starts, absent from EXP-0202, and fully decoded. The target `00594DE0` is 138 bytes / 50 instructions; the five neighboring callers are 105 or 106 bytes.
- `00594DE0` contains one direct call, `00594E2A → 00428B50`. The latter function is already body-reviewed in EXP-0196 (490 bytes; prior overlay SHA-256 `20902BB60EEB98A51A2A6672F97EAD594E04151164076B2FB13B31BC17BE7615`); this experiment does not add a second body-review row for it.
- All five compact callers directly call both `00594DE0` and `00428B50`:

  | Function | Size | Call to `00594DE0` | Call to `00428B50` | Raw body SHA-256 |
  | --- | ---: | --- | --- | --- |
  | `0059BA90` | 106 | `0059BAA1` | `0059BAD7` | `55CE6CDC7E0DD85C5FB587C6325614FD25DA910474DAA92D6E9013E473E4B895` |
  | `0059BC50` | 106 | `0059BC61` | `0059BC97` | `C9CADB11CAA0448ADA16998CA4AB01F4A12036B2D27AB7915E71561A0298533F` |
  | `0059BB00` | 106 | `0059BB11` | `0059BB47` | `9741186544213577028A93F6EF66A56DD038DCDC94D341DB921459208C9620E6` |
  | `0059BB70` | 106 | `0059BB81` | `0059BBB7` | `76FA9748AAF041D85ED4E4C389FA1854BD5DF5844AADFD9F8738F6862076CFAB` |
  | `0059BBE0` | 105 | `0059BBF1` | `0059BC27` | `3CFE2180658981740D332789E91C450B31570FE897FD5CB6F1C5652C443640B9` |

- The 106-byte bodies form two normalized pairs under the EXP-0197–0202 byte-masking recipe: `0059BA90` / `0059BC50` hash to `8F7E79B963A1F04B0DF0391EE4FB2E87FFAC5D5DE753B4C5116AB5A893B322B5`; `0059BB00` / `0059BB70` hash to `90BC56039E0365549DBAE194392B01F9B434B7BDFE597996F5C6E9F2514FD63B`. The 105-byte body `0059BBE0` has a distinct normalized hash, `BB88A2FE003A0EEADC72C91EBC3580F1C64F220B1A50EDF176834678E3560A46`.
- The offline caller index returns 14 call-edge rows from 13 caller starts to `00594DE0`; the selected five compact bodies are members of that set. A raw-body audit checked all 14 reported call sites. The offline caller query for the already reviewed `00428B50` returned 50 rows at its endpoint cap, so its complete fan-in remains unknown.
- The manual overlay rises from 228 to 234 unique body reviews, or 0.323039% of the 72,437-function index. All six new bodies are outside EXP-0139; its 148/254 review count is unchanged. No L2–L4 claims are added.

## Interpretation and claim limits

- **Observed:** five neighboring compact bodies each contain direct calls to both `00594DE0` and `00428B50`; the first target directly calls the already reviewed second target.
- **Observed:** four 106-byte callers form two normalized byte pairs; the 105-byte caller has a distinct normalized sequence. Raw body hashes are preserved for every function.
- **Inferred, limited:** this forms a useful static call neighborhood with two compact template families and an existing reviewed helper anchor. The calls do not prove dataflow, ownership, or shared high-level behavior.
- **Unknown:** the roles of the functions, meanings of arguments and globals, caller runtime reachability, and the complete fan-in to `00428B50`.
- **Not established:** normalized-byte equality or direct-call edges prove source names, semantics, or runtime behavior.

## Reproduction and limitations

With Python, pefile, Capstone, and the offline callgraph index available:

1. Verify the exact executable hash and indexed inclusive ranges.
2. Decode all six new bodies and verify instruction-size totals equal indexed sizes.
3. Recompute raw hashes and normalized byte hashes by zeroing only Capstone `disp_offset/disp_size` and `imm_offset/imm_size` spans without changing buffer length.
4. Verify the selected raw call operands target `00594DE0` and `00428B50`; confirm the latter's earlier EXP-0196 review rather than importing it twice.
5. Query callers of both targets, accounting for the caller endpoint cap on `00428B50`.

This was read-only static analysis; no Ghidra project or game process was used.

## Links

- Prior review of `00428B50`: [EXP-0196](EXP-0196-eleven-window-dispatcher-callees.md)
- Related call-graph batch: [EXP-0201](EXP-0201-four-candidate-functions-share-a-direct-call-target.md)
- Evidence: [six-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0203.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0203.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0203.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
