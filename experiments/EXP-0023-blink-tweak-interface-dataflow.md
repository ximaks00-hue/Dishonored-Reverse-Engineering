---
id: EXP-0023
title: "Blink tweak interface and per-level dataflow"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "How does native code read Blink tweak/level data through the component interface?"
---
# EXP-0023 — Blink tweak interface and per-level dataflow

- Status: the interface getter and its component-field source are resolved; the consumer strongly maps to the Blink tweak object and per-level data, but the native record layout does not match the complete serialized `PowerAttributes_Blink` declaration. Blink activation and relocation remain open.
- Date: 2026-10-26.
- Executable: workspace `Dishonored.exe`, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Ghidra project: `dishonored_exact_full`, x86, image base `0x00400000`; queries were read-only.
- Package: decompressed analysis copy of `DishonoredGame.upk`, SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`; UELib 1.13.3 output in `.tmp/ue-readonly-dump/EXP-0009-recheck.log`, `.tmp/ue-readonly-dump/EXP-0015-class-path-recheck.log`, and the targeted interface/class reflection pass `.tmp/ue-readonly-dump/EXP-0023-tweak-interface-recheck.log`.
- Scope: static inspection only. No game files or Ghidra program data were changed. `_excluded_coop_project/` was not accessed.

## Question

Does the Blink update path obtain its per-level data from the component's tweak interface, and can that source be joined to the package's `DisTweaks_Blink` object?

## Native interface resolution

The class descriptor for `DishonoredActivePowerComponent_Blink` is at `0x0135A7A8`; its UTF-16 class name is at `0x01165762`, and its constructor pointer is `FUN_00BF9A10`.

`FUN_00BF9A10` sets the primary vptr to `0x01168698` and the interface vptr at object offset `+0x54` to `0x0116867C`. The DWORD at interface-table slot `+0x10` (`0x0116868C`) is `0x00A446B0`. `FUN_00A446B0` returns the DWORD stored at `ECX+0x38`.

Both relevant callers pass `ECX = component + 0x54`. Therefore the ordinary getter result is the DWORD stored at `component + 0x8C`. `FUN_00BF9AB0` invokes this interface slot directly. `FUN_00BFBC90` calls helper `FUN_00AA5700`, which invokes the same `+0x10` interface slot and returns its result in EAX. Although Ghidra's current signature for that helper is `void`, the call site consumes EAX as the returned object pointer and the machine instructions preserve the getter/default-object result.

## Package-side join

The package declaration says `DishonoredActivePowerComponent` implements `DisTweaksInterface` and declares the adjacent base properties `m_CurrentLevel` and `m_pPowerTweaks`, in that order. The Blink default component sets `m_pPowerTweaks` to `DisTweaks_Blink'Twk_Powers.Blink.Twk_Blink'`. `DishonoredActivePowerComponent_Blink` additionally declares a separate native pointer named `m_pPowerAttributes`.

In the native consumer, `FUN_00BF9AB0` reads `component + 0x88`, subtracts one, and uses that as the level index. The getter at `component + 0x8C` immediately follows. This offset pairing matches the package order `m_CurrentLevel` then `m_pPowerTweaks`, so `+0x88` → `m_CurrentLevel` and `+0x8C` → `m_pPowerTweaks` are strong field-identity inferences. The parser does not expose native UProperty offsets, so retain the distinction between observed offsets and the inferred field-name join.

When the getter returns nonzero, `FUN_00BF9AB0` reads the selected data from `returned_object + 0x160 + (currentLevel-1)*0x38`. It uses the first DWORD as a distance and the DWORD at `+8` as a second distance/vertical term, and also reads record-relative values at `+0x14`, `+0x18`, and `+0x1C`. These offsets align with the beginning of the declared `PowerAttributes_Blink` field sequence (`m_Distance`, `m_HorizDistance`, `m_VertDistance`, then the time fields). The same data contributes to spatial candidate queries and distance comparisons in this function.

If the interface getter returns zero, `FUN_00BF9AB0` initializes global `DAT_0146F26C` from descriptor `0x01359D48`, whose class name is `DisTweaks_DarkVision`, then obtains that class's default object through `FUN_00497130`. The DarkVision class is therefore only the null-pointer fallback; it does not replace the ordinary component-supplied pointer path.

## Record-size discrepancy

The package declaration of `PowerAttributes_Blink` contains 15 floats, one 32-bit integer, and three object references: 19 DWORD fields, or `0x4C` bytes under the x86 representation. The native array access uses `0x38` (`14` DWORDs) as its stride. Thus the object pointer and initial field offsets strongly link the read to the component's tweak data, but the complete serialized struct cannot be laid over the native record byte-for-byte under this simple layout. Possible explanations include a native projection/cache, a distinct compiled record, a version/layout difference, or an incorrect start/stride join; none is established by this experiment.

## Claim classification

**Confirmed by binary evidence:** Blink constructor installs the `IDisTweaksInterface` vptr at `+0x54`; its `+0x10` method is `FUN_00A446B0`; that getter reads `[this+0x8C]`; `FUN_00BF9AB0` indexes the returned object using a current-level-like value from `+0x88`; the null branch uses `DisTweaks_DarkVision`; Blink's package default references `Twk_Powers.Blink.Twk_Blink` through `m_pPowerTweaks`.

**Strong inference:** object field `+0x88` is `m_CurrentLevel`, `+0x8C` is `m_pPowerTweaks`, and the returned object's level records are `DisTweaks_Blink.m_Levels`; the consumed offsets align with initial `PowerAttributes_Blink` fields, and those values feed spatial candidate/distance checks.

**Unresolved:** exact native offset metadata for those UProperties; why the native stride is `0x38` while the full serialized struct is `0x4C`; complete per-field mapping; whether these checks choose the final Blink destination; any collision/validity resolution that precedes movement; and the code that writes the player pawn's new location.

## Next work

1. Trace writes/initialization of component field `+0x8C` and determine whether it is populated from `m_pPowerTweaks` or a derived attribute cache.
2. Identify the source and full schema of the native `0x38` record, resolving the discrepancy against the serialized 0x4C struct.
3. Follow the candidate-query result through `FUN_00BF9AB0`, `FUN_00BFC160`, and later Blink mode handlers until either a pawn-location write is found or the targeting/effect-only path is established.
4. Separately trace PlayerController `Use`/`Select` state into the active-power manager; `Dis_SelectPower` itself selects state and does not yet prove Blink activation.
