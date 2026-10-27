---
id: EXP-0031
title: UsePower context lifecycle and callback cleanup
experiment_status: done
claim_status: mixed
build: "10256413"
question: "How do UsePower context lifecycle/callback cleanup helpers behave, and do they join activation?"
---
# EXP-0031 — UsePower context lifecycle and callback cleanup

- Status: the shared cleanup/state boundary around `DisItemContext_UsePower` is better characterized; the callback registration producer and user-input caller remain unidentified.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; read-only MCP decompilation/call graph.
- Method: static analysis only. No game files or Ghidra program bytes were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. The exact-build constructor candidate `FUN_00C43700` for `DisItemContext_UsePower` calls base initializer `FUN_00C04210`, then installs vtable `0x01183620` at object offset 0 and interface vtable `0x01183604` at `+0x38`. It does not visibly assign the callback-token field at `+0x50`. The base initializer `FUN_00C04210` clears a block of fields `+0x54` through `+0x9C` and `+0x50` is not part of its explicit zeroing sequence; absence from this constructor pseudocode does not prove the field remains unset after other initialization.
2. Shared cleanup routine `FUN_00C128F0` reads the DWORD at `this+0x50`, clears it, and, when nonzero, submits a cleanup callback through `FUN_0094DF00`/`FUN_00AEDF80` using callback `FUN_00C128B0`. The callback compares the saved token with the callback object's field at `+8`; on a match it clears the token and requests callback removal. This supports a callback-registration lifecycle associated with the object layout, but does not identify the event or the code that initially stores the token.
3. `FUN_00C128F0` is called by cleanup routines `FUN_00C2EBE0`, `FUN_00C309A0`, and `FUN_00CDFCC0`. These callers show that the helper is shared across several object paths; they do not by themselves attribute every call or the callback to a specific input event.
4. `DisItemContext_UsePower` slot `+0x134` target `FUN_00C44D30` has this static sequence: it first checks bit 2 at `*([context+0x3C]+0x114)+0x78`; under that condition it resolves an object from a global context and, if the result is null or its byte at `+0x62D` is zero, calls component slot `+0x174`. For a Blink component, the corresponding slot is `FUN_00BE7580` (EXP-0028). After that guarded branch, it calls `FUN_00BE70C0`; if that helper returns zero, it invokes `FUN_00C12930(3)`.
5. `FUN_00BE70C0` calls receiver slot `+0x160`; only when that call is nonzero does it dispatch another virtual call at `+0x1A8`. This helper is called with the component at context field `+0x114`; its exact receiver class and semantic contract are not established here.
6. `FUN_00C12930` is a shared state-transition routine with numerous callers. In the `FUN_00C44D30` path it receives integer 3, invokes context slot `+0x19C`, stores the argument as a byte at context `+0x41`, and performs additional owner/context checks. The same helper's broad call graph means the integer is recorded as a numeric state argument here; its semantic name is unknown.
7. The direct-call graph shows no ordinary code callers for `FUN_00C44D30` or `FUN_00C4B800`, consistent with their being virtual targets. EXP-0029's `FUN_00C0CA70` remains a slot-compatible generic dispatcher candidate, but its stored receiver is not proven to be a `UsePower` instance. No edge from PlayerController Use, the controller interaction FSM, `CastBlink`, or a proven animation event to this slot was established.
8. `FUN_00C105F0` is the setter for the callback token at `this+0x50`: it stores the supplied token; on zero→nonzero it registers `FUN_00C128B0` through `FUN_00B36CA0`, and on nonzero→zero it removes it through `FUN_00AEDF80`. The call graph reports one direct caller, `FUN_00C2F750`. Raw instructions at `0x00C2F77F`–`0x00C2F782` show the setter receives `ECX=ESI` and a stack token returned by `FUN_00BFF440` with `ECX=EBX`; `EBX` was loaded from `[input+4]`. `FUN_00BFF440` returns a nested manager pointer from that input object. This establishes one concrete token producer/registration route for the callback framework, but not the callback event's meaning or its relationship to `DisItemContext_UsePower`.
9. Ghidra classifies `0x01174BB4` as a data pointer to `FUN_00C2F750`; surrounding data contains a broad virtual-method-like pointer sequence. No class owner was recovered from this observation, so `FUN_00C2F750` is not attributed to UsePower or Blink.
10. Follow-up decompilation narrows the role of `FUN_00B36CA0`: it scans a manager-owned array at `+0x1650` with count at `+0x1654` for the first DWORD of its key argument. On a match it builds a 24-byte local descriptor and calls `FUN_00933B60`; otherwise it builds a 16-byte descriptor and calls `FUN_009FAC70`. Those helpers respectively write a six-DWORD record or append a four-DWORD record. Thus `B36CA0` is a keyed record update/append helper in this path; calling it a dedicated callback registrar is unsupported. The callback function pointer and fields are part of the descriptor passed into this generic helper, but the record's runtime consumer and event semantics remain unknown.
11. `FUN_00C12A80` is a separate state-copy path with seven direct callers. It copies 20 DWORDs from its source into the destination beginning at `+0x50`; if the first copied DWORD changes between zero and nonzero, it performs the same callback add/remove sequence using `FUN_00C128B0`, `FUN_00B36CA0`, and `FUN_00AEDF80`. This is consistent with a shared object-layout/state helper, but does not tie those callers to `DisItemContext_UsePower`.
12. A separate, exact-build callback-registration path is owned by the `DisItemPowers` virtual table: descriptor `0x01373DA0` names that class, constructor `FUN_00C63630` installs vtable `0x01183820`, and the entry at byte offset `+0x130` is `FUN_00C0F9F0`. Its raw call sequence sets a local key to `9`, calls `FUN_0094DF00` with the key pointer, `this`, callback pointer `FUN_00C0B940`, and zero, then uses the returned manager as ECX for `FUN_00B36CA0`. This is an additional call site of the generic keyed-record helper, separate from the `FUN_00C105F0` / `FUN_00C128B0` path above. `FUN_00C0B940` checks an interface at object `+0x40` and calls `FUN_00C89CD0` with fields at `+0xE4` and the object; `FUN_00C89CD0` traverses a linked structure and passes collected records to `FUN_00C89BC0`. No direct edge from this callback path to `FUN_00C0CA70`, `DisItemContext_UsePower`, or Blink move-mode code is established. The semantic name of key 9 and the callback event remain unknown.

