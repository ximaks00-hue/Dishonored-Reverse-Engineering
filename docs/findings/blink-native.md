# Blink native-path findings

Build 10256413. Keep wheel item `24`, UI enum `2`, active-array index `0`, and `_iPower` distinct until a proven conversion. Narrative summary: [Blink overview](../gameplay/blink/overview.md). Edges: [activation graph](../gameplay/blink/activation-graph.md).

## Confirmed package facts

- Blink component class/defaults, tweak levels, `CastBlink` use-action flags (`EXP-0009`, `EXP-0015`, `EXP-0025`).
- Player default graph: `PowerBlink` → `m_pBlinkPower` and `m_ActivePowers[0]` (`EXP-0015`).
- Scaleform PowerWheel: item ID `24` → external `onSelectionChanged` (`EXP-0019`).

## Confirmed native edges

| Edge | Result | EXP |
| --- | --- | --- |
| PowerWheel `OnSelectionChanged` → vtable `0x01161C08` `+0x1F0` → `FUN_00BCD800` | UI refresh / item-info; maps ID 24 → handler code 2 | 0021 |
| `Dis_SelectPower` → Controller `+0x560` → `FUN_00AB4680` | Bounds-check usable mapping; pawn selection slots | 0021 |
| Selection → pawn `+0x6E8/+0x6E4` → `FUN_00B56060` → `FUN_00B51790` | Component selection/state update, not activation | 0021, 0027 |
| Blink tweak getter via interface `+0x54` slot `+0x10` | Reads level/tweak fields; DarkVision null fallback | 0022, 0023 |
| UsePower context `+0x134` (`FUN_00C44D30`) → Blink `+0x174` → `+0x1AC` | Static bridge context → Blink move-mode | 0028 |
| UsePower context `+0x184` (`FUN_00C4B800`) → context-held component `+0x168`; Blink/Transversal `+0x168` → `FUN_00BFC020` → guarded `FUN_00BFAAA0` → component `+0x1AC` | Second conditional static bridge toward Blink move-mode; actual component vptr and event caller unknown | 0048 |
| Blink vtable `+0x340` → `+0x1AC` (`FUN_00BFC990`) | Internal route to move-mode setter | 0027 |
| Blink vtable `+0x1B0` (`FUN_00BFA270`) → `FUN_00BF5520` → same-receiver `+0x60/+0x64/+0x68`; consumed by `+0x1AC` | Stored-target producer/consumer same-instance field bridge; call scheduling/input still unknown | 0043, 0030 |
| Blink vtable `+0x13C` (`FUN_00BFC5D0`) in mode `0` → virtual `+0x1B0` on same receiver | Warmup update dispatches the target updater; Transversal's override forwards to the Blink base updater. Engine invocation of `+0x13C` is inferred from `TickGroup`, not directly observed | 0045 |
| Direct callers of `FUN_00BFA270` | Only `FUN_00CF3540` is an ordinary direct caller in the persisted graph; base Blink calls it through vtable `+0x1B0` from its Warmup update path. Engine-side indirect entry remains unknown | 0045 follow-up |
| Corrected `+0x13C` load-call scan | Full sweep finds 79 generic patterns (four unmapped in function index); one mapped candidate is in record parser `FUN_004052F0`; two more audits found generic dispatch paths without a Blink receiver/input join | 0046, 0051 |
| UsePower `+0x134` caller audit | Target appears at UsePower vtable entry `0x01183754`; no direct caller identified. Examined `FUN_00A96B50 → FUN_00C44E30` route is gated on DevouringSwarm | 0047 |
| `FUN_00C0CA70` receiver ABI | Calls returned `entry+0x1E0` object through `+0x184` (two args) then `+0x134` (three args); known UsePower targets both `RET 4`. Extra x86 arguments may be ignored and caller resets ESP from EBP, so this is an unresolved signature discrepancy, not an exclusion | 0049 |
| Transversal vtable `0x011BD0A8`, descriptor-associated class `DisDLC06ActivePowerComponent_Transversal` | Package says it extends Blink but has distinct `Transversal` UI selection; overrides `+0x1AC/+0x1B0` forward same `this` to Blink base `FUN_00BFC990/FUN_00BFA270` | 0044 |
| Blink move-mode path → candidate/trace → `FUN_006539C0` | Conditional pawn position write at `+0xC4/+0xC8/+0xCC` | 0024, 0030 |

## Rejected / deprioritized for Blink activation

| Candidate | Why | EXP |
| --- | --- | --- |
| PlayerPawn manager `+0x59C` as UsePower/Blink | Stack ABI incompatible with known UsePower targets (manager path itself is real) | 0035, 0037 |
| Shortcut `Use` → `FUN_00AB7D30` as direct activator | Updates shortcut/Scaleform state only | 0026, 0027 |
| `ArkCpntType_Lookat` as Blink teleport | Owned look-at method table; no relocation edge | 0014, 0018 |

## Open / weakened (not rejected)

| Candidate | Why | EXP |
| --- | --- | --- |
| `FUN_00C0CA70` as proven user-Use→UsePower dispatcher | Receiver class unproved; argument-count discrepancy with known targets needs vtable/semantic confirmation but does not reject the join; general dispatcher remains open | 0029, 0032, 0049 |
| Keyed registry `FUN_00B36CA0` → Blink | Shared helper; keys 3/9 unjoined to Use/Blink | 0031, 0036 |
| Input/event → UsePower `+0x134` or Blink `+0x340` | Confirmed bridges lack proven callers | 0028–0040 |
| `FUN_00BFAE60/FUN_00BFAFD0` → `FUN_00BF8C00` as Blink stored-target producer | **Rejected as Blink same-instance join:** Swarm vtable/`IsA(DevouringSwarm)` own this separate producer; offset overlap with Blink `FUN_00BFC990` is not a cross-instance bridge | 0042 (supersedes 0039 Blink-owner inference) |

## Still open

- Engine callsite that invokes Blink `+0x13C`; separately, event/caller that enters UsePower `+0x134/+0x184`, Blink `+0x340`, or changes the mode from Warmup to Move from player input. EXP-0048's second static route has no proven event caller or runtime receiver class.
- Runtime receiver vptr on candidate dispatchers; clean attach (`EXP-0016`).
- Writer/schema for `pawn+0x59C` / `+0xD4/+0xD8/+0xE0` (separate from Blink join).
