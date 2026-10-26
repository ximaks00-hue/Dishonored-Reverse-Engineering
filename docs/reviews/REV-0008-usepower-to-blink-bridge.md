# REV-0008 — UsePower-to-Blink virtual dispatch bridge

Date: 2026-10-26. Evidence source: user-provided EXP-0027/EXP-0028 progress narrative, not original Ghidra disassembly. **Binary-level claims are reported, not independently reproduced.**

## New reported bridge

- `DisItemContext_UsePower` slot `+0x134` resolves to `FUN_00C44D30`.
- Within this method, flag/state guards conditionally dispatch the current component's virtual slot `+0x174`.
- With a Blink receiver, component slot `+0x174` resolves to `FUN_00BE7580`, which invokes Blink slot `+0x1AC` → `FUN_00BFC990`.
- `FUN_00BFC990` writes mode byte `1` on a successful path; package enum supports `EBM_BlinkMove = 1`.
- Previously reported move-mode path `FUN_00BFC5D0 → FUN_00BFC160 → FUN_00BECDF0 → FUN_006539C0` conditionally writes pawn-relative vector components at `+0xC4/+0xC8/+0xCC`.

**What is not proven:** which input event or dispatcher invokes UsePower vtable `+0x134`, whether the runtime component at this callsite is Blink in a particular state, whether all guards pass, and execution of the position update in a controlled run. No unbroken runtime use-to-relocation trace.

## Earlier findings retained, not conflated

- Controller `Dis_SelectPower` maps `_iPower` through usable-power indices to a selected component; `FUN_00C4BA70` reads component byte `+0x74` and Controller stores current/prior values at `+0x632/+0x631`. Identification with reflected `m_eUISelection` remains inferred.
- Keyboard and gamepad shortcut Use targets `FUN_00AA0950` and `FUN_00AA0860` update index/mask, and `FUN_00AB7D30` updates shortcut arrays/Scaleform. Decompiled `OpenShortcuts`, `SetShortcutSelection`, wheel and dock-bar ActionScript do not show cast callback in examined bodies. All negative results are scoped.
- Separate reported Blink-vtable `+0x340 → FUN_00BE89E0` conditionally routes through slots `+0x18C/+0x178/+0x1AC` to mode setter. Its indirect caller `FUN_00652CF0` loads slot at `0x00653223` and invokes at `0x0065322B`; receiver class not established.
- Unknown table `0x011C55A0` shares 17 consecutive pointers starting at `+0x340` with Blink; not enough to identify class owner. DarkVision target differs.
- `FUN_00CAED80/FUN_00BE8A50` belongs to DarkVision, not established as Blink cast.
- `FUN_00CF34E0 → FUN_00CF3360 → FUN_00BFC990` exists as a distinct reported static path with upstream caller unknown. `0x011BD230` remains unattributed, no direct absolute references detected in prior pass.
- An unrelated generic helper `FUN_00BF30C0` and `FUN_00CF64B0`/table `0x011CD1D8` have no established UsePower ownership.
- Controller byte `+0x238` concerns shortcut selection; no direct method path to Blink in the inspected `FUN_00AB7D30` call graph.

## Priority now

**EXP-0029:** recover native owner/constructor/vtable and actual dispatch caller of `DisItemContext_UsePower +0x134`. Verify the runtime component pointer to Blink at `+0x174`, guard conditions, and link `FUN_00BFC990` to the already known conditional pawn position-write path. Preserve both direct and indirect-call edges and missing links explicitly.

Avoid overriding primary local EXP-0027 or EXP-0028: original files at user's Windows E: drive aren't exposed to the connected GitHub tools in this session.
