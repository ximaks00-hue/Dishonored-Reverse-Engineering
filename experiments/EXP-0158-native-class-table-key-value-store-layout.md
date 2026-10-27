---
id: EXP-0158
title: Raw x86 structure of the shared native class-table handoff helper
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What lookup, record, and bucket operations can be established from raw x86 for the shared helper used by selected class/table handoffs?"
---

# EXP-0158 — Raw x86 structure of the shared native class-table handoff helper

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, verified locally against [the build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: raw-byte follow-up of `FUN_0044C310`, `FUN_00B699E0`, and its lookup, slot-allocation, bucket-resize, rehash, and insert callees. Trace one exact callsite from `FUN_00A0DBF0` to establish the values passed by a selected class/table handoff.
- Exclusions: no complete registry/table inventory, full consumer inventory, runtime execution, token dispatch proof, exact C++ type/name for the registry, or semantic interpretation of the table target. EXP-0159 subsequently establishes one static consumer path; it does not prove runtime use. The existing Ghidra cache is navigation evidence only; structural claims below are checked against raw PE bytes.
- Tools: Python 3 with `pefile` and `capstone`; `tools/disassemble_va.py`; read-only static index/decompiler access for address selection and comparison. No game launch, process attach, or binary modification.

## Procedure

1. Re-read `docs/research-status.md`, `docs/gameplay/blink/activation-graph.md`, and the build record; confirm build ID and SHA-256.
2. Resolve exact function start/end addresses and sizes from `research/executable/functions.csv` / the exact-build function index.
3. Disassemble complete indexed byte ranges from the local executable with `python tools/disassemble_va.py --start VA --end VA`; compare register and stack dataflow across each helper call.
4. Hash each raw byte slice by mapping `VA - ImageBase` through the PE section table. Verify all saved cache JSON files name build `10256413` and the matching executable SHA; do not use pseudocode as the primary evidence.
5. Follow the selected `FUN_00A0DBF0` callsite at `0x00A0F148–0x00A0F166`; decode its string input from the exact PE and join its table-pointer address to the existing EXP-0137/0138 raw catalogs.

## Observations

### Shared handoff wrapper and helper

- `FUN_00454FE0` (30 bytes, `0x00454FE0–0x00454FFD`) calls `FUN_00449A10` with the string argument, literal zero, and flag argument, using the caller-provided local pointer as `this`; it returns that same pointer and ends with `ret 8`. Raw SHA-256: `7F48270762FE7380B3DD7FABE9964F0D897F4AEF9F2A2E9670A692A6C6417EF8`.
- `FUN_0044C310` (57 bytes, `0x0044C310–0x0044C348`) receives two stack values, stores them as adjacent dwords in a local pair, passes a pointer to that pair and an output-index pointer to `FUN_00B699E0`, with a null optional flag. It then returns the address `record_base + index * 0x14 + 8`. Raw function SHA-256: `D673CDAECEAC1A87A259D918BF35775954D07FFD8CA96DC1636D6BBC8E99C127`.
- `FUN_00B699E0` (200 bytes, `0x00B699E0–0x00B69AA7`) passes the first dword in the input pair as a pointer to `FUN_00938290`. On a hit it copies the two dwords pointed to by that value into record offsets `+0` and `+4`, and copies the pair's second dword to record offset `+8`. Thus the wrapper/helper path reads the first argument as a pointer to a two-dword key object and treats the second argument as the associated value. Raw SHA-256: `BD2C81FA8EC5D93C741A0B6B0A13F644F4FD26BA840994272EBE30C030DAF772`.
- On a miss, `FUN_00B699E0` calls `FUN_009C6560` to obtain a slot index and slot pointer. If the slot pointer is non-null, it copies the same two key dwords to `+0/+4`, the associated value to `+8`, and initializes the link at `+0x0C` to `0xFFFFFFFF`. It requests a bucket-count update through `FUN_00C18870`; when that helper returns zero, it calls `FUN_00423970` to insert the new slot into a bucket chain.

### Lookup and five-dword slot layout

- `FUN_00938290` reads a bucket count at registry offset `+0x38`; when nonzero, it selects the bucket using the first key dword masked by `bucket_count - 1`. It follows slot indices stored at slot offset `+0x0C`, compares both key dwords at offsets `+0` and `+4`, and writes either the matching slot index or `0xFFFFFFFF` to the output. Raw function SHA-256: `36FE1AC62CAC3ADE657B2E90E61F1B10F6436E83922C236B2345B5081C4A4425`.
- The indexed slot stride used by lookup and helper address arithmetic is `0x14` bytes (five dwords). The raw code identifies these fields:

| Slot offset | Raw x86 use | Bounded interpretation |
| --- | --- | --- |
| `+0x00` | First key dword is compared and used in bucket selection | Key word 0 |
| `+0x04` | Second key dword is compared | Key word 1 |
| `+0x08` | Updated/copied from input-pair dword 1; wrapper returns its address | Associated value field |
| `+0x0C` | Read/followed as the next slot index; written during insert/rehash | Bucket-chain link index |
| `+0x10` | Written with the masked bucket index during insert/rehash | Stored bucket index |

- `FUN_00423970` computes `(key_word_0 & (bucket_count - 1))`, copies the current bucket head to slot `+0x0C`, stores that bucket index at `+0x10`, and replaces the bucket head with the new slot index. Raw SHA-256: `46B1B17964F1D1F21AD8E80F37BAC38790032A360719B310D48FACEC3E615357`.
- `FUN_009C6560` obtains a slot from a free-list when its count is nonzero. Otherwise it calls `FUN_004283F0(1)` and `FUN_00433010(1)`, then returns the index and `base + index * 0x14` pointer. It also sets a bit for that slot in the associated bit array. Raw SHA-256: `46ABFCF6CABE12AA202D36222D37ADC665B8AA3219E43CD86DF99E8DAB937B57`.
- `FUN_00C18870` grows the bucket-count field at `+0x38` when it is zero or the computed target is larger, then calls `FUN_00C177E0`; the latter clears bucket heads and walks indexed slots to rebuild bucket indices and chain links. This is a static resize/rehash path, not evidence for when or whether the registry is reached in a game session. Raw SHA-256 values: `FUN_00C18870` `09F0AFC2D2E7A66B881F60C6321B7BE86D69F1318E908186E9BB5F11F1CFC85B`; `FUN_00C177E0` `6D4A32F38DA36508E57D17B5BE7DBBCEC5A284129F4881B7E28EAA2C68C139A2`.

### Selected registration callsite

- Raw bytes at `0x00A0F148–0x00A0F166` first push table-pointer address `0x012E54B0`, then the key-factory flag `1` and string VA `0x010D0438`. `FUN_00454FE0` consumes the latter two arguments (`ret 8`) and returns the caller's local key-object pointer; the earlier table pointer remains on the stack. The caller pushes the returned key-object pointer and calls `FUN_0044C310` with `ECX = 0x01435408`, so the wrapper receives `{key_object_pointer, table_pointer}`. The string at `0x010D0438` is `DisBehaviorNotice`.
- EXP-0137 joins this callsite's key and pointer symbol to UELib class path `Class'DishonoredGame.DisBehaviorNotice'`. EXP-0138 records that `0x012E54B0` contains a `.rdata` pointer to `UDisBehaviorNoticeexecRequestStateExitCallback_GenericAction` followed by `.text` target `0x009F5540`. These joins identify the values supplied by this example; they do not establish registry ownership or a consumer.
- Callsite byte-range SHA-256 (`31` bytes): `A0F53C3A9F85D656B71C12B61D1248965BA31F0705976F48730D952C05555D8D`.

## Interpretation and claim limits

- **Confirmed static implementation:** the helper performs lookup/update/insert over indexed five-dword slots, using a two-dword key, an associated value field, a bucket-chain link, and a stored bucket index. The wrapper returns the address of the associated-value field.
- **Observed static handoff:** the selected `DisBehaviorNotice` callsite passes a string-derived key handle and the pointer at `0x012E54B0` to the wrapper with receiver address `0x01435408`.
- **Inferred, narrow:** in the selected registration family the associated value is a pointer to a native-exec name/target list. This follows from the class/key labels and the raw pointer row in EXP-0138; the helper's generic record structure alone does not name that value's type.
- **Unknown:** the exact type and owner of the registry at `0x01435408`, all callers and values, the full set of consumer paths, whether stored pointers are dispatched, how `FUN_00454FE0` represents/normalizes keys beyond the two words read here, and runtime invocation/reachability. EXP-0159 traces one static lookup and name-to-pointer traversal only.
- **Limit:** raw bytes prove local x86 operations only. They do not prove that this initializer runs in the selected game session or that its registrations cause native function dispatch.

## Reproduction

From the repository root, disassemble the complete function ranges shown above with `tools/disassemble_va.py`. Calculate each raw-range digest by opening the exact EXE with `pefile`, mapping `VA - ImageBase` with `get_offset_from_rva`, slicing the indexed function size, and applying Python `hashlib.sha256`. The callsite is a 31-byte slice from `0x00A0F148` through `0x00A0F166`, inclusive. Confirm the executable SHA-256 before interpreting any VA.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior helper pseudocode review: [EXP-0075](EXP-0075-native-class-table-registration-helper.md)
- Class/key extraction: [EXP-0137](EXP-0137-native-class-registration-group-uelib-join.md)
- Raw pointer rows: [EXP-0138](EXP-0138-native-class-table-raw-pointer-validation.md)
- UELib NativeFlag/zero-token joins and unresolved ownership: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- One static lookup consumer, without caller/runtime proof: [EXP-0159](EXP-0159-native-class-table-static-consumer-lookup.md)
