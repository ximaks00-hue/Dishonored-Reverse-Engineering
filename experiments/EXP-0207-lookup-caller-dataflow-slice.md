---
id: EXP-0207
title: Trace lookup receiver and key-pair use across five callers
experiment_status: done
claim_status: mixed
build: "10256413"
question: How do five compact callers set up `0072E230`, and what do they do with its returned value?
---

# EXP-0207 — Trace lookup receiver and key-pair use across five callers

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: raw x86 review of five full function bodies that directly call `0072E230`: `00731CE0`, `00731D10`, `00731DB0`, `00731F30`, and `007344A0`. The previous EXP-0206 target body is a reviewed anchor, not a new review here.
- Context only: `00730BD0` has two additional direct calls to the anchor. Inspection decoded 1,692 of its 1,693 indexed bytes; the final byte is an incomplete instruction, so this function is not added to the fully decoded body-review overlay.
- Exclusions: no names, class ownership, field types, bytecode meaning, table identity, or runtime behavior are asserted. Decompiled pseudocode is treated as a navigation aid; call receiver and argument setup below is checked against raw instruction bytes.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; exact-build executable, function index, and matching offline callgraph snapshot.

## Procedure

1. Verify the registered executable SHA-256 and exact-build index rows for all five selected function starts and sizes.
2. Map each VA to the PE file, hash its exact indexed body, fully decode it as x86-32, and compute a same-length normalized hash by zeroing only Capstone-marked displacement/immediate spans.
3. Inspect raw instruction windows at each direct-call site to `0072E230`, including the preceding stack pushes and ECX assignment.
4. Compare output/index use with decompiler pseudocode, retaining raw call setup as authoritative where decompiler prototypes omit the hidden `__thiscall` receiver.
5. Add only the five fully decoded bodies to the portable L1 overlay; do not promote candidate meanings or runtime claims.

## Observations

All five bodies fully decode to their exact indexed sizes. RVA and file offsets are for the registered PE image base `0x00400000`.

| Function | Size | RVA | File offset | Raw body SHA-256 | Normalized SHA-256 | Calls to `0072E230` |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `00731CE0` | 43 | `00331CE0` | `003310E0` | `888007b7acfb21049726e787c3f9f25f00747690a84f1a9f72baa5900673b501` | `6fd106e928a26c2fae3ed26884d40330fb7a157daf874b086c94c16b23d29e82` | `00731D01` |
| `00731D10` | 154 | `00331D10` | `00331110` | `528ff519be3af40e8afbcab07e85d17dc7351da459f8426756632ebbe318b34e` | `7252cfb99772fd8322afacfe40147cbffd8fbd542bb24022716d47d8652e4459` | `00731D7E` |
| `00731DB0` | 250 | `00331DB0` | `003311B0` | `52abe0bd6bed3e14cd96dc5725e256fed39ebe349017f64fd71659fd50059385` | `a1c5a1133e574d270e4ee5e14f0d4f90f0b26e67f7cd1623f3ea660777f3157c` | `00731DEE` |
| `00731F30` | 188 | `00331F30` | `00331330` | `f909998b57244c02df2b749e4f58687158f90312355e42320f15687e1bd24fd0` | `e876b61ea198e582e70483686d972eebbc062f7c9d73b3646795f5f71f10dbd0` | `00731FB5`, `00731FCB` |
| `007344A0` | 538 | `003344A0` | `003338A0` | `4759894f83e1ed4aa3d9ec636ecfbb74ba15b991393ec891ae718e326bf4d711` | `312bf3aaa07211ee7d4ddd5c66aa322a606027c9341aa011c213d61744e7a27c` | `00734608`, `00734632` |

