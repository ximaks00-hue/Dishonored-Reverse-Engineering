# EXP-0015 — Resolution of PlayerController / PowerWheel receiver methods
**Status:** planned. **EXE:** Windows x86 SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` (report-only; locally recheck). Image base `0x00400000`.

## Hypothesis
The specific C++ methods executing wheel selection and power selection can be resolved by identifying the receiver's vtable **through constructor/registration evidence**. A UE3 native-exec name→wrapper table is not a C++ vtable.

## Known boundaries
| Owner | Exec function | Wrapper VA | Receiver byte offset |
|---|---|---:|---:|
| Controller | `Dis_WheelShortcuts_KeyboardSelect` | `0x009EDE30` | `+0x50C` |
| Controller | `Dis_WheelShortcuts_GamepadSelect` | `0x009EDD70` | `+0x504` |
| Controller | `Dis_WheelShortcuts_KeyboardUse` | `0x009EDE90` | `+0x510` |
| Controller | `Dis_WheelShortcuts_GamepadUse` | `0x009EDDD0` | `+0x508` |
| Controller | `Dis_SelectPower(int)` | `0x009EE630` | `+0x560` |
| Controller | `OnTeleport_Native(SeqAct_Teleport)` | `0x009EDC30` | `+0x4F8` |
| PowerWheel | `OnSelectionChanged(int)` | `0x009F8290` | `+0x1F0` |

*Important counterexample:* `DishonoredPawn.JumpOffPawn` also uses `+0x560`, so slot numbers are class-relative, not unique function IDs. Cheat-manager `+0x510/+0x514` and base Pawn teleport `+0x538` are likewise different receivers.

## Procedure (read-only)
1. Recalculate file SHA-256 and Ghidra program identity; do not force-save while there is an active transaction.
2. Run optional `Exp0015VtableCandidateExport.java` on the exact x86 program (in the companion pack). It scans initialized non-executable blocks for DWORD pointer runs consistent with the reported slots, retaining table-base references from code. **Candidate shape does not prove class owner.**
3. For promising candidates: locate writes of table address into the constructed object's first DWORD, trace constructors/native class name/factory registration, and identify class with **two independent indicators**.
4. Once a receiver table is proven, list concrete target VAs and RVAs at `+0x504/+0x50C/+0x510/+0x560`, and independently at PowerWheel `+0x1F0`.
5. Trace the implementation and data flow of `_iPower` and `_ItemIdx`; distinguish `DPWI_Blink=24`, UI enum `2`, active-array index `0`, and shortcut autoassignment order `1/5`.
6. If a teleport handler appears, verify whether it is a Kismet `SeqAct_Teleport` callback versus the physical movement implementation of Blink.
7. Record raw cross-references, function addresses, conditions, Ghidra version, method and possible negatives. Preserve contrary evidence.

## Deliverables
- table-candidate CSV + class-specific registration/constructor reasoning;
- concrete virtual method targets for controller and wheel;
- call graph with **observed edges only** and selection encoding evidence;
- unresolved alternatives and applicable build hash;
- separate ArkCpntType_Lookat/factory workstream if needed.

## Exit gate
At least one verified PlayerController vtable and one verified PowerWheel vtable, ownership supported by two independent indicators per table, and correct resolved target functions. Finding a pointer run alone is not completion. Blink displacement cannot be claimed until the execution chain and player position change have been evidenced.

## Important safety and workflow caveats
Don't run untrusted DLLs in the modified game copy, don't modify copyrighted game bytes, don't mix releases, and do not open a second headless process on the live locked Ghidra database. 
Official headless usage: https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md
