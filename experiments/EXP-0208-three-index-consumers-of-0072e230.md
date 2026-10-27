---
id: EXP-0208
title: Compare three index consumers of 0072E230
experiment_status: done
claim_status: mixed
build: "10256413"
question: How do three additional callers pass inputs to `0072E230`, and how are successful return values consumed?
---

# EXP-0208 — Compare three index consumers of 0072E230

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: raw x86 review of the complete indexed bodies at `00732AE0`, `00732CD0`, and `00732EA0`, each with a direct call to the previously reviewed `0072E230` helper.
- Exclusions: no class, subsystem, record, vector, key, or gameplay meanings are assigned. The pseudocode is used to navigate the body; raw call instructions confirm the hidden receiver and stack arguments.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; exact-build executable, function index, and callgraph snapshot.

## Procedure

1. Verify the registered executable SHA-256 and exact-build function index rows.
2. Map each VA to its PE file offset, hash the exact indexed bytes, and fully decode each body as x86-32.
3. Normalize same-length copies by zeroing only Capstone-marked immediate/displacement spans.
4. Inspect raw instruction windows at direct calls to `0072E230` and record receiver and stack-argument setup.
5. Trace the returned value only through the selected caller body; keep types and behavior claims open.

## Observations

All three selected bodies fully decode to their exact indexed size. RVA/file offsets use image base `0x00400000`.

| Function | Size | RVA | File offset | Raw body SHA-256 | Normalized SHA-256 | Call site |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `00732AE0` | 490 | `00332AE0` | `00331EE0` | `d5373893763cba33686ca2febc6b03ac5f7bebc838bdbd0fd033a9da00eedee9` | `444f1422c78289104924def94c67fbed0f949f7ad525faf15dd56ca67a1e5674` | `00732B27` |
| `00732CD0` | 460 | `00332CD0` | `003320D0` | `2257aa0c72623c7231ba6baa4eaa5a979692eecf63e02cbccbb64a7779bb8dbd` | `40e90a31d24f32a49baeae2dde4f379bf0e6e23a8a00c177182e7045c38689a7` | `00732D0B` |
| `00732EA0` | 492 | `00332EA0` | `003322A0` | `40931e21503ba7d9ee1e17055065a6fa3d96495c563749bbd8ddbaab4d1a1a09` | `9c372145765dd0263ab4aaee8a3c63b0c7bc98e4bbfe1c6e0aa8e7e1018accd7` | `00732EE6` |

- At each call site, raw x86 loads `[owner+0x1D4]` into `ECX`, checks it for null, pushes two DWORD values, and calls `0072E230`. The decompiler's apparent signatures omit the `__thiscall` receiver; the raw instructions establish it.
- `00732AE0` checks a zero/zero input pair, the receiver field, and the helper result against `-1`. On the successful path the result indexes a record table; the body reads a 16-byte value from the selected record and writes four DWORDs to the output area. The bytes do not establish the record or output type.
- `00732CD0` checks the input pair and receiver, then uses the helper result on successful paths. One branch uses the result with `0x20`-stride record storage and copies three DWORDs from a record region beginning at `+0x10`; another branch passes the result to `00718190` and copies fields at `+0x30`, `+0x34`, and `+0x38`. Counts and bounds guards are present. Mode and field meanings remain unknown.
- `00732EA0` checks the helper result against `-1`, then under another byte guard passes the returned value to `00718190` with a local buffer. Subsequent code reads triples of floating-point values at `0x10`-byte strides and computes a squared magnitude before writing output. The flag, buffer, and values are unnamed.
- The three functions had no prior semantic claims, analysis rows, or runtime evidence in their dossiers. They were L0 before this experiment; this review adds L1 body evidence only.
- Together with EXP-0206/0207, these callers provide repeated raw examples of a pair of stack DWORDs plus receiver `[owner+0x1D4]` passed to the same helper, with returned values used as guarded table indices or forwarded to another helper. This is a cross-caller static pattern, not proof of shared class ownership or runtime execution.
- The cumulative manual body-review overlay increases from 253 to 256 unique functions, or 0.353411% of 72,437. None of these three addresses belongs to the EXP-0139 target subset. No L2–L4 evidence is added.

## Interpretation and claim limits

- **Observed:** the three complete raw bodies each call `0072E230` with a receiver in `ECX` and two stack DWORDs.
- **Observed:** successful helper results feed record-indexed reads or a further call in all three selected callers.
- **Inferred, limited:** the lookup helper's result is used as an index-like value across multiple callers. Exact key construction, owner/registry identity, record types, and semantic role remain unknown.
- **Unknown:** names, class/subsystem ownership, runtime reachability, and user-visible behavior.
- **Not established:** that the three callers form one class, implement a named API, or execute during gameplay.

## Reproduction and limitations

1. Verify the executable hash and exact index sizes for all three VAs.
2. Recompute raw and normalized body hashes using same-length Capstone displacement/immediate normalization.
3. Decode each body completely and check raw call setup around `00732B27`, `00732D0B`, and `00732EE6`.
4. Trace selected return-value uses from the raw bodies; do not infer types from decompiler names or float operations alone.

This was read-only static analysis. No game process was used.

## Links

- Lookup helper and first caller group: [EXP-0206](EXP-0206-review-0072e230-bounded-lookup-accessor.md), [EXP-0207](EXP-0207-lookup-caller-dataflow-slice.md)
- Evidence: [three-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0208.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0208.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0208.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
