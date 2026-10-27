---
id: EXP-0206
title: Review 0072E230 and reconcile its indexed caller neighborhood
experiment_status: done
claim_status: mixed
build: "10256413"
question: What operations does the exact-build body at `0072E230` perform, and how complete is its indexed direct-call neighborhood?
---

# EXP-0206 — Review 0072E230 and reconcile its indexed caller neighborhood

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app 217980, build `10256413`, x86; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: raw-byte review of the 96-byte function at VA `0x0072E230`; comparison with its indexed direct callee and complete caller rows from the matching callgraph snapshot.
- Exclusions: no source-level name, field type, owner class, runtime reachability, or gameplay role is assigned. Callgraph proximity does not prove common subsystem ownership.
- Tools: Python 3.12, pefile 2024.8.26, Capstone 5.0.7; exact-build PE, function index, and offline callgraph snapshot exported 2026-10-26.

## Procedure

1. Re-read the current research status, Blink activation graph, build record, and session checklist; verify the executable SHA-256 against the registered build.
2. Resolve VA `0x0072E230` through the PE and exact-build function index, then hash and decode exactly the indexed 96-byte body as x86-32.
3. Normalize a same-length body copy by zeroing only Capstone-marked displacement and immediate spans; preserve instruction lengths and all other bytes.
4. Compare the raw instruction flow with the decompiler output and query the function dossier, dedicated `callers(limit=500)`, and `callees(limit=100)` endpoints.
5. Keep the result at L1 (body analyzed); record semantic, connectivity, and runtime axes separately.

## Observations

- The function index identifies `FUN_0072e230`, VA `0x0072E230`, RVA `0x0032E230`, size 96 bytes, inclusive body `0x0072E230–0x0072E28F`. PE mapping gives file offset `0x0032D630`.
- The executable hash matches the build record. Raw body SHA-256 is `6499be4cbac15390c1180d9dc26aa50843f48ebecdb3f7cd97a95767ed4d3b01`. All 96 bytes decode into 44 x86-32 instructions. Normalized same-length SHA-256 is `33c43857e8949fe41fd5050f393f5878aeafd2841db3d3f6dea7acd4619f8f4c`.
- The first two stack arguments are compared with zero; if both are zero, the body returns `0xFFFFFFFF` (`-1`). Otherwise, it forms `ECX+0xFC`, passes that receiver and stack-argument address to `FUN_00938290` at call site `0x0072E255`, and receives a slot index in a local variable.
- If the returned index is not `-1`, the body loads a base pointer through `[ECX+0xFC]`, adds `index * 0x14`, reads a DWORD at record offset `+8`, and returns it. The `-1` path returns `0xFFFFFFFF`. These are instruction-level effects; the record's type and the DWORD's meaning are unknown.
- The indexed direct-callee query returns exactly one edge: `0x0072E255 → 0x00938290`. EXP-0158 and EXP-0205 document that callee's bounded raw shape as a two-DWORD-key bucket/chain lookup; this does not establish the caller's key semantics or registry identity.
- The dedicated caller endpoint returns 37 direct-call-site rows from 32 distinct caller functions. Five callers have two sites each: `00730BD0` (`00730D03`, `00730EC2`), `00731F30` (`00731FB5`, `00731FCB`), `007344A0` (`00734608`, `00734632`), `007ACB00` (`007ACB18`, `007ACB76`), and `007B6DB0` (`007B6E3A`, `007B6E75`). The remaining 27 callers contribute one site apiece. The dossier embeds only 30 rows and is a bounded excerpt; the explicit query was requested with limit 500 and returned 37 rows.
- Eighteen of the 32 callers lie in the local address interval `0x00730BD0–0x00734C40`. Their names remain address-derived; the checked research corpus contains no prior semantic review for this group. Treat it as a prioritized comparison batch, not an established family.
- The portable cumulative manual-review overlay did not contain `0072E230` before this experiment. Adding this raw-body review changes the overlay count from 247 to 248 of 72,437 indexed functions (0.342366%). This is L1 body-review coverage; no L2–L4 evidence is added.

## Interpretation and claim limits

- **Observed:** the raw body rejects a zero/zero argument pair, calls `00938290`, uses the returned index with a `0x14` stride, and returns a DWORD at offset `+8` from the selected record address.
- **Inferred, limited:** in conjunction with the callee's independently reviewed lookup shape, `0072E230` is a bounded lookup/accessor candidate. The precise key, table type, owner class, and returned value semantics are unknown.
- **Observed:** the dedicated callgraph query contains 37 direct call sites from 32 distinct functions. The dossier's 30-row list is truncated context, not total fan-in.
- **Inferred, limited:** the 18 callers in the compact nearby address range are a useful next body-review batch because multiple callers share the helper. Address locality and call edges do not establish that they implement one subsystem.
- **Unknown:** indirect callers, caller argument values, object layout/type, runtime reachability, and gameplay connection.
- **Not established:** execution in game, named API behavior, or semantic understanding of the 32 callers.

## Reproduction and limitations

1. Verify the registered executable SHA-256 and exact function row for VA `0x0072E230`.
2. Map RVA `0x0032E230` to file offset `0x0032D630`; hash and fully decode the 96 bytes.
3. Recompute normalized hash by zeroing Capstone displacement/immediate spans in place without changing body length.
4. Query callers with a limit above 37 and callees for `0072E230`; count caller edge rows and unique source addresses separately.
5. Compare the dedicated caller list with the dossier excerpt; do not interpret the excerpt count as complete fan-in.

This was read-only static analysis. No game process was used.

## Links

- Prior lookup body and exact-build key-table observations: [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md)
- Independent callee hash and fan-in methodology: [EXP-0205](EXP-0205-reconcile-legacy-native-reviews-and-callgraph-fanin.md)
- Evidence: [body review overlay](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0206.csv), [cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0206.csv), [provenance summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0206.json)
- Evidence model: [L0–L4 methodology](../docs/methodology/function-evidence-model.md)
