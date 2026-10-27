---
id: EXP-0018
title: "NPC look-at property correlation"
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Does package data support NPC look-at ownership for ArkCpntType_Lookat, and is there a Blink move link?"
---
# EXP-0018 — NPC look-at property correlation

- Status: package ownership confirmed; native Ark type equivalence and Blink movement relation unresolved.
- Date: 2026-10-26.
- Build: Steam app 217980, build 10256413.
- Package input: decompressed analysis copy `assets/extracted/dishonored-blink/DishonoredGame.upk`, SHA-256 `28CF9A76825B92A12545E1A5584285DD4061B0BF85BD51293A0B4E51C29AEFF9`; derived from installed package SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`.
- Parser: Eliot.UELib 1.13.3, read-only package initialization and reflection.
- Scope: resolve the package owner/type reference for `m_pCpntLookat` and compare it with the native method-table evidence in EXP-0014. No installed game file, Ghidra program byte, or type was changed; `_excluded_coop_project/` was not accessed.

## Findings

- UELib resolves `m_pCpntLookat` as a `StructProperty` whose outer is `Class'DishonoredGame.DishonoredNPCPawn'` (export 8986); the property itself is export 2194.
- The property flags are `Native` and `Transient`. Its serialized `Struct` reference is import `-572`, resolving to imported `Core.ScriptStruct'Pointer'` (import-table index 571). UELib does not expose a concrete Ark class through this generic pointer type.
- The same package has look-at declarations including `DisLookAtRequest`, `m_LookAtRequest`, and `m_pCurrentLookAtDistraction`; these establish that the package contains a separate NPC look-at data path, but do not connect its consumers to a specific native type.
- Independently, EXP-0014 supports `FUN_00956660` as slot 7 in a method table whose name getter returns `ArkCpntType_Lookat`. That initializer looks up keys `BlinkBlender` and `Blink` and stores pointer-like lookup results.

## Evidence classification

**Confirmed:** `m_pCpntLookat` is a native, transient property owned by `DishonoredNPCPawn` and its declared serialized type reference is generic `Core.Pointer`. The package contains separate NPC look-at request/distraction declarations. EXP-0014's native method-table attribution and Blink-key lookup remain independently supported.

**Inference:** the shared `Lookat` naming makes it plausible that `m_pCpntLookat` relates to the native `ArkCpntType_Lookat` family. The property is generic `Pointer`, however, and the current artifacts do not prove that both names refer to the same runtime object or structure.

**Not established:** the concrete runtime type behind `m_pCpntLookat`; the types/roles of the `BlinkBlender` and `Blink` lookup results; whether the look-at component participates in Blink visuals/targeting; or any connection to the player-power activation or relocation path.

This result increases the plausibility that `FUN_00956660` belongs to NPC look-at/component initialization, and further weakens any attempt to treat its Blink-name lookups as proof of player teleportation. It does not rule out a visual support relationship.

## Reproduction

Run the local read-only UELib reflection utility against the decompressed analysis copy. The captured output is local-only at `.tmp/ue-readonly-dump/EXP-0018-property-owner-check.log`. Relevant values are the property outer path, `PropertyFlags`, `UStructProperty.Struct` import index, and import table entry 571.

