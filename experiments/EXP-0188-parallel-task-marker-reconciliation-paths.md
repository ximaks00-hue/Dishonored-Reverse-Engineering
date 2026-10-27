---
id: EXP-0188
title: Parallel task-marker reconciliation paths and callback arrays
experiment_status: done
claim_status: mixed
build: "10256413"
question: How do the two exact-build reconciliation routines differ in candidate input, matching, construction, storage, and stale-entry handling?
---

# EXP-0188 — Parallel task-marker reconciliation paths and callback arrays

- Date: 2026-10-27 (Europe/Kiev).
- Target executable: Steam app `217980`, x86 build `10256413`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build cached decompilation, function-dossier cross-check, and raw x86 inspection for `FUN_00BAD550`, `FUN_00BAD960`, their wrapper `FUN_00BB00C0`, and constructors `FUN_00BCE750` / `FUN_00BCE9A0`.
- No game launch, runtime trace, package payload parsing, memory write, or binary patch was performed.

## Procedure

1. Re-read the research status, Blink activation graph, and registered build record. Confirm the EXE hash above.
2. Read current decompilation JSON for the two reconciliation functions, wrapper, constructors, and removal helpers; verify each relevant cache records build `10256413` and the registered EXE SHA.
3. Compare the two reconciliation paths by input array, object match key, constructor, owner offsets, and visible branch conditions. Keep all structure/type names neutral unless supported by exact-build bytes.
4. Map the cleanup callsites from VA through PE sections to raw file offsets and decode x86 using Capstone; compare stack/register setup with the helper prototypes.
5. Cross-check function dossier callers/callees and cache hashes. Treat decompiler output as a rendering of target instructions and do not infer missing call arguments.

## Observations

