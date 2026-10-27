---
id: EXP-0205
title: Reconcile legacy native body reviews and measure full lookup fan-in
experiment_status: done
claim_status: mixed
build: "10256413"
question: Can the eight exact-build raw body reviews in EXP-0158 be reconciled into the portable function-review overlay, and what is the complete indexed direct-call fan-in to `00938290`?
---

# EXP-0205 — Reconcile legacy native body reviews and measure full lookup fan-in

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: reconcile eight raw-body records already documented in EXP-0158 into the cumulative portable manual-review overlay; independently recheck the raw body of `00938290`; query all indexed direct callers of that function.
- Exclusions: this does not create eight new reverse-engineering findings. Seven body digests are carried forward from EXP-0158; only `00938290` was independently rehashed in this pass. A static caller edge does not establish runtime execution or common semantics.
- Tools: exact-build function index; Python 3.12, pefile 2024.8.26, Capstone 5.0.7 for the independent `00938290` recheck; offline callgraph snapshot exported 2026-10-26.

## Procedure

1. Re-read EXP-0158, resolve its eight raw-reviewed addresses and sizes against the exact-build function index, and verify its recorded hashes against the source experiment; independently rehash `00938290` from the registered executable.
2. Check each address against cumulative overlay EXP-0204; all eight were absent.
3. Rehash and fully decode `00938290` from the registered executable and compare its result with EXP-0158.
4. Query `callers(00938290, kind=call, limit=500)` and compare the returned row count with the dossier's embedded caller excerpt.
5. Add one portable L1 row per historical raw body review, retain EXP-0158 as the evidence source, and keep semantic/runtime status unchanged.

## Observations

- EXP-0158 already records raw body hashes and static byte-level observations for these eight exact-build functions. Exact indexed sizes and hashes are:

  | Function | Size | RVA | Raw body SHA-256 | Bounded operation recorded by EXP-0158 |
  | --- | ---: | ---: | --- | --- |
  | `00454FE0` | 30 | `00054FE0` | `7f48270762fe7380b3dd7fabe9964f0d897f4aef9f2a2e9670a692a6c6417ef8` | Calls a key-construction helper and returns the supplied local pointer; exact key representation remains limited by EXP-0158. |
  | `0044C310` | 57 | `0004C310` | `d673cdaeceac1a87a259d918bf35775954d07ffd8ca96dc1636d6bbc8e99c127` | Builds a two-dword key pair, calls the shared table handoff, and returns an address at record `+8`. |
  | `00B699E0` | 200 | `007699E0` | `bd2c81fa8ec5d93c741a0b6b0a13f644f4fd26ba840994272ebe30c030daf772` | Performs the documented lookup/update/insert path over 0x14-byte indexed records. |
  | `00938290` | 123 | `00538290` | `36fe1ac62cac3ade657b2e90e61f1b10f6436e83922c236b2345b5081c4a4425` | Looks up a two-dword key through a bucket and linked slot indices; writes the matched index or `0xFFFFFFFF`. |
  | `00423970` | 98 | `00023970` | `46b1b17964f1d1f21ad8e80f37bac38790032a360719b310d48facece3e615357` | Inserts an indexed slot at a bucket head and writes its chain and bucket indices. |
  | `009C6560` | 170 | `005C6560` | `46abfcf6cabe12aa202d36222d37adc665b8aa3219e43cd86df99e8dab937b57` | Obtains an indexed slot through a free-list or allocation path and sets its associated bit. |
  | `00C18870` | 150 | `00818870` | `09f0afc2d2e7a66b881f60c6321b7be86d69f1318e908186e9bb5f11f1cfc85b` | Grows a bucket-count field and requests bucket rebuild when required. |
  | `00C177E0` | 413 | `008177E0` | `6d4a32f38da36508e57d17b5be7dbbcec5a284129f4881b7e28eaa2c68c139a2` | Rebuilds bucket heads, indices, and chain links over indexed slots. |

- The independently rechecked `00938290` body decodes as 55 x86-32 instructions covering all 123 indexed bytes. Its raw SHA-256 matches EXP-0158 exactly. The instructions support the lookup shape summarized above; field ownership, registry type, size invariants, and runtime use are not established by this recheck.
- The callgraph snapshot contains 517,589 edges and records the same executable SHA-256 as the build record. The explicit caller query returns 53 direct-call rows from 49 distinct caller functions. Four caller functions contribute two sites each: `00428D40`, `00731710`, `007C6CF0`, and `007C9FD0`.
- `function_dossier(00938290)` embeds 30 caller rows. That is a bounded agent-pack excerpt; it is not the total fan-in. The explicit `callers` query returned 53 rows under a requested limit of 500, with no truncation indicated.
- Three caller bodies are already present in the review overlay: `0046E5C0` (EXP-0159), `009C6170` (EXP-0196), and `007C3BC0` (EXP-0204). Other caller edges remain static callgraph records, not body reviews.
- A useful next low-cost candidate is `0072E230`: its indexed body is 96 bytes and its caller query reports 30 incoming call rows. This is a triage lead based on connectivity and body size only; its role and those callers' relationships remain unknown.
- Reconciling the eight EXP-0158 body records expands the cumulative overlay from 239 to 247 unique bodies, or 0.340986% of 72,437 indexed functions. The EXP-0139 subset remains 148/254 with 106 unreviewed. This raises L1 analysis coverage only; no semantic or runtime level is added.

## Interpretation and claim limits

- **Observed:** EXP-0158 contains eight build-bound raw body hashes and instruction-level records; this experiment adds those prior reviews to the portable cumulative overlay and independently reproduces the `00938290` digest.
- **Observed:** the full explicit callgraph query returns 53 direct-call rows from 49 caller functions in the matching build-bound snapshot.
- **Observed tool limit:** the dossier embeds 30 caller rows, while the dedicated caller query returns the full 53 rows for the same target and snapshot. Use the dedicated query for fan-in counts.
- **Inferred, limited:** `0072E230` may be an efficient next body to inspect because it is 96 bytes and has 30 indexed incoming call rows; this ranking says nothing about its semantics.
- **Unknown:** caller argument meaning, runtime reachability, complete indirect callers, and the semantic identities of most callers.
- **Not established:** a direct call edge or high fan-in proves common subsystem ownership or runtime use.

## Reproduction and limitations

1. Verify the registered executable hash and each exact indexed function start and size.
2. Read EXP-0158 and recompute raw hashes for any carried-forward body; this experiment independently recomputed `00938290`.
3. Verify the callgraph SQLite snapshot reports 517,589 edges and the registered executable SHA.
4. Run the explicit caller query for `00938290` with a limit above 53; count edge rows and unique caller starts separately.
5. Treat dossier caller lists as bounded context excerpts unless they provide an explicit completeness guarantee.

This was read-only static analysis. No game process was used.

## Links

- Historical body evidence: [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md)
- Shared consumer evidence: [EXP-0159](EXP-0159-native-class-table-static-consumer-lookup.md)
- Prior caller body review: [EXP-0196](EXP-0196-eleven-window-dispatcher-callees.md)
- Call-neighborhood evidence: [EXP-0204](EXP-0204-call-neighborhood-around-007c3bc0.md)
- Evidence: [eight-row overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0205.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0205.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0205.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
