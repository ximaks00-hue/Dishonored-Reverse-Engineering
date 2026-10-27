---
id: EXP-0035
title: "PlayerPawn context-manager population and dispatch"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Which class owns the +0x59C manager used by the EXP-0034 dispatch candidate?"
---
# EXP-0035 — PlayerPawn context-manager population and dispatch

- Status: the manager used by the EXP-0034 dispatch candidate is tied to the `DishonoredPlayerPawn` vtable path. The `+0x4BC` interface thunk adjusts back to the outer Pawn, so the observed inputs are Pawn-relative fields, not a separate object returned by that interface. The selected object's runtime class and any relation to user `Use` or Blink remain unresolved; the known `UsePower` implementation is ABI-incompatible with the inspected `FUN_00C04C30` call sequence.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; read-only MCP decompilation, disassembly, and xrefs.
- Package: workspace `DishonoredGame/CookedPCConsole/DishonoredGame.upk`, UE3 version `801/30`.
- Method: read-only package summary/object-name search and Ghidra analysis. No game files or Ghidra program bytes were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. The current `ue_explorer` MCP session successfully inspected `DishonoredGame.upk` and returned version `801/30`, engine version `9411`, 30,049 exports, 652 imports, 16 compressed chunks, and compression flags `2`. `search_objects("DisTweaks_UsePower")` returned the class export, its default object, and `pPlayerUsePower`. `decompile_object` returned an explicit limitation: UELib can read this package summary but cannot load/decompile its compressed object tables. Thus this session verifies tool registration, root resolution, package summary, and name search, but not object property values. The configuration/default values remain supported by the decompressed UELib artifact cited in EXP-0033.
2. The exact-build constructor evidence in EXP-0021 identifies `FUN_00ABF830` as the constructor path that installs the `DishonoredPlayerPawn` primary vtable `0x0111A3B0`; its base call is `FUN_00ABED50`.
3. Ghidra xrefs place `FUN_00B58860` at `0x0111A96C`, exactly `0x5BC` bytes after `0x0111A3B0`; they place `FUN_00AB3210` at `0x0111A978`, exactly `0x5C8` bytes after that same vtable base. The constructor installs this table. Therefore both functions are methods in the `DishonoredPlayerPawn` vtable path at slots `+0x5BC` and `+0x5C8`, respectively.
4. `FUN_00B58860` loads the secondary vtable pointer at `pawn+0x4BC` and invokes slot `+0x10` with `ECX=&pawn+0x4BC`. The `FUN_00ABED50` constructor writes vtable `0x01119918` at that field. Its slot `+0x10` contains `FUN_00ABEF90`, whose complete body is `LEA EAX,[ECX-0x4BC]; RET`; the call therefore returns the outer Pawn pointer. UELib independently declares `DishonoredPawn implements DisTweaksInterface` and includes a no-export interface-vtable field, consistent with this secondary-vptr path. The identity of the table as that interface's vtable is supported by the constructor, thunk, and metadata, but no standalone RTTI/name record was found. The following accesses are Pawn-relative, not fields of a separate interface-returned object.
5. Since the interface call returns `pawn`, `FUN_00B58860` passes the pointer stored at `pawn+0xE0`, the pawn itself, and the manager at `pawn+0x59C` to `FUN_00C18C80`. `FUN_00C18C80` initializes manager state (`+0xE0`, `+0xDC`) and creates/registers objects in the 0x0C-stride array at manager `+0x38` (count `+0x3C`, capacity `+0x40`). It invokes slot `+0x12C` on the object supplied from `pawn+0xE0` to obtain a class, creates an instance, then calls the instance's slots `+0x130` with that supplied object and `+0x144` with the manager. The first two initialized manager entries correspond to loop values 1 and 2. The supplied object's runtime class and the virtual methods' reflected semantic names remain unknown.
6. After `FUN_00C18C80`, `FUN_00B58860` reads a pointer/count pair from the Pawn itself at `+0xD4/+0xD8`; source records have an 8-byte stride. It reserves capacity in the same manager array and calls `FUN_00C04B80` for each pair (DWORD at source `+0`, byte at source `+4`). `FUN_00C04B80` appends a 0x0C-byte manager record with a null first DWORD, the supplied DWORD at `+4`, and the supplied qualifier byte at `+8`. The meaning and named Unreal properties for the Pawn fields and source values are unresolved.
7. The same manager field `pawn+0x59C` is consumed by the path in EXP-0034. `FUN_00AB3210` is in the `DishonoredPlayerPawn` vtable at `+0x5C8`; on its accepted branch it calls `FUN_00AA2590` with the outer pawn as receiver. `FUN_00AA2590` reads that receiver's `+0x59C` manager and calls `FUN_00C04C30`, which resolves the selected array entry and invokes its virtual slots `+0x134` and, conditionally, `+0x188`. This closes the object-owner/manager-field link from population to this dispatch route.
8. The operation handled by `FUN_00AB3210` is still unnamed. Its body checks mode, flags, object state, and `FUN_00C11B50`; its accepted branch calls `FUN_00B5D400`, invokes the selected-context dispatcher, and changes a state bit. Neither its vtable offset nor these checks identify a physical button or the game's `Use` action.
9. The `FUN_00C04C30` call ABI weighs against identifying its selected object as `DisItemContext_UsePower`. At `0x00C04C48`–`0x00C04C50`, the `+0x134` target is called with `ECX=receiver` and no explicit stack argument. Its conditional `+0x188` call pushes three DWORDs (`0x00C04C64`–`0x00C04C69`). The known `DisItemContext_UsePower` targets are `+0x134 -> FUN_00C44D30` and `+0x188 -> FUN_009EA9D0`; both use `RET 4`, and `FUN_00C44D30` reads a float at `[EBP+8]` (EXP-0028/0034). These callee-cleanup sizes do not match the call site's no-argument/three-argument stack behavior. Accordingly, the slot coincidence is not evidence for a UsePower receiver and the inspected route should be deprioritized as the missing Blink activation edge.
10. No evidence in this pass joins the manager at `pawn+0x59C` to the separate 0x30-stride records read by `FUN_00C0CA70`, nor to the keyed callback registry around `FUN_00B36CA0`. Keep these as distinct mechanisms pending a concrete pointer/dataflow edge.