- The local cache files for `FUN_00BAD550` (`10B43CA8F9E9265B73F465DF6CC185411489574D5C988BA809667E6EB001C2FB`), `FUN_00BAD960` (`FD20E4B1954E0543F30C6A602A7A532EFF10E2F94829D271469259C8D4052530`), `FUN_00BB00C0` (`A2FED82F1D52390E551D29073E6821477030C3D08B88D28161F969026E080FA1`), `FUN_00BCE750` (`5E7F646C2C03AFD77A5C981EF723674ACF508B6B7E806A1F8F0BEDCE0B0C62AB`), `FUN_00BCE9A0` (`0E63D8485848A117EF670C689AFDDEE97CFD52515DCBB52E432FFC3DECCD957B`), `FUN_00BD6640` (`1B16A5F0B1A9A6D3E8E535D4A84517742F804DD212450DA543CD4E92D295E4A2`), and `FUN_00BCEB00` (`664EA8543F6772C7291A71FCD1428DD67485E194F5CFEFAE3F6FC250B32DB8F0`) all carry the registered build ID and EXE SHA.
- Raw PE mapping confirms `FUN_00BAD960` starts at VA `0x00BAD960`, RVA `0x007AD960`, file offset `0x007ACD60`; the indexed body is 1,563 bytes with SHA-256 `223F16C8D12CB28A3F0ABBFF62E86FD6371BD58ACA181B26D6A44F9F14F12DE2`.
- `FUN_00BB00C0` calls `FUN_00BAD550`, then `FUN_00BAD960`, then iterates pointers in owner `+0x554` with count `+0x558`, invoking each object's virtual slot `+0x0C` with the wrapper's second argument. Its indexed direct caller is `FUN_00BB2280` at callsite `0x00BB23C4`.
- `FUN_00BAD550` obtains candidate row pointers from `FUN_00AD9910` in selector mode 1 when owner flag `+0x1C0` bit `0x80` is set. Its existing collection is owner `+0x524/+0x528`; the match key is existing object `+0x08` versus candidate row's first DWORD. For a missing item it allocates `0x88` bytes and calls `FUN_00BCE750`. It stores the object in `+0x524/+0x528` and appends the same pointer to the secondary `+0x554/+0x558` list. Selected settings depend on candidate row DWORD `+0x20` bit 0. Constructor `FUN_00BCE750` reads row byte `+0x1C`, as described in EXP-0184.
- `FUN_00BAD960` begins by invoking slot `+0x700` on the object at global pointer `0x0145F628`, with a local candidate-array descriptor and stack values `2` and `0`. EXP-0189 resolves the pointer's constructor/vtable provenance to a `DishonoredPlayerPawn` instance and the slot target to `FUN_00AB6960`: it walks a linked list rooted at Pawn `+0x9D4`, follows item `+0x90`, applies `FUN_00B0B780` in mode 2 with no threshold, and appends accepted item pointers. It then iterates Pawn array `+0xAC8` (count `+0xACC`), passes each element through `FUN_00B599B0`, and appends each non-null result to the same local candidate list using `FUN_00BA1330`. The list and array element categories remain unknown.
- `FUN_00BAD960` filters each temporary candidate through `FUN_00BA6E50`; its match key is existing object `+0x08` versus candidate actor pointer at candidate `+0x15C`. Its primary array is owner `+0x530/+0x534`. For a missing candidate it allocates `0xD8` bytes (raw `push 0xD8` at `0x00BADC27`; note this differs from the prior pseudocode-derived 0x88 estimate), calls constructor `FUN_00BCE9A0`, stores the result in `+0x530/+0x534`, and appends that pointer to the shared secondary `+0x554/+0x558` list. It writes object DWORD `+0x28` from candidate actor DWORD `+0x120` bit 0. These raw details supersede EXP-0188's initial cache-only estimates; no use of the `FUN_00BCE750` preset branch is shown in this path.
- After candidate reconciliation, `FUN_00BAD960` scans its primary array. For entries where `((byte)*(object+0x1C) & 0x8F) == 1`, raw x86 at `0x00BADE45–0x00BADE57` sets ECX to the secondary array descriptor `owner+0x554`, pushes the address of the current primary-array slot as the comparison pointer, and calls `FUN_00B36C00`. The helper compares `*array[i]` with `*target`, so this removes the same object pointer from the secondary list. The code then invokes the object's vtable slot 0 with stack argument `1`, and calls `FUN_00A4DDD0` with ECX=`owner+0x530`, index `i`, and count `1`, removing the current primary entry.
- Constructor `FUN_00BCE9A0` installs vtable pointer `0x011635C0`; raw PE data at file offset `0x00D61FC0` shows slot 0 = `0x00BD6640`. The exact-build indexed function `FUN_00BD6640` (33 bytes; body SHA-256 `C78F5687FC17BBAC5C642E26BBBE96B1009F521E197879B397D01B0F3C36F86E`) calls `FUN_00BCEB00`, tests the byte argument's bit 0, and calls `FUN_004042E0(this)` when set. `FUN_004042E0` passes that pointer to a virtual callback at slot `+0x0C` of the object stored at global `0x0140A90C`; the callback's semantic name is unresolved. In `FUN_00BAD960`, slot 0 receives `1`, so the object cleanup and this global callback are reached along the static branch. This does not establish when the branch executes in a game session or prove the callback is a memory free operation.
- The raw allocation at `0x00BADC25–0x00BADC59` reserves `0xD8` bytes, then passes candidate actor pointer, owner-context pointer `owner-root+0x7B4`, and owner `+0x38` to `FUN_00BCE9A0`. Its constructor initializes the object fields/vtable; do not use the previous 0x88 estimate, which came from an incorrect reading of cache pseudocode and is now superseded.
- `FUN_00BAD550` has a separate stale-tail loop. Raw x86 at `0x00BAD88E–0x00BAD8A3` loads the current primary slot address, sets ECX to owner `+0x554`, and calls `FUN_00B36C00`; it then calls object vtable slot 0 with argument `1`, and calls `FUN_00A4DDD0` with ECX=`owner+0x524`, index `i`, and count `1`. Thus both paths remove from the shared secondary array, call slot 0 with `1`, and remove the corresponding indexed primary item, while using different primary-array offsets.
- `FUN_00BCE9A0` initializes a different vtable pointer (`0x011635C0`) from `FUN_00BCE750` (`0x011635A8`), stores constructor arguments at object `+0x08/+0x0C/+0x10`, initializes additional fields and three-element arrays, and derives a pointer stored at object `+0x38` from its fourth argument. These observations support distinct construction paths, not semantic class names.
- The two vtables share a six-entry suffix: slots 6–11 of `0x011635A8` equal slots 0–5 of `0x011635C0`. This is a byte-level table observation, not proof of inheritance. Their slot `+0x0C` entries differ: `0x011635A8` points to `0x005CB0C0` (`ret 4`), while `0x011635C0` points to `0x00BB9FF0`. The latter body subtracts its second float argument from object fields `+0xC8` and `+0xD0`. `FUN_00BB00C0` forwards its second argument to each secondary-array object's slot `+0x0C`; its direct caller `FUN_00BB2280` passes a float argument. This establishes a polymorphic callback/update pass and one concrete field effect, but does not identify the objects or fields semantically.
- `FUN_00B36C00` and `FUN_00A4DDD0` are generic array-removal helpers in the local function dossiers. This does not resolve the stale-entry policy or callback meaning in the caller.

