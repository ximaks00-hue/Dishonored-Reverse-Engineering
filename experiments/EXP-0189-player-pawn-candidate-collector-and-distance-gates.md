---
id: EXP-0189
title: Player Pawn candidate collector and distance gates
experiment_status: done
claim_status: mixed
build: "10256413"
question: What concrete source and gates feed the second candidate stream in task-marker reconciliation?
---

# EXP-0189 — Player Pawn candidate collector and distance gates

- Date: 2026-10-27 (Europe/Kiev).
- Target executable: Steam app `217980`, x86 build `10256413`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build static cache and function-index review, read-only PE/vtable mapping, and raw x86 spot checks for `FUN_00ABF830`, `FUN_00AB5320`, `FUN_00AB6960`, `FUN_00B0B780`, `FUN_00B599B0`, and `FUN_00BA6E50`; follow-up of the collection path used by `FUN_00BAD960` in EXP-0188.
- No game launch, runtime trace, package payload parsing, memory write, or binary patch was performed.

## Procedure

1. Re-read the current research status, Blink graph, and registered build record; verify the exact EXE identity.
2. Verify build/hash metadata and file SHA-256 for each local decompilation cache listed in the companion evidence JSON.
3. Map Pawn vtable `0x0111A3B0` and slot `+0x700` through the target PE; compare the slot target with the exact-build function index.
4. Decode the constructor/destructor global-pointer writes and the `FUN_00BAD960` indirect-call setup from raw x86.
5. Trace the returned list items through the exact-build collector, predicate, pointer-return helper, and candidate distance gate. Record numeric fields and branches without assigning unsupported gameplay names.

## Observations

- Raw x86 in `FUN_00ABF830` writes vtable pointer `0x0111A3B0` to the constructed object's first DWORD at `0x00ABF88D`. EXP-0021 and EXP-0035 identify this exact vtable path as `DishonoredPlayerPawn`.
- At `0x00ABF986`, `FUN_00ABF830` writes its `ESI` object pointer to global `DAT_0145F628`, after its constructor loop reaches the normal return path. An earlier failure branch returns before this assignment. `FUN_00AB5320` writes zero to the same global at `0x00AB535A`.
- Vtable `0x0111A3B0` is at file offset `0x00D18DB0`; slot `+0x700` is VA `0x0111AAB0`, file offset `0x00D194B0`, and contains pointer `0x00AB6960`. The function index records `FUN_00AB6960` as a 138-byte body.
- Raw call setup in `FUN_00BAD960` loads the object from `DAT_0145F628`, loads its slot `+0x700`, and calls it with `this` equal to that object, a local array descriptor, mode `2`, and fourth argument `0`. With the constructor/vtable evidence above, this statically resolves the call receiver as a `DishonoredPlayerPawn` instance.
- `FUN_00AB6960` starts from the pointer at Pawn `+0x9D4`; it repeatedly advances through a next pointer at item `+0x90` via `FUN_00AA1EC0`. For each item, it calls `FUN_00B0B780(Pawn, item, 2, 0)`. Items for which the predicate returns nonzero are appended as pointers to the output array. The list's node type and purpose are not established.
- Exact-build callers `FUN_00AA4EA0` and `FUN_00AB9EA0` also walk Pawn `+0x9D4` through the same `+0x90` next-link and call `FUN_00B0B780`; the latter uses iterator helper `FUN_00AA1EB0`. This supports a shared linked traversal/filter pattern, but does not provide a semantic category name.
- Follow-up direct-displacement census: searching the exact-build PE for little-endian `0x9D4` occurrences and decoding/mapping each hit against the 72,437 indexed function bodies found six effective memory operands. Three are Pawn-context reads/address-of-head in `FUN_00AA4EA0`, `FUN_00AB6960`, and `FUN_00AB9EA0`; two are accesses in the `_Font_Cache` path (`FUN_00DB95D0` stores a float at object `+0x9D4`, and `FUN_00DB9E40` reads a float there); one in `FUN_009B8760` indexes a separate pointer array. No explicit Pawn-specific writer was found in the indexed bodies. Two other raw byte-pattern matches decode as branch displacement/immediate overlap, not effective memory operands. This does not exclude indirect/aliased stores, unindexed code, or zero-initialized allocation.
- Raw call setup corrects the cached decompiler rendering of `FUN_00B0B780`: at `0x00B0B7A1`, `mov ecx,[0x014719C4]` loads a global context object; the routine pushes candidate `item+0x4B8` and context `(Pawn[+0x15C])+0x4B8`, calls `FUN_00C62F20`, then invokes the context object's virtual slot `+0x10` with the candidate field pointer and helper result. It compares that return value to the requested mode (`2` here). The cached pseudocode assigns the helper call a different receiver/argument shape; raw x86 takes precedence. `FUN_00C62F20` has table/normalization behavior and other callers branch on numeric results 0/1/2, but the keys, categories, and semantic labels remain unresolved.
- Provenance for this correction: exact-build cache records `00B0B780.json` (SHA-256 `6B75E9E5B4658336DAA4052FFA8A9D2F78EE0C8C8A743FA425C41C62CEA055C3`) and `00C62F20.json` (SHA-256 `52B495F487BE784EF4D9BD6ECA7B23CB9D7A2545E78CE7C52B0CCC98D1585B89`) are bound to the registered build/hash. Cache hashes identify the JSON artifacts, not separate instruction-byte extracts; the recorded instruction addresses and disassembly are from the exact-build PE.
- `FUN_00BAD960` also walks Pawn array data `+0xAC8` for count `+0xACC`. Each entry is passed to `FUN_00B599B0`; a non-null returned pointer is appended to the same local candidate array. `FUN_00B599B0` checks entry bit `+0x508 & 0x400` is clear, resolves entry `+0x26C` through `FUN_00A660F0`, requires resolved-object field `+0x380` to be nonzero, and checks the bit-6 predicate from `FUN_00B00D20` on the object pointed to by that `+0x380` field before returning the pointer. The raw call keeps ECX equal to the `+0x380` object for `FUN_00B00D20`.
- Candidates from the temporary array are passed through `FUN_00BA6E50` before reconciliation. The function first requires `FUN_00BA0DE0(candidate, mode)` to return nonzero and applies an additional owner-byte `+0x1FE` bit-0 exclusion when the mode is `4`. It computes squared-distance comparisons against radii stored at owner-settings `+0x7FC`, `+0x800`, or `+0x804`; the last two are selected by the result of `FUN_00B4A300` on the candidate's pointer at `+0x15C`. The candidate pointer at `+0x15C` is then the key compared with existing reconciliation-object field `+0x08` in EXP-0188. These are numeric/static observations; the settings fields, candidate types, and user-visible meaning are unknown.
- EXP-0188 shows a separate resolved sequence over the same local array: each entry is converted through `FUN_00B599B0` only in the `+0xAC8` branch, then accepted candidates share the `FUN_00BA6E50` gate. The slot-`+0x700` collector's list entries are appended directly; this experiment does not claim that both source branches contain the same semantic type.