## Evidence classification

- **Confirmed:** workspace package inspection/search succeeds; package compression blocks object decompilation through this MCP; the `DishonoredPlayerPawn` constructor/vtable association; the `+0x5BC/+0x5C8` method slots; constructor-installed secondary vtable at `pawn+0x4BC` and slot `+0x10` thunk arithmetic returning the Pawn; `pawn+0x59C` manager use; manager setup/population call arguments, array strides/counts, and appended record writes; the same manager is used by the `AA2590 -> C04C30` dispatch path; raw call/callee stack behavior cited above.
- **Supported interpretation:** the secondary vtable at `pawn+0x4BC` is the Pawn's `DisTweaksInterface` implementation; the manager is a context-object manager; records inserted by `FUN_00C04B80` are metadata/configuration-derived placeholders because the first DWORD is null and `FUN_00C04BD0` returns that first DWORD. Their eventual consumer/producer is not yet known.
- **Unknown:** the runtime class stored at Pawn `+0xE0`; the named Unreal properties corresponding to Pawn `+0xD4/+0xD8/+0xE0`; slot `+0x12C/+0x130/+0x144` semantics; later writer that fills null record pointers; operation/input meaning of `FUN_00AB3210`; runtime selected-object vptr; any relation to `DisItemContext_UsePower`, `FUN_00C0CA70`, `FUN_00B36CA0`, or Blink activation.
- **Deprioritized:** treating the `FUN_00C04C30` dispatch as the UsePower/Blink input path, because its observed stack ABI conflicts with both known UsePower virtual targets.

## Next analysis

1. Map Pawn `+0xD4/+0xD8/+0xE0` to named native/reflected fields and identify the runtime class at `+0xE0`; the interface slot itself returns the outer Pawn via the verified adjustment thunk.
2. Find code that changes the first DWORD of the manager's 0x0C-stride entries from null to an object pointer; establish whether that writer acts on `pawn+0x59C` and what creates the object.
3. Resolve the dynamic class selected at `FUN_00C04BD0` and the semantics of `FUN_00AB3210`; do not infer `Use` from controller naming or slot numbers.
4. Keep `FUN_00C0CA70`'s 0x30-stride dispatch array and `FUN_00B36CA0`'s keyed registry on separate evidence graphs until a shared owner/pointer is demonstrated.
5. Join to Blink only if a concrete selected receiver resolves to `DisItemContext_UsePower` and the call arguments/ABI match `FUN_00C44D30` and `FUN_009EA9D0`.

