---
id: EXP-0178
title: Task-action active-objective and HUD gates
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do the exact-build task-action flag checks do to linked task processing and the HUD flag during activation?"
---

# EXP-0178 — Task-action active-objective and HUD gates

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.
- Scope: exact-build decompilation and local x86 disassembly around the generic task-action guards; donor symbol crosswalks for objective cast, active-state, and HUD lookup helpers; external task-action editor declaration/layout and objective-state enum.
- Exclusions: no specific retail sequence instance, property value, or runtime occurrence is established. Donor/editor field and enum names are cross-source candidates, not exact-build symbols or serialized values.
- Exact-build cache records: [activation 00BA8300](../knowledge/cache/decompiles/00BA8300.json), [objective cast 00ACD1F0](../knowledge/cache/decompiles/00ACD1F0.json), [objective IsActive candidate 00AC16C0](../knowledge/cache/decompiles/00AC16C0.json), [HUD lookup candidate 00BBF730](../knowledge/cache/decompiles/00BBF730.json), and popup callbacks [00BB2480](../knowledge/cache/decompiles/00BB2480.json), [00BB2500](../knowledge/cache/decompiles/00BB2500.json), [00BB2660](../knowledge/cache/decompiles/00BB2660.json), [00BB27C0](../knowledge/cache/decompiles/00BB27C0.json), [00BB28E0](../knowledge/cache/decompiles/00BB28E0.json), [00BB2A00](../knowledge/cache/decompiles/00BB2A00.json), and [00BB2B20](../knowledge/cache/decompiles/00BB2B20.json). All records bind to the registered EXE SHA/build ID.
- External source snapshot: `D:\Dishonored\01_REFERENCE\community\dishonoredrecompiled-main`; `functions_2013.csv` SHA-256 `C3B6821A018D30E2A317D95396B6584EB0C378BA5C0BD0075EC1E8C6C240CE88`; `match_2012_2013.csv` SHA-256 `06164572249FD3E2477F1C404B2AF6A27CACF83ACECB8C82DB08FCEDE037B330`; `DishonoredGameObjectivesClasses.h` SHA-256 `F5153AB3CF81341C94ADF6DE6B773721DED71E73CA22D45CAF586461EEC7979E`; `DishonoredGameEngineShims.h` SHA-256 `28C42700560E38AFDBB8ECD46D11065E9CD4BC89F8DFD8DFDC045A0216D7D2CA`.
- Editor source: `D:\Dishonored\10_EDITOR_RESTORATION\history\attempt-0_DishonoredEditor_2026-10-04\01_Archive\fansdk_audit\extracted\DishonoredEditor\Development\Src\DishonoredGame\Classes\DisSeqAct_TaskAction.uc`, SHA-256 `7B73806F22E07644CA2EDA7C6ADD3264E36280B62CA635BF7796AFACB99FC79F`.

## Procedure

1. Verify the registered build SHA and the SHA/build metadata of the four exact-build decompile caches.
2. Read the activation pseudocode and decode the call-site instructions around `FUN_00ACD1F0` and `FUN_00AC16C0` from the exact-build PE to identify the receiver passed to `IsActive`.
3. Compare donor export/matcher rows for `Cast<UDishonoredObjective>`, `UDishonoredObjective::IsActive`, and `DisGetGFxHUD` with exact-build starts and sizes.
4. Read the popup callback bodies to check whether they consume the HUD mask set by activation.
5. Read the editor declarations/defaults for the two task-action booleans, the reflected class span, and the separate objective-state enum.
6. Keep exact byte/bit behavior distinct from inferred property names, defaults, and runtime effects.

## Observations

