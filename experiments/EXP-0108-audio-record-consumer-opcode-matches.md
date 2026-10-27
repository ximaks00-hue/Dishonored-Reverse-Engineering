---
id: EXP-0108
title: Audio record reader and selected wrapper opcode matches
experiment_status: done
claim_status: observed
build: "10256413"
question: Does a static audio processing path read the same size/discriminator fields written by selected SoundEngine wrappers and dispatch matching record codes?
---

# EXP-0108 — Audio record reader and selected wrapper opcode matches

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the buffer reader `FUN_00D18530`, record dispatcher `FUN_00D20940`, its caller `FUN_00D21830`, and thread start path `FUN_00D46410`; correlate selected dispatch cases with literal fields written by wrappers already recorded in EXP-0106/0107.
- Exclusions: no runtime execution, frequency, actual sound output, complete dispatch-table inventory, or semantic assignment to uncorrelated case values. The `FUN_00D20940` decompile contains a Ghidra jumptable/spacebase warning, so only explicitly visible cases and data accesses are used. No game launch or binary modification.
- Tools: read-only `dishonored_static` decompiler, `dishonored_knowledge.function_dossier`, exact-build callgraph SQLite, and Ghidra headless `DumpXrefsAndDisasm.java` run with `-noanalysis -readOnly` for `00D46410` and `013A9CF0`; Python `pefile` to resolve IAT slots used in the worker disassembly.
- Durable output: [selected producer-to-consumer case map](../research/executable/evidence/EXP-0108-audio-record-consumer-opcode-map.csv).

## Procedure

1. Re-read repository instructions, status, Blink graph, and build record; verify the current executable SHA-256.
2. Decompile `00D18530`, `00D184D0`, `00D20940`, `00D21830`, `00D46480`, and `00D25EF0`.
3. Compare callgraph callers/callees for `00D18530`, `00D20940`, `00D21830`, and `00D25EF0`; use `DumpXrefsAndDisasm.java` at `00D46410` to inspect its code reference and instruction stream.
4. Resolve the worker instruction's indirect-call IAT slots against the exact executable import table.
5. Compare each selected wrapper's literal 16-bit `+2` field from EXP-0106/0107 against the corresponding `switch(puVar6[1])` case in `00D20940`. Record only matching values and visible callees/actions.

## Observations

- `FUN_00D18530` returns a pointer into a chunk selected by queue state and an available-byte count through its output parameter. When the current chunk is exhausted, it resets the per-chunk offset, advances/wraps the chunk index, and returns the next chunk's base pointer.
- `FUN_00D20940` has one indexed direct caller, `FUN_00D21830`; it calls `FUN_00D18530` at `00D209AA`. Its visible loop dispatches on `puVar6[1]`, advances the record pointer by the 16-bit length `*puVar6`, accumulates consumed bytes, and calls `FUN_00D184D0` to commit the consumed byte count. `FUN_00D184D0` adds that count to queue state and clears a one-byte state flag. The knowledge `function_dossier` view reports at most 30 caller items; the exact-build SQLite edge table contains 50 callsite edges / 48 unique callers to `FUN_00D21A00`, so the dossier list is not a complete cohort (EXP-0109).
- `FUN_00D21830` directly calls `FUN_00D20940` at `00D21849` while holding a critical section, among other processing calls.
- `FUN_00D46480` passes `&LAB_00D46410` as the first argument to `FUN_00D25EF0`. `FUN_00D25EF0` calls the imported `CreateThread` with that argument as the thread start routine and the supplied context pointer as its parameter. The label `"AK::EventManager"` is also passed by the caller into the thread helper. The thread-start address is not a separate indexed Ghidra function in this build.
- Read-only disassembly at `00D46410` shows a loop that calls `FUN_00D21830`, then indirect-calls the IAT slot at `00F941D0` with the context's event handle and timeout `0x102`, and repeats while the byte at context offset `+4` is zero. PE import parsing identifies `00F941D0` as `KERNEL32!WaitForSingleObject`. The `CreateThread` entry/context relationship is static evidence; it does not establish thread scheduling or runtime execution.
- The worker/dispatcher path reads the same 16-bit length/discriminator layout established by EXP-0106/0107: wrappers pass a record size to `FUN_00D218F0`, which writes that size into the first word before `FUN_00D18670` copies the bytes; the consumer advances by the first word and switches on the next word.
- Selected exact matches and observed cases:

