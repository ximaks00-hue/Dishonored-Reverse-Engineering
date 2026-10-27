---
id: EXP-0137
title: Selected native class-table key groups joined to UELib class paths
experiment_status: done
claim_status: mixed
build: "10256413"
question: "How many exact-build class/table key pairs in selected sibling registration bodies can be linked by exact label to the all-install UELib class-path catalog?"
---

# EXP-0137 — Selected native class-table key groups joined to UELib class paths

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: seven selected decompiler bodies called directly by `FUN_009DD640`, with expression-level class/table key pairs; exact label joins against the EXP-0071 all-install UELib `Class'...'` path catalog.
- Exclusions: no table-length or full-handler enumeration, no complete NativeToken-to-handler mapping, no claim that all registration routines are covered, and no runtime execution/reachability or package-load proof. Decompiler output is not original source.
- Tools and inputs: exact-build read-only decompiler cache; `uelib-class-object-catalog.csv.gz`; [native_class_registration_group_census.py](../tools/native_class_registration_group_census.py).
- Durable outputs: [332-row class/table key catalog](../research/executable/evidence/EXP-0137-native-class-registration-group-uelib-join.csv) and [summary with per-group counts and input hashes](../research/executable/evidence/EXP-0137-native-class-registration-group-uelib-join-summary.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; use the recorded build ID and executable hash as the identity gate.
2. Read the cached decompiler results for `FUN_009DD640` and seven direct callees. The reproducer rejects a cache whose build ID or executable SHA-256 differs.
3. In `FUN_009DD640`, count distinct direct callees after excluding its own function label and verify that each selected callee is a direct call in the decompiler body. This parent body sets and clears bit `0x200` around its sequence of calls; no meaning is assigned to that bit.
4. Extract only explicit key, pointer-symbol, and helper-call patterns. For the six `FUN_00454FE0` groups, accept either a local key and pointer passed to `FUN_0044C310`, or a local key referenced by `FUN_00B699E0`. In `FUN_004811B0`, separately capture the `FUN_00449A10("Class",0,1)` construction, adjacent pointer-symbol assignment, and `FUN_00B699E0` call.
5. Join each exact class-key string to rows in the EXP-0071 catalog with a non-null `Class'...'` path; preserve catalog row and package counts.
6. Emit one row per matched key/table-symbol pair with decompiler cache and pseudocode SHA-256 values. Do not infer table length from symbol addresses.

## Observations

- `FUN_009DD640` has 16 distinct direct callees in the cached pseudocode (excluding itself) and directly calls all seven functions in this extraction. The body sets `DAT_01412958` with mask `0x200` and later clears that mask; its role is unknown.
- The extraction recovered 332 distinct function/key pairs and 332 distinct key strings across seven functions:

| Function | Pairs | Helper shape |
| --- | ---: | --- |
| `FUN_006067A0` | 174 | `FUN_0044C310` wrapper |
| `FUN_0096DAB0` | 11 | direct `FUN_00B699E0` |
| `FUN_00970A10` | 1 | direct `FUN_00B699E0` |
| `FUN_0099A100` | 5 | direct `FUN_00B699E0` |
| `FUN_009AE330` | 1 | direct `FUN_00B699E0` |
| `FUN_00A0DBF0` | 135 | 51 direct `FUN_00B699E0`; 84 `FUN_0044C310` wrapper |
| `FUN_004811B0` | 5 | separate `FUN_00449A10` key factory, direct `FUN_00B699E0` |

- All 332 keys have exact label matches to at least one UELib `Class'...'` path. The matching rows total 11,141 and cover 844 distinct UPK paths in the 904-package catalog.
- The 327 `FUN_00454FE0` keys and five `FUN_00449A10` keys remain separate construction forms in the output. The CSV preserves the function, helper, key, pointer-symbol label/address suffix, decompiler cache hash, and UELib catalog matches.

## Interpretation and claim limits

- **Observed:** the exact-build decompiler output contains the extracted key/pointer/helper argument patterns in seven functions directly called by `FUN_009DD640`; every extracted key has an exact UELib class-path label match.
- **Inferred, narrow:** these functions provide build-specific associations between class-like keys and native-table-like pointer symbols. The pattern is consistent across multiple groups, but table contents and engine-level registration semantics are not established.
- **Unknown:** the meaning of the two key factories, helper storage/lookup behavior, table layout and length, token-to-entry conversion, runtime execution, and whether each UELib class path is the runtime owner of the associated native table.
- **Alternative explanations:** decompiler local-variable recovery may obscure argument roles; exact text equality can establish a label join without proving identity or runtime ownership; the sibling functions may perform initialization work beyond the extracted patterns.
- **Evidence that could change these claims:** read-only machine-code/dataflow inspection can validate helper argument flow and symbol targets; independently verified table extents and repeatable matching-build runtime observations are needed for table-use or dispatch claims.

## Reproduction and limitations

- From the repository root, run `python tools/native_class_registration_group_census.py`.
- The tool validates the build/hash identity stored in each decompiler cache, hashes each input cache and the class catalog, enforces the explicit extraction patterns and direct-call gate, then regenerates the CSV and JSON summary.
- No reset is required. The outputs are derived text catalogs and can be regenerated in place.
- The census is limited to seven selected bodies and the EXP-0071 UELib class catalog. A label join does not validate serialized class semantics, pointer contents, table boundaries, or runtime use.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior single-group studies: [EXP-0066 NativeToken handler candidates](EXP-0066-uelib-native-token-to-executable-handler-join.md), [EXP-0067 class/table handoff](EXP-0067-native-exec-class-table-handoff.md), [EXP-0075 helper trace](EXP-0075-native-class-table-registration-helper.md), [EXP-0076 class-label join](EXP-0076-native-class-table-uelib-class-join.md)
- UELib class catalog: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Function evidence overlay: [EXP-0128](EXP-0128-audio-request-queue-submission.md)
