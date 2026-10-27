# Blink

Build `10256413`. Durable edge list: [activation-graph.md](activation-graph.md). Condensed native findings: [blink-native.md](../../findings/blink-native.md). Detailed procedures remain in `experiments/EXP-*`.

Keep these integers distinct until a proven conversion: PowerWheel item `24`, UI enum `2`, active-array index `0`, controller `_iPower`.

## Confirmed (package)

- Package contains Blink mode/tweak/component types and `PowerBlink` / `Twk_Blink` entries ([EXP-0004](../../../experiments/EXP-0004-umodel-blink-triage.md), [EXP-0009](../../../experiments/EXP-0009-blink-decompression-and-uelib.md)).
- Player default graph: `PowerBlink` → `m_pBlinkPower` and `m_ActivePowers[0]` ([EXP-0015](../../../experiments/EXP-0015-player-power-default-graph.md)).
- Blink use tweak configures animation state `CastBlink` with move/look/self-interrupt flags ([EXP-0025](../../../experiments/EXP-0025-use-power-package-boundary.md)).
- Scaleform PowerWheel: item ID `24` → external `onSelectionChanged` ([EXP-0019](../../../experiments/EXP-0019-powerwheel-scaleform-selection-bridge.md)).
- Class is `native(Power)`; no Blink component UnrealScript body was recovered. Compressed UPK blocks object-table decompile; use the decompressed analysis copy ([EXP-0007](../../../experiments/EXP-0007-ue-explorer-mcp.md), [EXP-0009](../../../experiments/EXP-0009-blink-decompression-and-uelib.md)).

## Confirmed (native)

- PowerWheel `OnSelectionChanged` → vtable `+0x1F0` → `FUN_00BCD800`: UI item-info refresh; maps item `24` → handler code `2` (not activation) ([EXP-0021](../../../experiments/EXP-0021-exact-class-vtables-power-selection.md)).
- `Dis_SelectPower` → Controller `+0x560` → `FUN_00AB4680` → pawn selection/`FUN_00B51790`: selection/state update, not activation ([EXP-0021](../../../experiments/EXP-0021-exact-class-vtables-power-selection.md), [EXP-0027](../../../experiments/EXP-0027-use-power-dispatch.md)).
- Shortcut Use/Select wrappers update shortcut/Scaleform state via `FUN_00AB7D30`; no static edge to activation ([EXP-0026](../../../experiments/EXP-0026-shortcut-index-consumer-audit.md), [EXP-0027](../../../experiments/EXP-0027-use-power-dispatch.md)).
- Blink tweak data is consumed through an interface getter (level/tweak fields; DarkVision null fallback) ([EXP-0022](../../../experiments/EXP-0022-controller-shortcut-state-and-index-audit.md), [EXP-0023](../../../experiments/EXP-0023-blink-tweak-interface-dataflow.md)).
- **Static activation bridge:** `DisItemContext_UsePower` slot `+0x134` (`FUN_00C44D30`) → Blink `+0x174` (`FUN_00BE7580`) → Blink `+0x1AC` (`FUN_00BFC990`) → move mode on the successful branch ([EXP-0028](../../../experiments/EXP-0028-item-context-inheritance.md)).
- **Second conditional static route:** UsePower slot `+0x184` (`FUN_00C4B800`) obtains the context-held component at `context+0x3C → +0x114` and conditionally calls component slot `+0x168`. For the known Blink and Transversal vtables this reaches `FUN_00BFC020`, whose guards can reach `FUN_00BFAAA0`; when its config branch permits, the component's `+0x1AC` dispatch reaches Blink `FUN_00BFC990` (directly for Blink, through the same-receiver Transversal wrapper otherwise). This does not identify the input caller, prove the runtime component type, or guarantee move-mode success ([EXP-0048](../../../experiments/EXP-0048-usepower-component-slot168.md)).
- Separate internal Blink route: slot `+0x340` → `+0x1AC` ([EXP-0027](../../../experiments/EXP-0027-use-power-dispatch.md)). Do not merge with the UsePower bridge until a shared caller is shown.
- Move-mode processing can reach a gated pawn position write at `+0xC4/+0xC8/+0xCC` ([EXP-0024](../../../experiments/EXP-0024-blink-position-write-path.md), [EXP-0030](../../../experiments/EXP-0030-blink-move-transition-conditions.md)).
- Blink update slot `+0x13C` (`FUN_00BFC5D0`) dispatches virtual `+0x1B0` on the same receiver in mode `EBM_BlinkWarmup`; that reaches the target writer. The package sets Blink `TickGroup=TG_PreAsyncWork`, but the engine callsite and input-driven mode transition remain unknown ([EXP-0045](../../../experiments/EXP-0045-blink-update-slot-dispatch.md)).
- The follow-up direct-call index lists only Transversal wrapper `FUN_00CF3540` as a direct caller of `FUN_00BFA270`; base Blink enters that function through vtable `+0x1B0`. This narrows direct-call provenance without identifying the engine's indirect tick dispatch or linking it to input ([EXP-0045](../../../experiments/EXP-0045-blink-update-slot-dispatch.md)).
- The corrected executable scan finds 79 generic `+0x13C` load-call patterns; no Blink receiver/target has been proven. One mapped candidate is inside record parser `FUN_004052F0`; two more were traced to generic dispatch paths with no Blink/input join ([EXP-0046](../../../experiments/EXP-0046-blink-tick-dispatch-search.md), [EXP-0051](../../../experiments/EXP-0051-slot13c-candidate-context-audit.md)).
- The callgraph contains no direct code caller for UsePower `+0x134`; the examined `FUN_00A96B50 → FUN_00C44E30` branch requires a DevouringSwarm component and remains separate from Blink. The actual dynamic UsePower caller is still unknown ([EXP-0047](../../../experiments/EXP-0047-usepower-input-entry-audit.md)).
- The record dispatcher `FUN_00C0CA70` calls methods at `+0x184/+0x134` with more stack arguments than the known UsePower targets consume. Extra arguments may be ignored, so this discrepancy does not identify or reject the receiver; keep the route open pending vptr or semantic evidence ([EXP-0049](../../../experiments/EXP-0049-context-dispatch-abi-audit.md)).
- `DisDLC06ActivePowerComponent_Transversal` is declared as a Blink subclass with a distinct `Transversal` UI selection. Its descriptor-associated vtable `0x011BD0A8` overrides `+0x1AC/+0x1B0`; those wrappers pass the same receiver to Blink base `FUN_00BFC990/FUN_00BFA270`. This explains the methods' owner and forwarding path, but not the runtime scheduler or the base Blink input path ([EXP-0044](../../../experiments/EXP-0044-transversal-vtable-and-blink-base-calls.md)).