| Producer field | Consumer case | Visible case body |
|---|---:|---|
| `SetRTPCValue` `0x02` / `0x03` | 2 / 3 | Both paths call `CAkRTPCMgr::SetRTPCInternal`; case 3 passes a record-relative `TransParams` pointer. |
| `ResetRTPCValue` `0x05` / `0x06` | 5 / 6 | Both call `FUN_00D2FD30` with fields from the record. |
| `SetSwitch` `0x08` | 8 | Calls `FUN_00D2E180` with record values. |
| `PostTrigger` `0x0A` | 10 | Calls `FUN_00D2B030`, whose shown body iterates callback-like nodes and invokes an indirect method. |
| `RegisterGameObj` `0x0B` | 11 | Calls `FUN_00D2CB90`, whose shown body looks up or allocates a `CAkRegisteredObj`. |
| `UnregisterGameObj` / `UnregisterAllGameObj` `0x0C` | 12 | Branches between `FUN_00D2CC40` and `FUN_00D2CEE0`; the wrapper's `0xFFFFFFFF` field takes the all-object branch. |
| `SetObjectObstructionAndOcclusion` `0x16` | 0x16 | Calls `FUN_00D2CE70` with record fields. |
| `RenderAudio` helper marker `0x00` | 0 | Increments a state counter and checks a drain condition; after processing, the dispatcher clears a flag and calls `SetEvent`. |

- The per-case address and caution catalog is [EXP-0108-audio-record-consumer-opcode-map.csv](../research/executable/evidence/EXP-0108-audio-record-consumer-opcode-map.csv). The set above is intentionally limited to producer cases directly examined in EXP-0106/0107.

## Interpretation and claim limits

- **Observed:** the static dispatcher consumes size-prefixed, 16-bit-discriminator records from the chunked buffer and contains cases matching eight selected producer wrapper forms. For these addresses, producer discriminator values match consumer switch labels, and visible handler call shapes are consistent with their wrappers' indexed API names.
- **Inferred, limited:** the thread routine passed to `CreateThread` is the static processing path that calls the dispatcher, because the disassembly at the supplied entry address calls `FUN_00D21830`, which calls `FUN_00D20940`. This establishes a static thread-start/call-chain relation, not runtime scheduling or proof that all queued records reach the handler.
- **Unknown:** meanings and producer ownership for uncorrelated cases, the complete record schema and field types, conditions that enqueue each operation in real sessions, return/result propagation, event synchronization semantics, and runtime audio output.
- **Limit:** namespace labels and Ghidra pseudocode are analysis metadata, not original source. The dispatcher decompilation reports a jumptable/spacebase warning; conclusions are restricted to visible literal cases and the explicit pointer/length accesses. No game runtime was launched.

## Reproduction

Use read-only `dishonored_static.decompile_function` for the listed indexed addresses and `dishonored_knowledge.function_dossier` for their edges. For the non-indexed thread entry, run from the repository root:

```powershell
& "E:\Dev\Tools\ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat" `
  "E:\Dishonored Reverse Engineering\research\executable\ghidra-project" `
  "Dishonored-RHCP-10256413" -process "Dishonored.exe" -noanalysis -readOnly `
  -scriptPath "E:\Dishonored Reverse Engineering\research\executable\scripts" `
  -postScript DumpXrefsAndDisasm.java 00D46410 50
```

The executed read-only Ghidra script also queried `013A9CF0`; observed incoming references were from `00D184E0`, `00D18580`, and `00D18670`, consistent with the recorded capacity/chunk-buffer helper path. This does not identify a runtime reader by itself.

## Links

- [EXP-0106 wrapper record fields and buffer writer](EXP-0106-audio-api-command-record-queue.md)
- [EXP-0107 RenderAudio conditional write](EXP-0107-renderaudio-shared-buffer-link.md)
- [EXP-0072 exact-build function triage](EXP-0072-exact-build-internal-function-subsystem-triage.md)
- [EXP-0108 consumer case catalog](../research/executable/evidence/EXP-0108-audio-record-consumer-opcode-map.csv)
