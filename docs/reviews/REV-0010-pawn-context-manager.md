# REV-0010 — Pawn context manager and keyed registry audit

Date: 2026-10-26. Basis: user's reports on EXP-0032–EXP-0036. This is an **assessment of reported static observations**. Original local experiments, Ghidra program and EXE were not read through connected repository, and no runtime experiment was performed.

## Progress

- `FUN_00B58860` and `FUN_00AB3210` reportedly belong to `DishonoredPlayerPawn` vtable slots `+0x5BC` and `+0x5C8`; the former configures context-manager pointer at `pawn+0x59C`, the latter uses the manager to dispatch through `FUN_00AA2590` and `FUN_00C04C30`.
- `FUN_00C04C30` invokes receiver virtual slots `+0x134` and conditionally `+0x188`. The known `DisItemContext_UsePower` `+0x134` method (`FUN_00C44D30`) reportedly expects an extra float argument and returns with `RET 4`, whereas this callsite does not explicitly supply it. **Treat this route as a poor or unproven UsePower candidate**, not an identified cast dispatcher. Recheck exact stack contract, implicit arguments, adjusted `this`, thunk and calling conventions before classifying irreconcilable.
- `FUN_00B36CA0` has 107 call references and manages generic keyed records; concrete registrations key 3 → `FUN_00C128B0` and key 9 → `FUN_00C0B940` are separate usages, not proof of Blink-specific event handling.
- `DisTweaks_ItemPowers` configuration reportedly links `Use Power` → `DisTweaks_UsePower` → class `DisItemContext_UsePower`; this establishes package configuration, not runtime construction.
- `FUN_00C0CA70` traverses a `0x30`-stride array at manager `this+0x60` with base/count/capacity at `+0x27C/+0x280/+0x284`; virtual receiver is read through another pointer chain involving `+0x1E0`. Five direct call sites were analyzed, but no concrete UsePower receiver is shown. Producers of the records are still unknown.
- `FUN_00C2F750` provides a callback token into `FUN_00C105F0`; `FUN_00C12A80` conditionally registers/removes entries, but registry owner and event identity still unknown.
- `ue_explorer.inspect_package` and `search_objects` now work; direct `decompile_object` on compressed tables remains limited. The already decompressed local UELib evidence should not be treated as invalidated.

## Prior evidence to preserve

- Known conditional inner route: `DisItemContext_UsePower +0x134 → FUN_00C44D30 → Blink +0x174/FUN_00BE7580 → Blink +0x1AC/FUN_00BFC990 → mode 1`.
- Separate movement path `FUN_00BFC5D0 → FUN_00BFC160 → FUN_00BECDF0 → FUN_006539C0` writes pawn-relative `+0xC4/+0xC8/+0xCC` on successful conditions.
- No documented end-to-end user-button-to-runtime-Blink execution.

## Next discriminating checks

1. Establish manager `pawn+0x59C` construction, ownership, and exact writers of empty/context entries.
2. At `FUN_00C04C30`, recover the actual machine-code stack delta and intended virtual method signature, not only decompiler's argument count; decide if UsePower `RET 4` is possible.
3. Identify owner of keyed manager storage `+0x1650` and registration / lookup use of keys 3 and 9; do not assert all 107 callers are callbacks.
4. Trace package `DisTweaks_UsePower` to a runtime constructed `DisItemContext_UsePower` object through constructor/object fields and assigned vptr.
5. Independently revisit dispatcher `FUN_00C0CA70` receiver's pointer identity, not just matching slot offsets.

**Open question:** where does an actual user Use input connect to a runtime UsePower object, and how does that object reach the conditional Blink move-mode setter?