## Inferred (needs discriminating check)

- `component+0x74` ↔ package `m_eUISelection` (Blink default enum `2`) — strong layout candidate, no UELib native offset ([EXP-0027](../../../experiments/EXP-0027-use-power-dispatch.md)).
- Interpreting tweak level rows as upgrade tiers — data-shape inference only ([EXP-0009](../../../experiments/EXP-0009-blink-decompression-and-uelib.md)).

## Rejected / deprioritized as Blink activation

- PlayerPawn manager at `+0x59C` / `FUN_00C04C30`: real path on the pawn, but stack ABI incompatible with known UsePower targets ([EXP-0035](../../../experiments/EXP-0035-playerpawn-context-manager-provenance.md), [EXP-0037](../../../experiments/EXP-0037-pawn-manager-provenance-and-abi.md)).
- `FUN_00C0CA70` as a *proven* user-Use→UsePower dispatcher: open/weakened (receiver class unproved; callers are state/timer/audio-adjacent) ([EXP-0029](../../../experiments/EXP-0029-usepower-runtime-dispatch.md), [EXP-0032](../../../experiments/EXP-0032-dispatch-record-provenance.md)).
- `ArkCpntType_Lookat` as Blink teleport ([EXP-0014](../../../experiments/EXP-0014-native-owner-triage.md), [EXP-0018](../../../experiments/EXP-0018-npc-lookat-property-correlation.md)).

## Still open

- What engine scheduler invokes Blink `+0x13C`, and what event/input enters UsePower `+0x134/+0x184` or Blink `+0x340`, or changes mode from Warmup to Move (E7 on the activation graph).
- Runtime receiver vptrs for candidate dispatchers; clean process attach ([EXP-0016](../../../experiments/EXP-0016-runtime-mcp-executable-binding.md)).
- Whether `CastBlink` animation or controller Use actually drives the confirmed UsePower bridge.
- Conversion among wheel `24`, UI `2`, active index `0`, and `_iPower`.

## Related records

- [activation-graph.md](activation-graph.md)
- [blink-native.md](../../findings/blink-native.md)
- [BUILD-STEAM-10256413](../../../research/builds/BUILD-STEAM-10256413/build.md)
- [package archaeology](../../../research/packages/README.md)
