# REV-0006 — Blink move-mode and pawn-position write audit

Date: 2026-10-26. **Basis: user-provided progress text, not primary binary/decompiler logs.** No access in this turn to local EXP-0022–0024, Ghidra project, executable bytes, or UELib output. Distinguish reported static observation from independent confirmation.

## New static path reported

```text
FUN_00BFC990 -- sets mode=1 (matched to package EBM_BlinkMove)
    [caller and transition unknown]
FUN_00BFC5D0 -> FUN_00BFC160 -> FUN_00BECDF0 -> FUN_006539C0
                                              writes supplied vector to owner pawn +0xC4/+0xC8/+0xCC
```

The reported call path is a **major advance**, but do not claim full input-to-cast execution: we have neither the upstream event calling FUN_00BFC990 nor validated runtime evidence that these fields are the pawn's authoritative Location and that the path executes under the required conditions. The user reports a position write; exact disassembly, pointer provenance, and before/after state remain prerequisites for independently established semantics.

## Tweak retrieval path (reported)

- Blink constructor installs an interface table at component `this+0x54`.
- Its `+0x10` slot reaches `FUN_00A446B0`, which reads a pointer at component `+0x8C`; `+0x88` is read as a level index.
- UELib/defaults relate Blink `m_pPowerTweaks` to `Twk_Powers.Blink.Twk_Blink`. Mapping native fields `+0x88/+0x8C` to named `m_CurrentLevel/m_pPowerTweaks` is **strongly inferred**, not independently verified class-layout evidence.
- `FUN_00BF9AB0` and `FUN_00AA5700` call a getter `+0x10` on a nested object at `this+0x54`; when non-null, they use its result. Null fallback fetches class default object through global `DAT_0146F26C`, initializer `FUN_00BF3030` and `FUN_00497130`. The fallback descriptor reportedly names `DisTweaks_DarkVision`: **do not label this fallback as Blink tweaks**.
- `FUN_00BFBC90` copies data from helper output into another object. Its destination semantics are not established.
- The native record stride is `0x38` (56 bytes), whereas the reported serialized `PowerAttributes_Blink` has 19 four-byte fields = `0x4C` (76 bytes). These layouts do NOT match directly. Distinct type or transformation remains possible.

## Correct research status

1. **Known by report:** class-specific candidate methods, getter and fallback, move-mode path to a function writing three vector components into Pawn-relative memory.
2. **Not known:** calling event for `FUN_00BFC990`, input-use dispatch path, runtime branch conditions, authoritative meaning of Pawn `+0xC4/+0xC8/+0xCC`, `0x38` layout, exact native tweak field layout.
3. **Do not merge concepts:** controller `Dis_SelectPower` selects a power; PowerWheel `OnSelectionChanged` updates UI; neither alone proves activation/cast. A mode transition and actual position update require separate observations.
4. **Prior research correction:** `DisTweaks_DarkVision` fallback undermines earlier assumption that every `0x38` data read is Blink settings. Keep rejected interpretation in history rather than silently replacing it.
5. Exact executable SHA `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` is reported rechecked by user; not independently recalculated here.

## Most discriminating next checks

- Xrefs and callback/virtual callers of `FUN_00BFC990` including indirect calls and tables; find who sets EBM_BlinkMove and why.
- Recover actual argument/register flow from `FUN_00BECDF0` into `FUN_006539C0`; check pointer chain to owner Pawn, branch conditions and whether writes are location, cached position, or something else.
- For target vector, back-slice each component through collision/trace outputs and `0x38` record reads, documenting any intervening clamping, offsets or substitutions.
- Derive exact `0x38` record fields and distinguish them from `0x4C` package struct. Track array allocation/count/stride, source getter, and optional conversion from package attributes.
- Confirm getter owner/interface layout and `+0x88/+0x8C` property identities with independent layout evidence.
- Preserve no-execution boundary if untrusted `dinput8.dll` remains in workspace.

## Exit criteria for full Blink relocation

Exact input/cast event -> mode transition -> trace/target result -> call site -> Pawn pointer -> verified Location mutation, on same SHA-anchored build. Until then **partial static movement-path reconstruction**, not end-to-end Blink.
