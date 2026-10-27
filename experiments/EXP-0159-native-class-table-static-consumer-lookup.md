---
id: EXP-0159
title: Static handler resolution paths through the global selector table and class-table registry
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What handler-selection paths and output writes can be established in FUN_0046E5C0 from exact-build raw x86?"
---

# EXP-0159 — Static handler resolution paths through selector table and class-table registry

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, verified against [the build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: full raw-x86 control flow of `FUN_0046E5C0`, including its guarded nonzero-selector path, the zero-selector registry lookup at `0x01435408`, and the output field writes.
- Exclusions: caller/entry reachability, registry initialization order, actual runtime keys and values, concrete class/function ownership, and indirect invocation of a selected target.
- Tools: Python 3 with `pefile` and `capstone`; `tools/disassemble_va.py`; `tools/scan_pointer_refs.py`; exact-build function index. No process attach, game launch, or binary modification.

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build ID and EXE hash.
2. Resolve the exact function range for `FUN_0046E5C0` from `research/executable/functions.csv`.
3. Disassemble its complete raw x86 range; inspect both the selector-table path and references to `0x01435408`.
4. Scan exact immediate references to `0x01435408` and raw pointer references to `FUN_0046E5C0`; use these scans to bound, not infer, caller coverage. Inspect PE section headers to determine whether selector-table values are present in file-backed bytes.
5. Hash the indexed function bytes after mapping VA through the PE image base and section table.

## Observations

- The exact-build index records `FUN_0046E5C0` at `0x0046E5C0–0x0046E83D`, size 638 bytes. SHA-256 of that exact function range is `3188F8F58F2E19A5E47C5FD35E2D9698386EDFF3E21227DF9A3C24DDD5550BE0`.
- The function passes its incoming `this` (`EBX`) to `FUN_00425D90` and saves the return in `ESI`. Raw x86 for that helper walks from the supplied object through pointer `[node+0x24]` until `[node+0x30]` equals global `0x0141B314`, then returns that node. The named indexed function `GetStackOwnerClass` at `0x00926480` loads `[arg+0x10]`, passes it to the same helper, and returns the result. This is a static symbol/usage association; it suggests a stack-owner-class lookup but does not by itself establish the node's type or the global sentinel's meaning.
- Using the returned `ESI`, `FUN_0046E5C0` checks bit `0x400` at `[EBX+0x80]` and bit `0x4000` at `[ESI+0xC8]`. If the first bit is clear or the second is set, it writes pointer `0x0045FF10` to `[EBX+0x9C]` and returns.
- Otherwise it reads a 16-bit value from `[EBX+0x84]`. If nonzero, the raw instruction at `0x0046E626` loads the DWORD at `0x014068F0 + selector*4` and stores that value at `[EBX+0x9C]`; this function contains no explicit bounds check on the selector. It does not call the loaded pointer in this path.
- PE section metadata places `0x014068F0` inside the virtual `.data` section but beyond its file-backed `SizeOfRawData` (section-relative offset `0x19D8F0`; raw size `0x14D000`; virtual size `0x21B3BC`). The table entries therefore have no corresponding bytes in this executable file. This static examination cannot establish their runtime values or how they are populated. The same global is referenced by other static decoder paths (for example, `FUN_004052F0` in EXP-0046 and reviewed native-exec adapters); shared address use does not establish that all sites use the entries with the same meaning.
- At `0x0046E783–0x0046E796`, the function passes a pointer to a two-dword local key and an output-index pointer to `FUN_00938290`, with `ECX = 0x01435408`. At `0x0046E7A8`, it reads the record-array base from `[0x01435408]`. These are the two code references to the registry address found by `tools/scan_pointer_refs.py --va 0x01435408 --code-only` within this function.
- A zero selector enters the registry fallback. The function builds a bounded 1024-byte string by copying/appending runtime-derived string fragments and the exact PE literal `exec` (VA `0x00FA8000`), then uses that string in a two-dword-key lookup. If `[ESI+4] == 0xFFFFFFFF`, the function instead calls `FUN_00449730` with pointer `0x00FBBA28` and integer arguments `0, 1, 1`; the raw DWORD at `0x00FBBA28` is `0x005CB0C0`, not a verified string. Otherwise, the key source is `[ESI+0x28]`. The special pointer and key semantics are unresolved. A cached decompilation renders the pointer as a string, but that interpretation is not supported by the current raw-byte inspection.
- The lookup result is compared with the local `0xFFFFFFFF` sentinel. On a hit, raw instructions compute `record_base + index * 0x14`, then load the pointer at record offset `+8`. This matches the slot layout independently described in [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md).
- The value pointer is treated as a sequence of 8-byte entries: a name pointer at entry offset `+0`, then a target pointer at `+4`. The code compares each pointed-to name byte-by-byte against a local, null-terminated string. It advances to the next name at `+8` until it encounters a null name pointer or a matching string.
- On a string match, the code stores the entry's target pointer to `[EBX+0x9C]`. If the registry lookup misses, the value pointer is null, the first name is null, or the sequence ends without a match, it stores zero to `[EBX+0x9C]`. A separate exception/error path writes `0x0045FF10` to the same field.
- `tools/scan_pointer_refs.py --va 0x0046E5C0` finds one raw pointer occurrence, at `0x00FBBA6C` in `.rdata`. It lies within a local 26-DWORD run from `0x00FBBA1C` through `0x00FBBA80`; every DWORD in that run equals an entry address in the exact-build function index. The run's neighboring DWORDs are not in that index. This strengthens the observation that the occurrence belongs to a function-address sequence, but does not establish its table bounds, owner, type, or use. Scanning code for the run start and the target slot address found no exact immediate references; that does not exclude references through another base or computed offset. No direct call to `FUN_0046E5C0` was established by this experiment.
- EXP-0138 records an example registration table at `0x012E54B0` containing a name pointer and target `0x009F5540`; EXP-0158 records the `DisBehaviorNotice` registration handoff. This experiment does not prove that the runtime key/string used here selects that example table or target.

## Interpretation and claim limits

- **Confirmed static control flow:** after the two flag guards, a nonzero 16-bit selector loads one DWORD from `0x014068F0 + selector*4` into `[EBX+0x9C]`; a zero selector enters the name-based registry fallback. Guard failure writes the fixed pointer `0x0045FF10`.
- **Observed symbol association:** the context node returned by `FUN_00425D90` is read by `FUN_0046E5C0` and by the indexed function named `GetStackOwnerClass`. The helper's exact pointer walk is confirmed statically; interpreting the returned node as a stack owner class follows the symbol name and remains unverified against class metadata or runtime state.
- **Confirmed static dataflow:** `FUN_0046E5C0` queries the registry at `0x01435408` with a two-dword key, reads the associated value from the matching 0x14-byte record, scans 8-byte name/target entries, and conditionally writes a selected pointer or zero to `[EBX+0x9C]`.
- **Observed static role:** this function is a consumer of the same registry structure whose helper layout is traced in EXP-0158. The table entries are used here as name-to-pointer records.
- **Inferred, cross-layer candidate only:** the 16-bit selector at `[EBX+0x84]` may correspond to a native-function token, and the zero-selector fallback may resolve token-zero class-table entries. This fits the separate UELib `NativeToken` observations (EXP-0066) and the class/table name-target joins (EXP-0137–0139), but no object-layout proof or selector-to-table-entry mapping has been established. The global selector table is not file-backed, so this experiment cannot confirm its values.
- **Unknown:** the helper result's exact node type and the meaning of global `0x0141B314`; the 16-bit selector's exact field identity; runtime contents/population of `0x014068F0`; key semantics; source/meaning of the composed name; concrete owner of the registry and entry list; caller/invocation condition; whether the selected pointer is later called; and any runtime reachability or behavior.
- **Limit:** disassembly establishes local static operations only. The single `.rdata` pointer occurrence is a candidate reference, not proof of a vtable or caller. The function stores a selected pointer but no call through `[EBX+0x9C]` is established here.

## Reproduction

From repository root, verify the executable SHA-256 from the build record, then run:

```powershell
python tools\disassemble_va.py --start 0x0046E5C0 --end 0x0046E83D
python tools\disassemble_va.py --start 0x00425D90 --end 0x00425DBE
python tools\disassemble_va.py --start 0x00926480 --end 0x0092648F
python tools\scan_pointer_refs.py --va 0x01435408 --code-only
python tools\scan_pointer_refs.py --va 0x0046E5C0
```

The function size and range are recorded in `research/executable/functions.csv`. Hash the 638 raw bytes beginning at VA `0x0046E5C0` after RVA-to-file-offset mapping to reproduce the digest above.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Registry helper layout: [EXP-0158](EXP-0158-native-class-table-key-value-store-layout.md)
- Selected registration and raw table evidence: [EXP-0137](EXP-0137-native-class-registration-group-uelib-join.md), [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- Nonzero `NativeToken` name/target candidates: [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md)
- Prior catalog join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
