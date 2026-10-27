# REV-0007 — UsePower boundary and negative xref review

Date: 2026-10-26. Source: user-provided reports after REV-0006. **No direct Ghidra, game binary, or local EXP-0025/0026 file access** in this GitHub session. All native findings are report-derived.

## New positive findings (reported)

1. Package metadata contains `DisItemContext_UsePower` and a Blink setup animation `CastBlink`. These support a plausible activation context but do not establish a specific input handler or callback.
2. A separate native path `FUN_00CF34E0 → FUN_00CF3360 → FUN_00BFC990` reaches the mode-setting method. The caller/event that enters `FUN_00CF34E0` is unknown.
3. Earlier path `FUN_00BFC5D0 → FUN_00BFC160 → FUN_00BECDF0 → FUN_006539C0` conditionally writes a vector into Pawn-relative `+0xC4/+0xC8/+0xCC`. Those writes occur only if helper guards pass. Runtime proof of authoritative player Location remains a separate gate.
4. Shortcut state at controller `+0x238` is read/updated by functions moving among occupied shortcut slots; `FUN_00AB7D30` drives state/UI updates, without a reported **direct** call to `Dis_SelectPower` or Blink move mode. Semantics of shortcut stored byte `+0x228` remain to be established.

## Negative evidence and corrections

- An earlier suggestion that nearby `0x011BD230` is an active indirect dispatch/callback table is weakened: no direct code call xrefs to `FUN_00CF34E0` and no absolute xrefs to table addresses were found in the specified search. **Do not call the table identified**. Absence of literal/absolute references does not rule out relative table offsets, computed pointers, relocation or indirect references; inspect raw table bytes and dataflow separately.
- Direct call-graph absence under `FUN_00AB7D30` is limited to recovered **direct edges in inspected code**, not a whole-program absence of invocation via CALLIND, callbacks or game event scheduling.
- `DisItemContext_UsePower` and `CastBlink` are identifiers/metadata; exact code edge to `FUN_00CF34E0` is **not established**.
- Maintain separate UI-only selection path (`FUN_00BCD800`), controller selected-power data path (`FUN_00AB4680`), and native move-mode/position paths.
- `PowerAttributes_Blink` package structure reports 19 four-byte fields (`0x4C`); native stride `0x38` remains unequal. DarkVision default fallback in `FUN_00BF9AB0` must not be misidentified as Blink tweak defaults.

## Next discriminating experiment

**EXP-0027**: identify exact callers/indirect references to `FUN_00CF34E0`, evaluate the concrete contents of candidate `0x011BD230`, resolve object ownership of the native UsePower context, and trace input/cast dispatch to mode transition. Include a specific test for relative offset-based references, but do not invent them. In parallel inspect controller slot-selection byte `+0x228` / index `+0x238` to determine whether those are UI-only or consumed by a real cast handler.

## Source identity

Exact x86 EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` is previously reported rechecked by user, not independently rehashed in this session. Don't run untrusted local DLLs. No game files modified here.

## Provenance limitation

The existing GitHub EXP-0025 is an earlier experimental **plan** named `EXP-0025-blink-cast-and-position-proof.md`, whereas the user's new local report cites another `EXP-0025-use-power-package-boundary.md`. Both are distinct documents sharing an ID. Keep both paths and avoid falsely treating the earlier plan as the new primary report; reconcile after original local files are available. The repo also contains earlier planned EXP-0023/0024 files under different names.