# REV-0005 — Review of EXP-0021 / EXP-0022 status report

Date: 2026-10-26. Scope: user-provided combined status report after REV-0004. **This is a documentary review, not an independent Ghidra re-run.** Original local EXP-0019, 0020, 0021, 0022, binary, decompiler output and game assets are **not present** in the connected GitHub branch. Do not fabricate evidence.

## Resolved owner-first virtual dispatch (reported)

| Class | Descriptor VA | Constructor VA | vtable VA | virtual byte offset | slot address VA | concrete method VA |
|---|---:|---:|---:|---:|---:|---:|
| `DisGFxMoviePlayerPowerWheel` | `0x01354070` | `0x00BD1080` | `0x01161C08` | `0x1F0` | `0x01161DF8` | `0x00BCD800` |
| `DishonoredPlayerController` | `0x01316938` | `0x00ABD1F0` | `0x01118738` | `0x560` | `0x01118C98` | `0x00AB4680` |

These assignments use the user's reported descriptor→constructor→vptr evidence. The exact bytes and call ABI remain independently unverified here. The previous false attribution `FUN_00BBD3A0` to PowerWheel is **superseded**: reported Store descriptor `0x013543E0` → constructor `0x00BD7910` → vtable `0x01163388`.

### Confirmed within reported static trace

- PowerWheel `OnSelectionChanged`: reported wheel ID `24` → branch code `2`, class `DishonoredActivePowerComponent_Blink`, active-power lookup, Scaleform `UpdateItemInfos`. This is an **information/UI refresh** path; it does not prove casting, motion, or assignment of `_iPower`.
- Controller `Dis_SelectPower(int _iPower)`: target `FUN_00AB4680` checks an index against `pawn+0xA44` and reads array/storage at `pawn+0xA40`, passing data through pawn virtual slots `+0x6E8/+0x6E4`. This supports **selection-index lookup**; source-side mapping to `m_UsableActivePowerIndices` is **inferred**, not a proven field name.
- Pawn field area `+0x788/+0x78C` behaves consistently with active-power array storage; **do not conflate object field offsets** with a *vtable slot offset* of equal number in another call.
- Shortcut `Use/Select` bodies modify state/bitmask, call Scaleform `SetShortcutSelection`, and write a shortcut-derived byte at `+0x228`; this byte's semantics are unproven. No direct Blink cast call observed in the **inspected bodies only**.
- Four reported Blink-vtable-specific candidates: `0x00BFC5D0`, `0x00BFC160`, `0x00BFBC90`, `0x00BF9AB0`. Across the family, code references positions, distances, timers and stride `0x38`, but assignments to individual functions and record format **are not supplied** by the summary. No observed direct pawn-position write **within the inspected code**, not proof of absence downstream.
- `0x00C7E200` and `0x00C82AA0` each reportedly have 301 data references; this does not prove Blink-specific behavior. `0x00414DC0` checks object flag `0x80000`, without confirmed meaning.

### Provenance / environment

- Latest local user report says workspace EXE SHA-256 was recalculated and matched earlier `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; here we cannot reproduce that hash.
- Ghidra reports total 72,925, while indexed CSV `getFunctions(true)` contains 72,437 non-external functions. API semantics explain the method discrepancy *in principle*, but exact external count 488 still must be measured in this particular database.
- The stale path in `get_database_info` is unresolved metadata; no supported rebinding/save has been shown.
- Local tests were **not** run in EXP-0022 according to report.
- Excluded co-op project remains out of scope; do not browse it or use unexplained DLLs.

## Critical distinctions and falsification targets

1. **Selection vs activation:** `UpdateItemInfos` and `SetShortcutSelection` update UI/state; neither proves initiating Blink.
2. **Three mappings remain separate:** wheel item `24` → UI `2` is observed *in this handler*, but `_iPower`, usable-array index, and active-array index `0` are not thereby equated.
3. **Index access:** validate `pawn+0xA40/+0xA44` with disassembly, array element width and bounds, and compare UE3 reflected declaration before assigning a property name.
4. **Candidate calls vs movement:** no direct write in four methods is a bounded negative result. Follow return values, outgoing calls, CALLIND and state transitions until the specific pawn/world transform write is identified.
5. **`0x38` stride:** establish base allocation, count/capacity, element reads/writes, index calculation and producers/consumers before naming a point/trajectory structure.
6. **Class-layout stability:** base-class/different-vtable method comparisons require concrete Blink vtable address, base table address, constructor and slot offsets, absent from current summary.

## Recommended next experiments

- **EXP-0023:** targeted Blink native dataflow, configuration consumers, callback/callind edges and possible move/transform side effects. Evidence export is read-only and hash-guarded.
- **EXP-0024 (separate):** shortcut stored byte `+0x228`, usable power indices at `+0xA40/+0xA44`, active power arrays at `+0x788/+0x78C`, map to Blink through confirmed construction/array access; no forced equivalence.
- Sync original EXP-0019–0022 as permitted text/evidence once accessible; do not replace primary experiments with this summary.

Official Ghidra API: [DecompInterface](https://ghidra.re/ghidra_docs/api/ghidra/app/decompiler/DecompInterface.html); [PcodeOp](https://ghidra.re/ghidra_docs/api/ghidra/program/model/pcode/PcodeOp.html); [ReferenceManager](https://ghidra.re/ghidra_docs/api/ghidra/program/model/symbol/ReferenceManager.html).