## Interpretation

- **Confirmed by exact-build static evidence:** `DAT_0145F628` is assigned the constructed object whose vtable path EXP-0021/0035 identify as `DishonoredPlayerPawn`; its cleanup path clears the global. `FUN_00BAD960` invokes that object's vtable slot `+0x700`, and the exact vtable entry points to `FUN_00AB6960`.
- **Observed:** slot `+0x700` collects filtered pointers from a linked traversal rooted at Pawn `+0x9D4`, while a second source traverses Pawn array `+0xAC8/+0xACC` and maps entries through `FUN_00B599B0`. Both feed the temporary candidate descriptor used by reconciliation.
- **Observed:** the `+0x9D4` traversal and `FUN_00B0B780` predicate are also used by two other indexed Pawn functions; the node category remains unknown. A full indexed effective-displacement census found no explicit Pawn-specific writer for `+0x9D4`; other structures use the same numeric offset for unrelated float/pointer-array fields.
- **Observed:** the collector call uses mode `2` and threshold `0`; raw call setup shows a global context at `0x014719C4`, a `FUN_00C62F20` helper call, and a virtual `+0x10` result compared with that mode. Numeric category semantics remain unknown. The later candidate gate uses squared distances and owner-settings values at `+0x7FC/+0x800/+0x804`.
- **Unknown:** the linked-list element class, semantic meaning of the mode-2 virtual result, meaning of the `+0xAC8` array elements and `+0x380` pointer, radius-setting names, visibility effects, runtime frequency, and connection to a specific retail Kismet node.
- The shared global pointer's use by notification handlers is a cross-reference to the same global variable, not proof that their arrays or control-flow roles are the same subsystem as this candidate collector.

## Next discriminating work

1. Search constructor/allocation and alias/dataflow paths for initialization of the Pawn list head `+0x9D4`, next pointer `+0x90`, and array `+0xAC8/+0xACC`; direct indexed displacement search found no Pawn-specific writer, but does not rule out zero-init or indirect writes.
2. Resolve the global context at `0x014719C4`, `FUN_00C62F20` table keys, and the nested virtual `+0x10` implementation/value categories, including other callers of `FUN_00B0B780`.
3. Trace candidate `+0x15C` provenance and owner-settings `+0x7FC/+0x800/+0x804` consumers to test the static radius gates without assigning UI semantics from offsets alone.
4. Keep runtime visibility, concrete Boyle node linkage, and all behavior claims unknown until independently supported.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Player Pawn vtable and selection context: [EXP-0021](EXP-0021-exact-class-vtables-power-selection.md)
- Reconciliation and callback arrays: [EXP-0188](EXP-0188-parallel-task-marker-reconciliation-paths.md)
- Evidence cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
- Machine-readable evidence: [EXP-0189 evidence JSON](../research/executable/evidence/EXP-0189-player-pawn-candidate-collector.json)