## Evidence classification

**Confirmed in the analyzed binary:** constructor/vtable values as above; `+0x50` callback-token store and add/remove behavior; callback comparison; the `FUN_00C2F750` call-site supplies the result of `FUN_00BFF440` to `FUN_00C105F0`; the branch order inside `FUN_00C44D30`; `FUN_00BE70C0`'s virtual dispatch pattern; `FUN_00C12930(3)` follows only when `FUN_00BE70C0` returns zero in this method; the keyed record scan/update/append behavior of `FUN_00B36CA0`; and the distinct `DisItemPowers` vtable `+0x130` route registering callback `FUN_00C0B940` under local key 9 through the returned manager.

**Supported interpretation:** the `+0x50` field participates in a callback registration/removal lifecycle backed by a generic keyed record manager. The callback's subject, record consumer, and event type remain unknown.

**Unknown:** the complete set of token producers and the class owning the observed `FUN_00C2F750` route; the event semantics of callback `FUN_00C128B0` or the separate key-9 callback `FUN_00C0B940`; whether either callback targets animation events; which method calls `UsePower +0x134` during gameplay; the class behind virtual slot `+0x160`; and whether the observed `FUN_00C44D30` path is the event that starts Blink.

## Next analysis

1. Identify the class/vtable owner of `FUN_00C2F750` and the consumer/manager semantics behind its token from `*(input+4)`; determine whether its receiver is related to item contexts. Do not merge it with Blink until that ownership edge is proved.
2. Recover the dynamic class and dispatch purpose for `FUN_00BE70C0`'s slot `+0x160` / `+0x1A8`.
3. Return to EXP-0029's record receiver at `entry+0x1E0`; prove or disprove that its dynamic vptr is `0x01183620` at an observed call site.
4. Search for the upstream invocation of `FUN_00C44D30` through the item-context or event system. Keep the controller shortcut and `FUN_00CF34E0` branches separate unless a concrete code/dataflow edge joins them.
