---
id: EXP-0159
title: Static consumer lookup and name-target traversal for the shared class-table registry
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What does FUN_0046E5C0 read from the registry at 0x01435408, and what does its static dataflow establish?"
---

# EXP-0159 — Static consumer lookup and name-target traversal for the shared class-table registry

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, verified against [the build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: raw-x86 review of `FUN_0046E5C0`, exact-build references to the global registry address `0x01435408`, and the lookup result's dataflow through a table-like sequence.
- Exclusions: caller/entry reachability, registry initialization order, actual runtime keys and values, concrete class/function ownership, and indirect invocation of a selected target.
- Tools: Python 3 with `pefile` and `capstone`; `tools/disassemble_va.py`; `tools/scan_pointer_refs.py`; exact-build function index. No process attach, game launch, or binary modification.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build ID and EXE hash.
2. Resolve the exact function range for `FUN_0046E5C0` from `research/executable/functions.csv`.
3. Disassemble its raw x86 range and inspect the region around both references to `0x01435408`.
4. Scan exact immediate references to `0x01435408` and raw pointer references to `FUN_0046E5C0`; use these scans to bound, not infer, caller coverage.
5. Hash the indexed function bytes after mapping VA through the PE image base and section table.

## Observations

- The exact-build index records `FUN_0046E5C0` at `0x0046E5C0–0x0046E83D`, size 638 bytes. SHA-256 of that exact function range is `3188F8F58F2E19A5E47C5FD35E2D9698386EDFF3E21227DF9A3C24DDD5550BE0`.
- At `0x0046E783–0x0046E796`, the function passes a pointer to a two-dword local key and an output-index pointer to `FUN_00938290`, with `ECX = 0x01435408`. At `0x0046E7A8`, it reads the record-array base from `[0x01435408]`. These are the two code references to the registry address found by `tools/scan_pointer_refs.py --va 0x01435408 --code-only` within this function.
- The lookup result is compared with the local `0xFFFFFFFF` sentinel. On a hit, raw instructions compute `record_base + index * 0x14`, then load the pointer at record offset `+8`. This matches the slot layout independently described in [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md).
- The value pointer is treated as a sequence of 8-byte entries: a name pointer at entry offset `+0`, then a target pointer at `+4`. The code compares each pointed-to name byte-by-byte against a local, null-terminated string. It advances to the next name at `+8` until it encounters a null name pointer or a matching string.
- On a string match, the code stores the entry's target pointer to `[EBX+0x9C]`. If the registry lookup misses, the value pointer is null, the first name is null, or the sequence ends without a match, it stores zero to `[EBX+0x9C]`. A separate exception/error path writes `0x0045FF10` to the same field.
- `tools/scan_pointer_refs.py --va 0x0046E5C0` finds one raw pointer occurrence, at `0x00FBBA6C` in `.rdata`. The pointer scan does not identify the data's owner or prove an indirect caller. No direct call to `FUN_0046E5C0` was established by this experiment.
- EXP-0138 records an example registration table at `0x012E54B0` containing a name pointer and target `0x009F5540`; EXP-0158 records the `DisBehaviorNotice` registration handoff. This experiment does not prove that the runtime key/string used here selects that example table or target.

## Interpretation and claim limits

- **Confirmed static dataflow:** `FUN_0046E5C0` queries the registry at `0x01435408` with a two-dword key, reads the associated value from the matching 0x14-byte record, scans 8-byte name/target entries, and conditionally writes a selected pointer or zero to `[EBX+0x9C]`.
- **Observed static role:** this function is a consumer of the same registry structure whose helper layout is traced in EXP-0158. The table entries are used here as name-to-pointer records.
- **Unknown:** the key's semantic meaning, the source/meaning of the comparison string, concrete owner of the registry and entry list, caller and invocation condition, whether the selected pointer is later called, and any runtime reachability or behavior.
- **Limit:** disassembly establishes local static operations only. The single `.rdata` pointer occurrence is a candidate reference, not proof of a vtable, caller, or dispatch route.

## Reproduction

From repository root, verify the executable SHA-256 from the build record, then run:

```powershell
python tools\disassemble_va.py --start 0x0046E5C0 --end 0x0046E83D --print-from 0x0046E780
python tools\scan_pointer_refs.py --va 0x01435408 --code-only
python tools\scan_pointer_refs.py --va 0x0046E5C0
```

The function size and range are recorded in `research/executable/functions.csv`. Hash the 638 raw bytes beginning at VA `0x0046E5C0` after RVA-to-file-offset mapping to reproduce the digest above.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Registry helper layout: [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md)
- Selected registration and raw table evidence: [EXP-0137](EXP-0137-native-class-registration-group-uelib-join.md), [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- Prior catalog join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