- At all seven call sites, raw x86 sets up a two-DWORD stack argument pair and a nonzero receiver in `ECX`. In several decompiler outputs the apparent call prototype lists only the stack pair, omitting the `__thiscall` receiver. The raw callsite windows are the evidence for the receiver.
- `00731CE0` checks that the two input DWORDs are not both zero and that `[this+0x1D4]` is nonzero. It loads `[this+0x1D4]` into `ECX`, pushes both inputs, calls the anchor, and returns its result. The field's type and purpose are unknown.
- `00731D10` reads a byte through a cursor at `param_2+0x18`, uses that byte to index a function-pointer table at absolute address `0x014068F0`, advances the cursor, and has a conditional `'A'` path that calls through the pointer cell `0x014069F4`. It forms two output DWORDs; if they are not both zero and `[owner+0x1D4]` is nonzero, it calls the anchor with that owner field in `ECX` and stores the returned DWORD. Encoding/bytecode meanings remain unknown.
- `00731DB0` initializes its output pair to zero, guards a zero/zero input and a nonzero `[this+0x1D4]`, then calls the anchor. On the non-`-1`, positive-result path, it uses the returned value with a `0x50`-byte stride to read another index from row offset `+0x40`; it then uses that index with the same stride and copies two DWORDs from the selected row's start. Array bounds assertions are present in the decompiler output; row/array types and the returned index meaning remain unknown.
- `00731F30` decodes two pairs of DWORDs from its cursor path, assigns `[owner+0x1D4]` to `ECX`, and calls the anchor twice. It checks both returned values against `-1`; when both pass, it calls `FUN_0075DDA0` with the two results and stores that return. The downstream function's role is unknown.
- `007344A0` loops over records with a `0x10`-byte stride. Each record supplies two consecutive DWORD pairs; each pair is conditionally looked up through the anchor using `[owner+0x1D4]` as receiver. The two results (or `-1` sentinels) are written to an output array at an 8-byte stride before later virtual callbacks consume it. This establishes a repeated static dataflow shape, not the input records' semantic identity.
- Context-only caller `00730BD0` contains calls at `00730D03` and `00730EC2`. Raw setup at both sites loads key DWORD pairs from separate indexed regions at owner offsets `+0xF8` and `+0x104`, and loads `ECX` from a pointer field at `+0x1D4` of a local object. Its indexed body is 1,693 bytes but the last byte does not complete an instruction; its dossier remains L0 and it is excluded from this EXP's full-body overlay.
- EXP-0206 records 37 direct-call sites to `0072E230` from 32 distinct functions. The five reviewed bodies contribute seven of those sites. The shared receiver/key setup supports a bounded relationship between callers and the indexed lookup helper, while caller identities and owner fields remain unnamed.
- The cumulative manual overlay rises from 248 to 253 unique bodies, or 0.349269% of 72,437 indexed functions. The five additions are outside the EXP-0139 target subset. No L2–L4 evidence is added.

## Interpretation and claim limits

- **Observed:** each of the five selected bodies fully decodes; their raw callsites pass two stack DWORDs and a receiver in `ECX` to `0072E230`.
- **Observed:** selected callers consume the returned DWORD as a guarded index/result, including a path that uses it to select `0x50`-stride rows and a path that performs two lookups before a downstream call.
- **Inferred, limited:** the shared helper is used as a pair-key lookup/index accessor across multiple call contexts. EXP-0206's raw body and EXP-0158/0205's callee review support this shape. Key meanings, table ownership, record types, and subsystem remain unknown.
- **Observed, bounded context only:** `00730BD0` also calls the helper twice, but one indexed tail byte did not decode; this EXP records only the two callsite windows and does not count it as a fully reviewed body.
- **Unknown:** runtime execution, owning class, serialization/bytecode meaning, caller roles, and whether the five functions belong to one subsystem.
- **Not established:** names guessed from code shape, gameplay behavior, or execution in the registered build.

## Reproduction and limitations

1. Verify the EXE SHA-256 and resolve all selected VA/size rows in the exact-build index.
2. Map each RVA to its file offset and recompute raw and normalized hashes.
3. Decode the five selected bodies and verify exact instruction coverage equals the indexed body size.
4. Inspect raw bytes around the seven call sites to verify pushes, ECX receiver assignment, and direct-call destinations.
5. For `00730BD0`, preserve its incomplete final byte as a limitation; do not claim a whole-body decode.
6. Query the dedicated callgraph endpoints for complete call-site counts; dossier edge excerpts may be capped.

This was read-only static analysis. No game process was used.

## Links

- Lookup helper raw-body review: [EXP-0206](EXP-0206-review-0072e230-bounded-lookup-accessor.md)
- Earlier exact-build key-table observations: [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md)
- Evidence: [five-body overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0207.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0207.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0207.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
