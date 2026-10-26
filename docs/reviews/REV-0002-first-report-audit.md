# REV-0002 — First report audit (2026-10-26)

**Status:** review of supplied 85-line Markdown report. **Original game binaries, Ghidra database, and EXP-0001–EXP-0013 logs have NOT been accessed through this repository.** Do not mistake reported observations for independently reproduced results.

**Target build reported:** Steam 217980 / public build 10256413; Dishonored.exe x86, 18,041,856 B, SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.

## Findings and qualification

| Domain | Reported evidence | Assessment / next check |
|---|---|---|
| Inventory | 13,746 current files; 13,603 hash-equal; +143/−4 vs prior local manifest | Arithmetic matches (prior file count 13,607), but work folder is NOT a clean Steam installation; classify added DLL and analysis files offline. |
| Steam build | app 217980 / build 10256413 | SteamDB confirms public build **ID**, not the particular EXE SHA. Obtain depot-file provenance. |
| UPK | DishonoredGame.upk version 801/30; 24,432 names, 30,049 exports, 652 imports; Core.upk 720/1,356/18 | Parser-reported counts, not semantic coverage or engine architecture proof. |
| Decompression | Gildor Tools/PackageUnpack built from source; UELib 1.13.3 initialized 30,049 exports | Good separation of working decompressed copy and original; store tools/args, source and output hashes. |
| Native Blink class | `DishonoredActivePowerComponent_Blink` extends `DishonoredActivePowerComponent`, `native(Power)` | No direct Function exports in examined class ≠ absence of native methods, inherited code, or other packages. |
| Blink tweaks | CDO values differ from `Twk_Powers.Blink.Twk_Blink`; runes [1,3] | Two indexed values may reflect progression; code path consuming the data has NOT been identified. No inferred runtime `m_fBlinkDistanceMax`. |
| Ghidra | Autoanalysis indexed 72,925 functions, image base 0x400000 | Autoanalysis completed ≠ full native reconstruction. Recover lock/saving and stale executable-path metadata. |
| Exec stubs | Cheat manager BlinkShowRange / RangeFull and other power wrappers found | Adapters to native/virtual functions, not proof of Blink movement implementation. |
| `FUN_00956660` | Uses keys `BlinkBlender` and `Blink` through lookup helper `FUN_00592BE0` | Function owner, lookup result types, and link to gameplay unknown. Single .rdata function pointer NOT sufficient for vtable identification. |

## Specific next task: EXP-0014

Investigate the suspected pointer at `0x010A66B0`, function `0x00956660`, lookup helper `0x00592BE0` and initialization helper `0x00454FE0`.

1. Export xrefs to the function, lookup helpers, strings and *table address*, not just the pointed function.
2. Inspect neighboring `.rdata` DWORDs and seek constructor stores of a table-base address; classify table as vtable or another dispatch structure only with multiple independent clues.
3. Track `this+offset` writes and the subsequent consumers of the two lookup return values.
4. Reconstruct record stride and key construction for `FUN_00592BE0`; do not assume `FName` solely because two integers are compared.
5. Map any validated owner to UE3 class metadata, if supported, and preserve unresolved branches.

## Normalized addresses (reported VA → derived RVA)

Image base `0x00400000`:
- `FUN_00956660` `0x00956660 → 0x00556660`
- `FUN_00592BE0` `0x00592BE0 → 0x00192BE0`
- `FUN_00454FE0` `0x00454FE0 → 0x00054FE0`
- `BlinkBlender` `0x010A5830 → 0x00CA5830`
- `Blink` `0x010A5840 → 0x00CA5840`
- `.rdata` candidate slot `0x010A66B0 → 0x00CA66B0`
- `execBlinkShowRange` `0x009F4020 → 0x005F4020`
- `execBlinkShowRangeFull` `0x009F4090 → 0x005F4090`

Reported byte offsets `+0x510/+0x514/+0x560/+0x788/+0x7E4` would correspond to 4-byte-pointer indices 324/325/344/482/505 **only if they actually reference a pointer table**.

## Repository gap

The connected `main` branch is an initial scaffold and does not contain the build manifests or EXP-0001–EXP-0013 referenced in the uploaded local report. This draft PR provides a review and a new protocol only; it does NOT fabricate or rewrite absent primary evidence. Local `E:\\...` paths must be replaced by portable repository links as source material is synchronized.

## Proposed milestones

- **P0:** preserve Ghidra project safely, update .gitignore for excluded coop project; never run untrusted `dinput8.dll`.
- **P1:** complete read-only EXP-0014 export and manually validate callers, table candidate and `this` ownership.
- **P2:** verify UE3 property offsets and Blink tweak index consumers; distinguish defaults vs instance values.
- **P3:** only with an established code path, investigate targeting and final position update.

Exit criterion for native owner milestone: build SHA check, function + table xrefs, *two independent ownership indicators*, and documented use of returned lookup values.

## References

- Source: user-provided «Отчёт о проделанной работе» (primary EXP log files not available here).
- Steam public build: https://steamdb.info/app/217980/depots/
- Ghidra Program API: https://ghidra.re/ghidra_docs/api/ghidra/program/model/listing/Program.html
- Ghidra ReferenceManager: https://ghidra.re/ghidra_docs/api/ghidra/program/model/symbol/ReferenceManager.html
- Gildor PackageUnpack: https://github.com/gildor2/UEViewer/tree/master/Tools/PackageUnpack