- In `FUN_00BA8300`, the action's DWORD at byte offset `+0xF8` is read twice: bit 0 is copied into the HUD object's flag mask `+0x1FC / 0x4000`; bit 1 gates an objective-state filter. The activation candidate's function-size mismatch and donor match quality are documented in EXP-0177.
- Under the outer activation guards (`DAT_0145F614 != 0` and its `+0x6F8` field nonzero), the code gets a HUD pointer via `FUN_00BBF730`. If non-null, it sets or clears HUD mask `0x4000` from action bit 0, processes linked tasks, then ORs `0x4000` back into that HUD field.
- Exact-build callbacks `FUN_00BB2480`, `FUN_00BB2500`, `FUN_00BB2660`, `FUN_00BB27C0`, `FUN_00BB28E0`, `FUN_00BB2A00`, and `FUN_00BB2B20` each test the same HUD mask `param_1+0x1FC & 0x4000` before building or changing objective/task popup records. When the mask is clear, these callback bodies skip their popup-record work.
- If action bit 1 at `+0xF8` is clear, each non-null task instance that passes the other helper guards reaches the virtual `+0x190` callback without the objective-active filter.
- If action bit 1 is set, the action passes the task instance's pointer at `+0x24` to `FUN_00ACD1F0`. The helper is a donor-matched candidate for `Cast<UDishonoredObjective>`: it returns the pointer when it is an objective cast, otherwise null. A failed cast passes the OR condition; a successful cast is passed in ECX to `FUN_00AC16C0`.
- Exact-build x86 instructions at `0x00BA842C–0x00BA843B` show `push eax; call 0x00ACD1F0; add esp,4; test eax,eax; je ...; mov ecx,eax; call 0x00AC16C0`. Thus the active-state helper receives the successful cast result as its object receiver.
- `FUN_00AC16C0` returns whether the byte at receiver offset `+0x45` equals zero. Its donor export row is `UDishonoredObjective::IsActive`, matcher method `callee`, ratio `1.000`, donor sizes 9/9; the exact-build indexed size is also 9 bytes.
- `FUN_00ACD1F0` has an exact-build indexed size of 66 bytes versus donor 2013 size 69. Its donor row is `Cast<UDishonoredObjective>`, matcher method `callee`, ratio `1.000`; retain the 3-byte size discrepancy.
- `FUN_00BBF730` has exact-build/donor size 57/57; the donor candidate is `DisGetGFxHUD` with `callee` ratio `0.950`.
- External editor source declares `m_bShowHUDNotification` first and `m_bOnlyOnTasksInActiveObjectives` second in `DisSeqAct_TaskAction.uc`, with both defaulted true in that editor artifact. The generated reflected C++ class lists these as adjacent bitfields and reports a reflected property span at bytes 248–252 (`0xF8–0xFC`). This aligns with the exact-build bit reads at `+0xF8`, but does not prove per-node retail values or bit-name assignment in the target package.
- External generated enum `EDisObjectiveState` lists `DOS_Active=0`, `DOS_Completed=1`, and `DOS_Failed=2`. This is consistent with exact-build `IsActive` testing objective byte `+0x45` for zero and EXP-0174's candidate completion write of value 1; the enum artifact is not hash-bound to build 10256413.

## Interpretation

- **Observed, exact-build static:** the action has two relevant flag bits at `+0xF8`. Bit 0 conditionally sets HUD mask `+0x1FC & 0x4000` during the guarded activation loop. The popup callbacks in EXP-0176 check this same bit and skip popup-record work when it is clear. Bit 1, when set, adds an objective filter: if the task's `+0x24` pointer casts to an objective, that objective must pass the active test at `+0x45 == 0`; if the cast fails, this filter branch permits processing.
- **Inferred, field labels:** editor declarations and reflected field order support identifying bit 0 as candidate `m_bShowHUDNotification` and bit 1 as candidate `m_bOnlyOnTasksInActiveObjectives`. The editor defaults are not transferred to any specific retail action instance.
- **Inferred, state label:** the exact-build `IsActive` candidate's zero comparison and external enum support `objective +0x45 == 0` as candidate `DOS_Active`; value 1 as candidate `DOS_Completed` is independently consistent with EXP-0174. The exact-build code observation is stronger than the donor enum label.
- **Unknown:** whether other consumers use HUD mask `0x4000`, the visible presentation/localization of popup records, the live identity of the outer activation gate, the serialized retail flags on Boyle actions, and runtime occurrence.
- **Limit:** names/defaults/enums come from external editor/2013 donor artifacts without the target EXE hash. Ghidra output is a rendering of the exact-build machine code, not original source. No compressed package payload was decompiled and no runtime process was launched.

## Reproduction

1. Confirm the build SHA in `research/builds/BUILD-STEAM-10256413/build.md` and the cache metadata for the linked functions.
2. Re-run the read-only decompilations and inspect `FUN_00BA8300`'s guards and two bit tests.
3. Re-disassemble exact-build VA `0x00BA842C` to verify the `Cast` result is moved to ECX before the `IsActive` call.
4. Resolve the three donor rows and compare their donor/index sizes; do not hide the 66/69 size discrepancy for the cast helper.
5. Verify the same `+0x1FC & 0x4000` guard in the seven popup callback caches and compare with their numeric record writes in EXP-0176.
6. Inspect the identified editor script, generated class header/layout, and enum declaration while keeping their provenance distinct from target build bytes.

## Links

- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Generic Task resolution and vtable dispatch: [EXP-0177](EXP-0177-kismet-task-variable-to-native-dispatch.md)
- Task/objective completion path: [EXP-0174](EXP-0174-task-to-objective-completion-hud-path.md)
- Evidence cluster: [OBJ-001](../docs/findings/obj-001-objective-task-kismet-hud.md)
