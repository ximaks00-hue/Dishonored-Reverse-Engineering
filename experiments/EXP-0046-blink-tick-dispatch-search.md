---
id: EXP-0046
title: "Search for the engine dispatcher of Blink update slot +0x13C"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the exact-build executable expose a direct or statically identifiable indirect engine callsite for Blink vtable slot +0x13C?"
---

# EXP-0046 — Search for the engine dispatcher of Blink update slot +0x13C

- Date: 2026-10-26.
- Build: Steam build `10256413`; static MCP reports executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, image base `0x00400000`, and a ready 72,437-function index. This matches [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: bounded static search for code that invokes the Blink update vtable slot at `+0x13C`; distinguish direct function references from generic same-offset calls.
- Method: read-only static MCP, the persisted exact-build callgraph SQLite index, and a reproducible Capstone 5.0.7 x86 scan of executable PE sections (`tools/exp0046_scan_slot13c.py`). No game/Ghidra program bytes were changed; no game process was launched; `_excluded_coop_project/` was not accessed.

## Procedure

1. Re-read the project status, Blink activation graph, build record, and session checklist before recording results.
2. Confirmed static MCP health: build ID and EXE SHA-256 match the build record; project/index readiness is true.
3. Queried incoming call/data edges to `FUN_00BFC5D0` and its Blink/Transversal vtable slots, and incoming call/data edges to the updater `FUN_00BFA270`.
4. Reproduced the full executable-section sweep with Capstone `skipdata=True` for (a) `call [reg+0x13C]` and (b) `mov reg,[base+0x13C]` followed within three decoded instructions by `call` through that same register. This later complete sweep supersedes the earlier one-hit scan result; it decodes 4,210,462 instructions and skips 134 data bytes.
5. Mapped all candidates through `functions.csv`; four candidates have no containing function entry in that index. Decompiled and inspected the raw candidate in `FUN_004052F0` read-only.

## Observations

- The callgraph has two data references to `FUN_00BFC5D0`: Blink vtable entry `0x011687D4` and Transversal vtable entry `0x011BD1E4`. It has no direct code-call edge to that function.
- `FUN_00BFA270` has one direct code caller in the index: `FUN_00CF3540` at `0x00CF3552`. It also has a data reference at Blink vtable slot `0x01168848` (`Blink vtable 0x01168698 + 0x1B0`). EXP-0045 establishes that `FUN_00BFC5D0` makes a same-receiver virtual `+0x1B0` call in mode 0; this is the base Blink route.
- The full sweep found no direct `call [reg+0x13C]` form and found 79 load-then-call patterns. Four did not map to a containing function in the available index. The previously reported one-hit count was incomplete and is superseded by this reproduction.
- One mapped sequence is `mov eax,[edx+0x13C]` at `0x004053FB`, followed by `call eax` at `0x00405404`, inside `FUN_004052F0` (`0x004052F0–0x00405466`).
- The sequence is inside `FUN_004052F0` (`0x004052F0–0x00405466`). Its decompilation advances an input cursor at `param_2+0x18`, dispatches byte-coded handlers through `DAT_014068F0`, obtains a record/class-like object through parser state, and loops over records. In that loop it calls a method from `piVar2`'s vtable slot `+0x13C` with `_Dst`, a record-derived address, and `0`; an optional method at `+0x168` is called afterward under a flag check. The available index does not identify this receiver as a Blink component or the target as `FUN_00BFC5D0`.
- The `FUN_004052F0` candidate demonstrates that this slot number is also used by an unrelated record-processing call path. It is not evidence of the engine's Blink tick dispatcher. The other 78 patterns are generic same-displacement candidates and require per-site receiver analysis before classification.
- Search limitation: this scan recognizes only an immediate displacement form and a short `mov`-then-`call same register` form. It does not prove absence of a dispatcher using computed offsets, other registers/instruction sequences, callbacks, or runtime-populated tables.

## Interpretation / claims

- **Confirmed:** the exact-build index records Blink and Transversal vtable data references to `FUN_00BFC5D0`, and no direct code-call edge to it.
- **Confirmed:** the reproducible full sweep found 79 generic `+0x13C` load-then-call patterns and zero direct memory-call forms; the earlier one-hit scan result was incomplete.
- **Observed, interpretation limited:** one mapped candidate is at `0x004053FB` / `0x00405404` inside `FUN_004052F0`, a record-processing path. The remaining candidates have not been attributed to receiver classes or Blink targets.
- **Observed, interpretation limited:** `FUN_004052F0` has parser/input-cursor and record-iteration behavior; its `+0x13C` virtual call receives a record-processing argument pattern. Its dynamic class and target are not established, so the call is classified as an unrelated generic-slot candidate, not Blink dispatch.
- **Unknown:** the engine-side callsite and runtime scheduler that invoke Blink `FUN_00BFC5D0` at vtable `+0x13C`.
- **Conclusion:** the scan does not identify the Blink tick dispatcher. The 79 matching instruction patterns are generic; no receiver among them has yet been proven to be a Blink/Transversal object whose target is `FUN_00BFC5D0`. Per-candidate receiver/vptr resolution remains necessary.

## Reproduction and limitations

- Check `dishonored_static.health` for build/hash/index identity.
- Query the callgraph SQLite `edges` table for incoming edges to `00BFC5D0` and `00BFA270`.
- Run `python tools/exp0046_scan_slot13c.py`; the checked-in candidate list is `research/executable/evidence/EXP-0046-slot13c-candidates.csv`. Inspect mapped candidates from function entry in read-only Ghidra.
- A direct-call index cannot enumerate virtual invocation sites. The bounded instruction-pattern scan is not a proof that no alternative dispatch sequence exists.
- Ghidra pseudocode is an analysis rendering, not original source.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Related: EXP-0043, EXP-0044, EXP-0045, EXP-0048, and EXP-0028.
- Graph: [Blink activation evidence graph](../docs/gameplay/blink/activation-graph.md)
