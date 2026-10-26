# EXP-0024 — Selection-index and shortcut-code mapping

**Status: planned, not executed.** Parent evidence: report-only EXP-0021/0022 summary and REV-0005 audit. Build SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (revalidate before binary work).

## Variables / namespaces that must not be conflated

| Origin | Value or field | Status |
|---|---|---|
| PowerWheel item enum | `DPWI_Blink=24` | package metadata from earlier report |
| UI selection enum | `eDisUISelectionType_Blink=2` | package metadata |
| Wheel handler | `24 → branch code 2` | static result reported in EXP-0021 |
| Default Pawn | `m_ActivePowers[0]` points to Blink | serialized package default |
| Autoassigned shortcuts | gamepad position 1, keyboard position 5 | default array *orders*, not necessarily shortcut indices |
| Controller selection | `_iPower` integer | domain/encoding **unknown** |
| Pawn array | pointer/data `+0xA40`, bound `+0xA44` | native dataflow report; class-offset naming **hypothesis** |
| Pawn active-power storage | `+0x788/+0x78C` | identity with `m_ActivePowers` unproven |
| Shortcut byte | `+0x228` | stored value; mapping not established |

## Experiment steps

1. Reconfirm Controller constructor/vtable/slot target `0x00AB4680` from primary bytes; identify `this` vs Pawn base addresses.
2. Trace how `_iPower` is range checked and how it addresses the `+0xA40` array. Determine element width, allocation, length/capacity, signedness and sentinel/error behavior.
3. Resolve real Pawn targets at `+0x6E8/+0x6E4`; look for reads of the returned usable index into `+0x788/+0x78C` and any state changes. **Same hex literal as a vtable slot doesn't imply the same data structure**.
4. Trace shortcut Select/Use state update and source of byte `+0x228`: table base, array stride, lookup bounds, enum mapping; compare keyboard/gamepad independently.
5. If the code maps wheel 24 to 2 in `FUN_00BCD800`, record exact branch site, arguments and call edge. This UI conversion does not establish a cast conversion.
6. Use a controlled test build/runtime observation only after setting a clean DLL baseline. Check changes in current selected power separately from Blink cast/teleport; avoid running unknown `dinput8.dll`.

## Falsification cases

- Usable-array element at index 0 is not Blink, despite serialized active-power index 0 referring to Blink.
- UI code 2 maps to a wheel highlight but not the parameter domain of `Dis_SelectPower`.
- Shortcut stored byte `+0x228` is a UI slot label rather than a power enum.
- Pawn `+0x788` represents a different field than inferred, or a base-subobject pointer changes offsets.

## Exit

Provide a *directly observed mapping* between `_iPower` and Blink element (or document negative/alternative results), with concrete reads and writes and a named build. Separately document use/cast initiation if present. Do not label Blink relocation found merely because the selection state updates.