## Interpretation

- **Observed:** the two routines reconcile different candidate sources into different primary collections. `FUN_00BAD550` matches task-target rows and constructs via `FUN_00BCE750`; `FUN_00BAD960` gathers filtered entries through a `DishonoredPlayerPawn` linked collector at `+0x9D4` and a second Pawn array at `+0xAC8/+0xACC`, then applies the `FUN_00BA6E50` candidate gate, matches actor pointers, and constructs via `FUN_00BCE9A0` (details and limits in EXP-0189).
- **Observed:** both append newly created pointers to the array at `+0x554/+0x558`, which `FUN_00BB00C0` subsequently traverses with a slot-`+0x0C` virtual call. The two constructor-installed vtables use different targets for that slot: one is a `ret 4` stub, and the other subtracts the forwarded float argument from fields `+0xC8/+0xD0`. The common table suffix and differing callbacks do not prove inheritance or identify either object family. The shared array's semantic name remains unknown.
- **Observed:** stale-entry cleanup in `FUN_00BAD960` removes the object's pointer from the secondary array, calls slot 0 with argument `1`, and removes one item at the same index from the primary array. The installed slot-0 target calls `FUN_00BCEB00`, then passes `this` to an unresolved global virtual callback when argument bit 0 is set. Raw call setup, vtable data, and helper bodies confirm this static call sequence.
- **Inferred only at structural level:** the primary arrays `+0x524/+0x528` and `+0x530/+0x534` hold separate collections associated with the two reconciliation paths. Their object roles may differ; no common type or gameplay meaning is asserted.
- **Unknown:** semantic identity of the linked-list and array entries, meaning of the mode-2 filter and the spatial thresholds, the `+0x1C` mask and object `+0x28` bit, runtime execution/visibility, and relation to a particular Boyle Kismet node.

## Next discriminating work

1. Identify writers/registration paths for Pawn list head `+0x9D4`, its `+0x90` next link, and array `+0xAC8/+0xACC`, without assigning semantic names from offsets alone. EXP-0189 did not find a Pawn-specific `+0x9D4` writer in its bounded scan. The same global pointer is referenced by objective-notification handlers in EXP-0171; whether those references share any dataflow beyond the global is unresolved.
2. Compare the two constructor vtables and object-field consumers to test whether the primary collections are separate object families.
3. Trace slot `+0x0C` targets and consumers for both vtables to establish the callback contract and the meaning, if any, of fields `+0xC8/+0xD0`.
4. Keep preset enum labels and retail Kismet links at their current evidence level; no runtime behavior is established.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Prior marker and preset path: [EXP-0184](EXP-0184-task-target-selector-to-marker-and-focus-path.md)
- Related task-target record evidence: [EXP-0181](EXP-0181-task-target-per-instance-array-and-archive-paths.md), [EXP-0182](EXP-0182-task-target-layout-and-save-crosswalk.md)
- Pawn candidate-source follow-up: [EXP-0189](EXP-0189-player-pawn-candidate-collector-and-distance-gates.md)
- Evidence cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
