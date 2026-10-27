---
id: EXP-0128
title: SoundEngine bank and preparation request submission path
experiment_status: done
claim_status: mixed
build: "10256413"
question: What exact static path connects selected LoadBank and PrepareEvent wrappers to request storage and their completion-event handling?
---

# EXP-0128 — SoundEngine bank and preparation request submission path

- Experiment status: done
- Claim status: mixed
- Build ID: 10256413
- Question: What exact static path connects selected `LoadBank` and `PrepareEvent` wrappers to request storage and their completion-event handling?
- Scope and exclusions: Read-only decompiler and exact-build direct-call graph review of selected AK::SoundEngine wrappers and helpers. No runtime thread scheduling, request execution, bank contents, event semantics, or audio behavior is established.
- Prerequisites / starting state: Exact build 10256413 and executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` checked against the build record.
- Tools and versions: Read-only static MCP decompiler (`analyzeHeadless -noanalysis -readOnly`), persisted function index, and local `callgraph.sqlite`.

## Procedure

1. Start from address-derived unknown callees in the EXP-0111 audio API direct-callee cohort, focusing on the `FUN_00D27810` request path.
2. Decompile `FUN_00D27810`, its visible storage and keyed-reference helpers, and selected named API wrappers that call them.
3. Query exact direct callers for the examined addresses and separate AK::SoundEngine API callers from helpers with additional unclassified callers.
4. Record visible record construction, allocation, locking, event, and wait operations without assigning source-level type names to recovered stack/structure layouts.

## Observations

- `AK::SoundEngine::LoadBank` at `00D144E0` creates a Win32 event, constructs a local nine-dword request-like block containing `param_1`, `param_2`, callback/data fields, and the event storage, then calls `FUN_00D27810` and `FUN_00D13590`. `ClearPreparedEvents` at `00D148C0` follows the same visible pattern with a different leading operation value. These are decompiler-recovered AK API names and static calls; no request execution is observed.
- `AK::SoundEngine::PrepareEvent` at `00D14830` creates an event, calls `FUN_00D14310(param_1,param_2,param_3,1)`, then calls `FUN_00D13590` with the returned value. Other indexed `PrepareEvent` callers also reach `FUN_00D14310`.
- `FUN_00D142B0` copies nine dwords of locally assembled fields into a stack block and calls `FUN_00D27810`. Its indexed callers include two `LoadBank` overloads.
- `FUN_00D14310` rejects a zero item count with `0x1F`. For count one it dereferences the supplied array pointer; for a nonzero copy flag and count above one it allocates `count*4` bytes and copies the array. It builds a stack block and calls `FUN_00D27810`; on a non-`1` result it frees the temporary array when the count was not one.
- `FUN_00D143F0` similarly rejects a zero count or null pointer, selects/copies an array based on count and a flag, constructs a stack block, and calls `FUN_00D27810`; it frees its temporary copy on the shown non-`1` path. Indexed callers include `PrepareGameSyncs` wrappers.
- `FUN_00D27810` enters a critical section at `param_1+0x30`. If its third argument is nonzero, it calls `FUN_00D1B4C0` with the fourth argument and exits through a failure branch unless that helper returns `1`. It then calls `FUN_00D27670` with a pointer to the local request fields, maps null/non-null to return values `2`/`1`, conditionally calls `FUN_00D1B530` when a flagged enqueue failed, calls `SetEvent` on the handle stored at `param_1+0x28` when the result is `1`, leaves the critical section, and returns.
- `FUN_00D27670` selects a node from a linked free-node chain or allocates `0x28` bytes if its count is below a stored limit; it links the selected node into a queue, increments a counter, and copies nine dwords from the supplied request block. This is a queue-like storage operation by visible pointer updates; node type and consumer ownership remain unrecovered here.
- `FUN_00D13590` waits indefinitely on the handle at `param_1[1]` only when its second argument equals `1`; it then closes and clears that handle and returns `*param_1`. Otherwise it closes/clears the handle if present and returns the second argument. Its AK callers include `LoadBank`, `UnloadBank`, `PrepareEvent`, `ClearPreparedEvents`, and related APIs.
- `FUN_00D1B4C0` searches three-dword entries by key under a critical section, increments a matching entry's second dword, or calls `FUN_00D1B3D0` to find/create a keyed entry. It returns `0x34` when creation fails and `1` otherwise. `FUN_00D1B530` decrements a matching entry's count or calls `FUN_00D1B420` when the count is below two; after releasing the critical section it waits indefinitely on a stored handle when a global thread ID differs from `GetCurrentThreadId()`.
- The direct-call index shows `FUN_00D1B4C0` has two callers (`FUN_00D27810` and `FUN_00D27940`), while `FUN_00D1B420` has six callers including `FUN_00D27810`'s release path and several other address-derived functions. Their storage/refcount mechanics are observed, but subsystem ownership is not assigned.
- The indexed callgraph includes 20 direct callers to `FUN_00D27810`; the selected `LoadBank`, `PrepareEvent`, and `PrepareGameSyncs` wrappers are part of that set. Caller edges prove static references, not runtime reachability.

## Interpretation

- **Observed:** selected named AK::SoundEngine wrappers construct fixed or array-based request blocks and statically route them through `FUN_00D27810`; that helper serializes queue-node insertion under a critical section and signals a stored event on its success result.
- **Observed:** `FUN_00D13590` conditionally waits on and closes a handle based on a returned numeric status.
- **Inferred, limited:** the selected wrappers form a bank/preparation request-submission path. Queue insertion is visible; whether the caller's subsequent wait denotes completion of bank/preparation work, and whether the same event field participates in worker wakeup or completion, remains unknown.
- **Unknown:** exact request-block type/layout, meaning of operation values and callback fields, queue consumer identity, thread scheduling, relationship between the event passed by each wrapper and the event signaled at `param_1+0x28`, status-code semantics, and runtime execution.
- **Unassigned:** the keyed-entry/reference helpers `FUN_00D1B3D0`, `FUN_00D1B420`, `FUN_00D1B4C0`, and `FUN_00D1B530` remain subsystem-unassigned because their indexed caller set extends beyond the sampled AK::SoundEngine request path.
- Confidence: High for visible field copies, conditions, direct calls, Win32 API calls, and indexed caller addresses; medium for grouping selected wrappers into one submission path; no runtime claim.
- Alternative explanations: The queue and keyed-reference helpers may be shared by additional engine subsystems, and some decompiler argument recovery may omit implicit `this` or stack-passed blocks.
- Evidence that would falsify this interpretation: A corrected function-boundary/callgraph result that removes the listed direct edges, or a corrected decompile that changes the recorded branch/copy/lock behavior.

## Reproduction

- Reset/cleanup steps: None; read-only analysis.
- Repeat count and variation: One static decompile per selected address; exact direct-call edges checked from the local SQLite callgraph.
- Known sources of variance: Decompiled types and calling-convention recovery; no runtime comparison.

## Links

- Build: `research/builds/BUILD-STEAM-10256413/build.md`
- Files/functions/objects: `FUN_00D144E0`, `FUN_00D14830`, `FUN_00D142B0`, `FUN_00D14310`, `FUN_00D143F0`, `FUN_00D27810`, `FUN_00D27670`, `FUN_00D13590`, `FUN_00D1B3D0`, `FUN_00D1B420`, `FUN_00D1B4C0`, `FUN_00D1B530`
- Related experiments: EXP-0106, EXP-0107, EXP-0108, EXP-0109, EXP-0111
- Open questions: Request consumer path and event/status semantics; ownership of shared keyed-reference helpers.
