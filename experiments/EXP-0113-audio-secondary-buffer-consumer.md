---
id: EXP-0113
title: Audio subsystem secondary chunk-buffer consumer and termination path
experiment_status: done
claim_status: observed
build: "10256413"
question: Does the exact-build static function graph expose a second consumer of the chunk-buffer helper family, and what record cases and termination-side operations are visible?
---

# EXP-0113 — Audio subsystem secondary chunk-buffer consumer and termination path

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: read-only exact-build decompilation and indexed callgraph review of `FUN_00D1E4A0`, `FUN_00D184F0`, `FUN_00D184D0`, `FUN_00D1F770`, `FUN_00D16870` (`Term`), and `FUN_00D18620`; compare their helper and state-access shapes with the primary record consumer in EXP-0108.
- Exclusions: no claim that the primary and secondary paths use the same buffer instance, no complete record schemas or virtual-call target semantics, no runtime execution/thread identity, and no observed audio output.
- Tools: read-only exact-build `dishonored_static.decompile_function`, `dishonored_knowledge.function_dossier`, and the indexed exact-build callgraph.

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, EXP-0108, and build record; verify the selected build identity.
2. Retrieve dossiers for `00D1E4A0`, `00D1F770`, `00D16870`, `00D184F0`, `00D184D0`, `00D18620`, and `00D20940`.
3. Read-only decompile `00D1E4A0`, `00D184F0`, `00D18620`, and `00D1EDE0`/`00D1EEC0`; record literal switch values, helper calls, and visible state updates only.
4. Compare the buffer helper call edges and pointer/index arithmetic against the EXP-0108 primary consumer. Keep common helper shape separate from proof of common queue instance or runtime use.

## Observations

- The indexed callgraph lists `FUN_00D1F770` as a direct callee of `Term` (`00D16870`), and `FUN_00D1F770` directly calls `FUN_00D1E4A0`, `FUN_00D18620`, `FUN_00D1EDE0`, and `FUN_00D1EEC0`.
- `FUN_00D1E4A0` enters a critical section and loops until three compared state fields are equal and a byte condition is zero. Otherwise it obtains a record pointer from `FUN_00D184F0` and dispatches on the 16-bit value at record offset `+2`. Visible cases are `1`, `0x19`, `0x21`, and `0x25`.
- The visible case bodies include calls through record-derived object/vtable pointers, `FUN_00D24D90`, and, in one branch of case `1`, `FUN_00D14D10`. The function calls `FUN_00D184D0` with the record's 16-bit first field on the visible consumption paths and loops back; interpretation of the indirect targets and all record fields remains open.
- `FUN_00D184F0` returns a pointer into a chunk selected by index/offset fields; when its current offset reaches the stored chunk length, it resets the offset, advances/wraps the chunk index, and returns the next chunk base. `FUN_00D184D0` adds its argument to a state field at `+0x14` and clears a byte at `+0x20`.
- In EXP-0108, `FUN_00D20940` obtains data via `FUN_00D18530`, which uses the same indexed chunk-descriptor shape as `FUN_00D184F0` and additionally reports available bytes. It also calls `FUN_00D184D0` to commit consumed length. The exact-build graph lists `00D1E4A0` as the only indexed direct caller of `00D184F0`; `00D184D0` has direct callsites from both `00D1E4A0` and `00D20940`.
- All four visible secondary discriminator values (`1`, `0x19`, `0x21`, `0x25`) also appear as explicit top-level case values in the primary `FUN_00D20940` dispatcher (EXP-0108/0109). EXP-0109 lists direct writer-cohort producers for those primary cases: `FUN_00D16BE0` for `1`; `Break`, `Close`, `FUN_00D252F0`, `Pause`, `Play`, `Resume`, and `Stop` for `0x19`; `ExecuteActionOnEvent` for `0x21`; and `SeekOnEvent` for `0x25`.
- `FUN_00D18620`, called by `FUN_00D1F770`, iterates chunk entries, calls `AK::MemoryMgr::Falign` on each stored chunk pointer, then aligns and clears the descriptor allocation fields shown in its decompile.
- `FUN_00D1EDE0` and `FUN_00D1EEC0`, also directly called by `FUN_00D1F770`, walk separate linked-list fields, perform visible object/vtable and free-list operations, decrement count fields, and align freed record allocations. Their data structures and callback meanings are not resolved here.

## Interpretation and claim limits

- **Observed:** the exact-build static graph contains a second path through chunk-descriptor read/consume helpers: `Term` → `FUN_00D1F770` → `FUN_00D1E4A0` → `FUN_00D184F0` / `FUN_00D184D0`. Its visible record cases are `1`, `0x19`, `0x21`, and `0x25`. This differs from the primary EXP-0108 dispatcher path, which uses `FUN_00D18530` and a visible switch over its records.
- **Observed:** those four numeric case values are reused in both consumer functions' visible switches. The primary writer-to-case associations in EXP-0109 establish those values on the `FUN_00D21A00` route; they do not establish that these producers feed `FUN_00D1E4A0` or that the two consumers share record layouts.
- **Observed:** the `Term`-reachable helper `FUN_00D18620` visibly aligns stored chunk pointers and clears fields in a descriptor-like structure.
- **Unknown:** whether the two consumers operate on the same descriptor or separate instances, how either consumer is scheduled at runtime, what the indirect record callbacks mean, and how the secondary cases relate to public audio API calls.
- **Limit:** shared helper names, similar pointer/index arithmetic, and common byte-commit helper establish a static helper-family relationship only. Decompiler pseudocode is not original source; no runtime was launched.

## Reproduction

Use the read-only static dossier/decompile tools for the listed addresses. The selected decompiles are cached under `knowledge/cache/decompiles/`; the exact-build callgraph is the source for the stated direct-call relations. Compare with [EXP-0108](EXP-0108-audio-record-consumer-opcode-matches.md).

## Links

- [EXP-0108 primary audio record consumer](EXP-0108-audio-record-consumer-opcode-matches.md)
- [EXP-0106 shared record writer path](EXP-0106-audio-api-command-record-queue.md)
- [EXP-0111 audio API direct-callee cohort](EXP-0111-audio-api-direct-callee-cohort.md)
- [Build record](../research/builds/BUILD-STEAM-10256413/build.md)
