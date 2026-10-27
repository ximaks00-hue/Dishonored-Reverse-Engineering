# Blink activation evidence graph

Build `10256413`. Edges are labeled by evidence status. Do not merge parallel graphs until a concrete join exists.

```mermaid
flowchart TB
  subgraph indices["Keep distinct until proven conversion"]
    W24["PowerWheel item 24"]
    U2["UI enum Blink = 2"]
    A0["ActivePowers index 0"]
    IP["_iPower / usable mapping"]
  end

  subgraph ui["UI / selection"]
    SF["Scaleform onSelectionChanged"] --> PW["PowerWheel +0x1F0 FUN_00BCD800"]
    PW -->|"confirmed: UI refresh only"| UIINFO["UpdateItemInfos"]
    DSP["Dis_SelectPower FUN_00AB4680"] --> SEL["Pawn +0x6E8/+0x6E4"]
    SEL -->|"confirmed: selection state"| SM["FUN_00B51790 state manager"]
    SCUT["Controller shortcut Use/Select"] -->|"confirmed: shortcut UI state"| SCSTATE["FUN_00AB7D30"]
  end

  subgraph usepower["UsePower → Blink move mode"]
    TWEAK["DisTweaks_UsePower / CastBlink"] -.->|"package config only"| CTX["DisItemContext_UsePower"]
    CTX -->|"confirmed static"| C134["+0x134 FUN_00C44D30"]
    C134 -->|"confirmed when Blink recv"| B174["Blink +0x174 FUN_00BE7580"]
    B174 -->|"confirmed"| B1AC["Blink +0x1AC FUN_00BFC990"]
    CTX -->|"+0x184 vtable entry"| C184["FUN_00C4B800"]
    C184 -->|"conditional: FUN_BE8C50 != 0 and FUN_B49020 == 0"| CP168["context-held component +0x168"]
    CP168 -->|"if Blink or Transversal vptr"| B168["FUN_00BFC020"]
    B168 -->|"component guards pass"| RESET["FUN_00BFAAA0 clears mode byte +0xC9"]
    RESET -->|"config float +0x1C <= 0"| B1AC
    B340["Blink +0x340 FUN_00BE89E0"] -->|"confirmed internal"| B1AC
    BTICK["Blink +0x13C FUN_00BFC5D0"] -->|"mode 0 / Warmup: same-receiver virtual dispatch +0x1B0"| BWR
    CAND["FUN_00BFAE60/BFAFD0 → FUN_00BF8C00\n+0x60 write"] -.->|"rejected as Blink instance\n(EXP-0042: DevouringSwarm)"| B1AC
    BWR["Blink +0x1B0 FUN_00BFA270 → FUN_00BF5520"] -->|"confirmed: same receiver fields +0x60/+0x64/+0x68"| B1AC
    B1AC -->|"confirmed conditional"| MOVE["EBM_BlinkMove / mode 1"]
    MOVE -->|"confirmed gated"| POS["Pawn pos +0xC4/+0xC8/+0xCC"]
  end

  subgraph transversal["DLC06 Transversal subclass (separate UI selection)"]
    TRV["DisDLC06ActivePowerComponent_Transversal\nextends Blink; UI selection Transversal"]
    TVT["vtable 0x011BD0A8"]
    TRV --> TVT
    B174 -->|"inherited +0x174; if Transversal receiver"| CF34
    TVT -->|"+0x1AC wrapper; same this"| B1AC
    TVT -->|"+0x1B0 wrapper; same this"| BWR
  end

  subgraph open_callers["Open: who calls into activation"]
    INPUT["Player Use / anim / event"] -.->|"unknown"| C134
    INPUT -.->|"unknown; no proven caller of UsePower +0x184"| C184
    INPUT -.->|"unknown"| B340
    CF3540["FUN_00CF3540 (Transversal +0x1B0; entry 0x011BD258)"] -->|"confirmed wrapper; same this"| BWR
    BTICK -.->|"engine invocation inferred from TickGroup; callsite unknown"| OPEN1
    CF34["FUN_00CF34E0 (Transversal +0x1AC; entry 0x011BD254)"] -->|"confirmed tail-call; same this"| B1AC
    CF34 -.->|"runtime scheduler unknown"| OPEN1["Transversal vtable owner confirmed; scheduler unknown"]
    C0CA["FUN_00C0CA70 0x30 array"] -.->|"open/weakened: receiver unproved"| C134
    C0CA -.->|"open/weakened: arg-count difference needs receiver/signature proof; extra args may be ignored (EXP-0049)"| C184
    REG["FUN_00B36CA0 keyed registry"] -.->|"open: no Use/Blink join"| OPEN2["keys 3 / 9 only"]
  end

  subgraph rejected["Rejected as Blink/UsePower activation"]
    PPM["PlayerPawn manager +0x59C"] -->|"ABI reject vs known UsePower targets"| C04["FUN_00C04C30"]
    LOOK["ArkCpntType_Lookat"] -.->|"no relocate edge"| OPEN3["NPC look-at context"]
  end

  W24 --> SF
  U2 -.->|"candidate only"| DSP
  A0 -.->|"default slot only"| SEL
  IP --> DSP
  SCSTATE -.->|"no direct edge"| DSP
  SM -.->|"no activation edge"| CTX
```

