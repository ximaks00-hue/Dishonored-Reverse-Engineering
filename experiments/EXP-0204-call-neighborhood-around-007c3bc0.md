---
id: EXP-0204
title: A compact caller neighborhood converges on 007C3BC0 and a reviewed helper
experiment_status: done
claim_status: mixed
build: "10256413"
question: What direct-call structure is present in `007C3BC0` and four compact indexed callers, and do the callers also reach the previously reviewed helper `00428B50`?
---

# EXP-0204 — A compact caller neighborhood converges on 007C3BC0 and a reviewed helper

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: five new exact-build function-body reviews: target `007C3BC0` plus four compact callers `007C4000`, `007C3D60`, `007C5910`, and `007C5D40`. All five were L0 and absent from the EXP-0203 cumulative overlay. The already reviewed `00428B50` is a linked anchor, not a new review.
- Exclusions: static calls and body-shape comparisons do not establish semantic roles, class ownership, runtime reachability, or shared source-level behavior. Names remain index-generated.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; registered executable, exact-build function index, offline callgraph, and raw PE mapping.
- Baseline: EXP-0203 records 234 unique body reviews. Neighbor `005D1270` was already reviewed in EXP-0202 and is not counted again.

## Procedure

1. Verify the registered executable hash, indexed function starts/sizes, and that the five selected starts are absent from the EXP-0203 cumulative overlay.
2. Fully decode each selected body as x86-32, calculate raw and normalized SHA-256 hashes, and collect every direct-call site and target.
3. Query the indexed incoming edges to `007C3BC0`; distinguish the five selected bodies from already reviewed `005D1270` and the remaining callers.
4. Compare calls to `00428B50` with its prior EXP-0196 raw-body review; account for the endpoint cap on its incoming-edge query.
5. Keep all five new records at L1. Record no semantic, dataflow, or runtime claim.

## Observations

- The five bodies fully decode to their indexed sizes and have distinct raw and normalized hashes:

  | Function | Size | RVA | File offset | Raw body SHA-256 | Normalized SHA-256 |
  | --- | ---: | ---: | ---: | --- | --- |
  | `007C3BC0` | 67 | `003C3BC0` | `003C2FC0` | `da97f4dab44cab05fafeebdd70c1f11ebb6219507c0fc1d9f2625ef0daa81fa4` | `161c5bebddfd64970dcca57c100c9448c016c9fbf00cf19b875f55550af9404d` |
  | `007C4000` | 109 | `003C4000` | `003C3400` | `4d2b2229bee27b1fb3a1baf80f45d87cc91fa19bcf11e0f3a0a14597d933e3d9` | `d604feefedd3d209dfeb48433e5e55cc5b51209bf26e297fcae52c890ca1f934` |
  | `007C3D60` | 311 | `003C3D60` | `003C3160` | `f2128d120ce1266defa195442d9e7122a03f419b3d9df4e78cfb7602f2e771ee` | `223d8e8c00c6a41ed223f457ca70b6c7d06cfea0c9b977d6ee9d9c0790345eb9` |
  | `007C5910` | 223 | `003C5910` | `003C4D10` | `c64fdaeb55666c0fd79a5e300635224757b98a25e5e46de46cd16d94121d094a` | `65b2cfddf0b42dd0a33839cf641bab8b04376a08cfaea365d7757973abe8fcb5` |
  | `007C5D40` | 417 | `003C5D40` | `003C5140` | `21c3af58975c92d55dc061d9f6517f709ccdf81085daf5a2adae413e236eed5e` | `690c9af3541d6684555ebcdc8397263c4c74b8f18a0cdee09d18603911d5b8ae` |

- Their direct calls are:

  | Function | Direct call sites → targets |
  | --- | --- |
  | `007C3BC0` | `007C3BD2 → 00938290` |
  | `007C4000` | `007C401E → 007C3BC0`; `007C4051 → 00428B50` |
  | `007C3D60` | `007C3DDD → 00428B50`; `007C3DFA → 007C3BC0`; `007C3E28 → 00428B50`; `007C3E6C → 00428B50`; `007C3E82 → 007AA9A0` |
  | `007C5910` | `007C5968 → 00428B50`; `007C5987 → 007C3BC0`; `007C59C2 → 00428B50` |
  | `007C5D40` | `007C5DA5 → 00569E50`; `007C5DCE → 00731CE0`; `007C5DE4 → 007C3BC0`; `007C5E39 → 00718190`; `007C5E4B → 0050D270`; `007C5E80 → 00428B50`; `007C5E9C → 007AE760`; `007C5EB4 → 00418B50` |

- The offline callgraph reports 11 incoming call edges to `007C3BC0`, one from each of 11 caller starts. Four selected callers are in this experiment; `005D1270` was reviewed in EXP-0202; five other callers are larger bodies and remain for later triage. `007C3BC0` has one indexed outgoing direct call, at `007C3BD2 → 00938290`.
- All four selected callers also directly call `00428B50`, which was reviewed in EXP-0196 (490 bytes; raw SHA-256 `20902bb60eeb98a51a2a6672f97ead594e04151164076b2fb13b31bc17be7615`). A caller query for `00428B50` returned 200 rows at the endpoint cap; total fan-in remains unknown.
- The five normalized hashes are all distinct. This package is connected by indexed direct-call relationships, not by a repeated normalized-body template.
- The EXP-0203 cumulative overlay rises from 234 to 239 unique reviewed bodies, or 0.329942% of the 72,437-function index. All five new bodies are outside EXP-0139, which remains at 148/254 reviewed with 106 body-unreviewed. No L2–L4 claims are added.

## Interpretation and claim limits

- **Observed:** four selected compact callers each contain a direct call to `007C3BC0` and a separate direct call to the previously reviewed `00428B50`.
- **Observed:** `007C3BC0` contains a direct call to `00938290`. EXP-0158 had already established the callee's raw static two-key bucket-chain lookup operations; this call edge alone does not identify the caller's arguments or runtime use.
- **Inferred, limited:** this is a useful bounded call neighborhood and a repeatable triage unit. The relation graph can help select further callers or the callee for review.
- **Unknown:** meanings of the five functions and their arguments, ownership, dataflow, runtime reachability, and complete fan-in to `00428B50`.
- **Not established:** callgraph connectivity proves shared behavior, subsystem ownership, or execution during gameplay.

## Reproduction and limitations

With the registered executable, Python, pefile, Capstone, and the offline callgraph index available:

1. Verify the executable SHA-256 and resolve each function start, RVA, file offset, and inclusive size from the PE and exact-build index.
2. Fully decode the five bodies and recompute raw body hashes.
3. For normalized hashes, make a same-length copy and zero only Capstone-marked `disp_offset/disp_size` and `imm_offset/imm_size` spans; do not insert or remove bytes.
4. Verify the direct-call operands and call sites in raw instruction bytes.
5. Query callers of `007C3BC0` and `00428B50`; treat returned rows as an index snapshot and account for the 200-row cap on the latter endpoint.

This was read-only static analysis; no game process was used.

## Links

- Prior reviewed helper: [EXP-0196](EXP-0196-eleven-window-dispatcher-callees.md)
- Neighboring reviewed caller: [EXP-0202](EXP-0202-two-new-native-body-families-share-distinct-call-targets.md)
- Previous call neighborhood: [EXP-0203](EXP-0203-compact-callers-converge-on-reviewed-shared-helper.md)
- Evidence: [five-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0204.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0204.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0204.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
