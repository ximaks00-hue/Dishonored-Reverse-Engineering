---
id: EXP-0037
title: Pawn manager provenance and dispatch ABI recheck
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does the Pawn manager dispatch ABI match DisItemContext_UsePower, and who writes pawn+0x59C?"
---
# EXP-0037 — Pawn manager provenance and dispatch ABI recheck

- Status: the `pawn+0x4BC` interface thunk is resolved to an outer-Pawn adjustment; manager configuration inputs originate from Pawn fields. The `FUN_00C04C30` call sequence is stack-incompatible with both known `DisItemContext_UsePower` targets. The manager's stored-object writer, field names, and relation to Blink remain unresolved.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra database: `dishonored_exact_full`, x86, image base `0x00400000`; read-only disassembly, raw-byte reads, xrefs, and decompilation.
- Package: decompressed analysis copy `assets/extracted/dishonored-blink/DishonoredGame.upk`, SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`; UELib 1.13.3. Probe output is preserved under ignored `.tmp/uelib-probe/EXP-0037-pawn-class-recheck.log`.
- Method: inspect constructor/vtable instructions, decode the interface thunk, read vtable bytes, simulate x86 stack effects for the virtual dispatch site, inspect all indexed textual references/stores to displacement `+0x59C`, and emit the `DishonoredPawn`/`DisTweaks_Pawn` declarations from the decompressed package. No game file or Ghidra program bytes were modified; `_excluded_coop_project/` was not accessed.

## Findings

1. Constructor `FUN_00ABED50` writes a vtable pointer to `this+0x4BC` twice during base construction: an intermediate table `0x010D9910`, then final table `0x01119918` at `0x00ABEE7D`. Raw Ghidra bytes at `0x01119918` show slot `+0x10` contains `0x00ABEF90`.
2. `FUN_00B58860` loads the pointer at `[pawn+0x4BC]`, then explicitly sets `ECX=pawn+0x4BC` before calling its slot `+0x10`. Decoding `0x00ABEF90` yields exactly `LEA EAX,[ECX-0x4BC]; RET`. Therefore this interface call returns the outer Pawn pointer. The subsequent loads in `FUN_00B58860` are from `pawn+0xE0`, `pawn+0xD4`, and `pawn+0xD8`, not from a separate object returned by the interface.
3. The decompressed UELib declaration says `DishonoredPawn extends GamePawn` and implements `DisTweaksInterface`; it declares a no-export `VfTable_IDisTweaksInterface` and a transient `DisTweaks_Pawn m_pPawnTweaks`. This supports identifying the secondary vptr at `+0x4BC` as the Pawn's tweaks-interface vptr, though no standalone RTTI label for vtable `0x01119918` was found. The offset names `+0xD4/+0xD8/+0xE0` are not joined to UProperty names by UELib, and `m_pPawnTweaks` is not assigned to `+0xE0` as a fact.
4. `FUN_00C18C80` receives the pointer loaded from `pawn+0xE0` as one argument, the outer Pawn as another, and the manager pointer from `pawn+0x59C` in ECX. It invokes slot `+0x12C` on the `+0xE0` object to obtain a class, creates an object, then invokes the new object's slots `+0x130` (with the `+0xE0` object) and `+0x144` (with the manager). That dynamic object's class and the semantics of those methods remain unresolved.
5. The 8-byte-stride source array used by `FUN_00B58860` begins at `pawn+0xD4` and has count `pawn+0xD8`. Its records contribute a DWORD and a qualifier byte to `FUN_00C04B80`, which appends a 0x0C-stride manager record with a null object pointer, the DWORD at `+4`, and qualifier byte at `+8`. No named source property or later writer of the null pointer was identified in this pass.
6. Stack contract, first indirect call: after `FUN_00C04C30` pushes ESI and EDI, it calls vtable `+0x134` with `ECX=receiver` and no explicit argument push. `DisItemContext_UsePower` vtable `0x01183620` holds `FUN_00C44D30` at `+0x134`; its raw instructions read `[EBP+8]` as a float and end with `RET 4`. At this call site `[callee EBP+8]` would alias the caller's saved EDI, and `RET 4` would discard that saved register. The caller's subsequent pops/return would be misaligned. This is a concrete ABI contradiction, not merely a parameter-count difference in decompiler output.
7. Stack contract, second indirect call: if the first returns nonzero, `FUN_00C04C30` pushes three DWORDs before slot `+0x188` and performs no caller-side stack cleanup before its epilogue. The UsePower vtable target at `+0x188` is `FUN_009EA9D0`, whose raw body is `MOV EAX,1; RET 4`; it would remove one of the three pushed arguments, leaving the remaining pushes in front of the caller's saved registers. This call is likewise incompatible. The receiver's dynamic vptr is still unknown, but these exact UsePower targets cannot execute correctly through this call sequence under the observed x86 stack state; a thunk would need to exist in the receiver's slot, and the known UsePower table points directly to these bodies.
8. A Ghidra text scan found 449 instruction references to an operand displacement `+0x59C`, demonstrating that the displacement is widely reused. A narrower scan found nine direct `MOV [base+0x59C],...` stores in the indexed image. The bodies `FUN_00B9F210` and `FUN_00BAF5D0` use that offset as an integer index bounded by an array count at `+0x588` (including `-1` sentinel handling), so they are not stores to the Pawn's manager pointer. The remaining stores were not attributed to the Pawn manager in this pass. Thus the search does not identify the manager pointer's writer or constructor.
9. Exact-build xrefs still tie `FUN_00B58860` and `FUN_00AB3210` to `DishonoredPlayerPawn` vtable `0x0111A3B0` slots `+0x5BC/+0x5C8`, and EXP-0035 ties their use to the manager loaded from `pawn+0x59C`. The ABI check further deprioritizes this dispatch route as the user Use/Blink entry. No edge joins it to `FUN_00C0CA70`'s 0x30-stride array or `FUN_00B36CA0`'s keyed registry.
10. Registry `FUN_00B36CA0` remains unresolved as to its manager owner and event consumer. The 107 code references plus key-3/key-9 examples in EXP-0036 establish shared generic use, but do not identify the owning registry object.

## Evidence classification

- **Confirmed:** the constructor's `+0x4BC` vtable assignment; vtable slot `+0x10 -> FUN_00ABEF90`; thunk's `ECX-0x4BC` return; Pawn-relative `+0xD4/+0xD8/+0xE0` accesses; call-site stack operations and raw callee cleanup for both UsePower targets; the two unrelated `+0x59C` integer-index uses; package declaration that `DishonoredPawn` implements `DisTweaksInterface`.
- **Supported interpretation:** vtable `0x01119918` is the `DisTweaksInterface` secondary vtable; the pointer at Pawn `+0xE0` is a tweak/factory object because C18C80 queries its slot `+0x12C`; `pawn+0x59C` holds a separate manager object.
- **Unknown:** exact interface/vtable attribution absent an RTTI/name record; named properties for offsets `+0xD4/+0xD8/+0xE0`; dynamic class/value at `pawn+0xE0`; source/allocation/setter for the manager pointer at `pawn+0x59C`; null-record population path; selected receiver class at `FUN_00C04C30`; owner and event consumer of `FUN_00B36CA0`; relation to user Use/Blink.
- **Rejected for the observed call path:** selecting `DisItemContext_UsePower` as the receiver of `FUN_00C04C30`'s `+0x134/+0x188` calls. The exact table targets and ESP behavior are incompatible absent an alternate receiver thunk; the known UsePower table has no such thunk at those slots.

## Next analysis

1. Identify the native property/type behind Pawn `+0xE0` and the 8-byte-stride records at `+0xD4/+0xD8`; determine whether `m_pPawnTweaks` is involved without assuming the offset mapping.
2. Find allocation/initialization or serialized-default provenance for the manager pointer at `pawn+0x59C`; search by the manager's observed structure (`+0x38/+0x3C/+0x40/+0xE0`) and callers rather than displacement alone.
3. Search for a non-null writer to the first DWORD of the 0x0C manager entries, keeping it distinct from the separate 0x30-stride `FUN_00C0CA70` array.
4. Identify the receiver vptr for `FUN_00C04BD0` selections and the actual operation semantics of Pawn vtable slot `+0x5C8`.
5. Continue owner/consumer analysis for the keyed registry in EXP-0036 separately.
6. Resume Blink joining only if a concrete route reaches the `DisItemContext_UsePower` vtable with a stack-compatible call/thunk and the actual Blink component receiver.