## Edge checklist

| ID | Edge | Status | Primary EXP |
| --- | --- | --- | --- |
| E1 | Scaleform focus → `OnSelectionChanged` int | confirmed correlation | 0019 |
| E2 | PowerWheel `+0x1F0` → item-info refresh | confirmed | 0021 |
| E3 | `Dis_SelectPower` → selection/state manager | confirmed | 0021, 0027 |
| E4 | Shortcut Use → activation | open (no static edge) | 0026, 0027 |
| E5 | UsePower `+0x134` → Blink `+0x1AC` | confirmed static | 0028 |
| E5a | UsePower `+0x184` → context-held component `+0x168` | confirmed static conditional; dynamic component class at runtime unknown | 0048 |
| E5b | Blink/Transversal `+0x168` → `FUN_00BFC020` → guarded `FUN_00BFAAA0` → component `+0x1AC` → conditional Blink move-mode entry | confirmed static conditional; success/runtime occurrence unknown | 0044, 0048 |
| E6 | Blink move mode → position write | confirmed gated | 0024, 0030 |
| E6a | Blink base `+0x1B0` target writer → fields consumed by Blink base `+0x1AC` | confirmed same receiver fields; Transversal subclass wraps both with same `this` | 0043, 0030, 0044 |
| E6b | Blink update `+0x13C` in Warmup → virtual `+0x1B0` target refresh | confirmed static same-receiver dispatch; engine tick callsite unknown (generic slot candidates remain unresolved; two audited without a Blink join) | 0045, 0046, 0051 |
| E7 | Input/event → UsePower `+0x134/+0x184` or Blink `+0x340` | open; dynamic caller of both UsePower methods not identified; +0x13C candidate audit adds no Blink/input edge | 0028–0040, 0042, 0047–0049, 0051 |
| E8 | `FUN_00C0CA70` → UsePower instance | open / weakened; argument counts differ from known target signatures, but extra arguments may be ignored; dynamic receiver class remains unknown | 0029, 0032, 0049 |
| E9 | Pawn manager → known UsePower targets | rejected (ABI); manager path itself is real | 0035, 0037 |
| E10 | Keyed registry → Blink | open / unjoined | 0031, 0036 |

## Next discriminating checks

1. The target writer/consumer join and Blink Warmup `+0x13C` → virtual `+0x1B0` dispatch are confirmed (EXP-0043/0045); package `TickGroup` supports, but does not prove, an engine tick interpretation. Corrected EXP-0046 finds 79 generic `+0x13C` load-call patterns; EXP-0051 traces two candidates to generic dispatch paths without establishing Blink receivers. Find a scheduler call through dataflow that proves the receiver's class/vptr. EXP-0048 adds a conditional static UsePower `+0x184` → component `+0x168` route; EXP-0049 records an argument-count discrepancy at `FUN_00C0CA70`, but extra arguments may be ignored, so the receiver identity remains open. Trace tick registration, context creation, and the actual caller of `+0x184` independently; do not join them based on nearby code or shared offsets.
2. Runtime vptr at UsePower/Blink call sites after a clean process attach (`EXP-0016`).
3. Do not prioritize E9 as Blink activation until a stack-compatible receiver appears; keep E8 on a separate open graph.
4. Keep Swarm producer graph (`FUN_00C44E30` → `FUN_00BFAFD0`) out of Blink activation unless a new join appears.
