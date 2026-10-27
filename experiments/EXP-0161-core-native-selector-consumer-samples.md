---
id: EXP-0161
title: Core bytecode handlers consume the shared native selector table
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Do indexed Core native-handler samples read a bytecode token and dispatch through the selector table identified in EXP-0159/0160, and how much of the Core token catalog has exact indexed targets?"
---

# EXP-0161 — Core bytecode handlers consume the shared native selector table

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: exact-build Core rows in the EXP-0066 static native-token catalog; raw PE verification of recorded `.data` name-pointer/adjacent-target pairs; cached exact-build decompiler review of two indexed Core handler samples and the shared selector-table initializer.
- Exclusions: no runtime execution or bytecode capture; no proof that the class-table handoff invokes these targets; no claim that all 156 Core tokens have indexed targets or are reachable; no new manual function-body review overlay entry.
- Tools: EXP-0066 [native-token dispatch catalog](../research/executable/evidence/native-token-dispatch-catalog.csv), exact-build `functions.csv`, Python 3.12.10 with `pefile` 2024.8.26, and the read-only `dishonored_static` cache for Ghidra 12.1.2 output.

## Procedure

1. Re-read the research status, Blink activation graph, and exact-build record; verify build `10256413` and executable SHA-256.
2. Select catalog rows whose package is `Core.upk`; count rows, distinct token values, and distinct xref sites.
3. For each distinct xref site, map the VA through the PE section table and compare the raw DWORDs at `site` and `site+4` with the catalog's string VA and adjacent target VA.
4. Query the cached exact-build decompilation for indexed targets associated with Core tokens `129` (`Not_PreBool`) and `130` (`AndAnd_BoolBool`), plus initializer `FUN_00426C60`.
5. Compare the sampled instructions with EXP-0159's nonzero selector load and EXP-0160's static table initialization/registration evidence. Keep registration reachability separate from consumer semantics.

## Observations

- The catalog contains 166 Core rows, 156 distinct token values, 164 distinct `.data` xref sites, and 162 distinct adjacent target VAs. All 166 `(token, target VA)` pairs are distinct. Six token values map to multiple target VAs; four target VAs are shared by multiple token values. The repeated catalog rows therefore represent distinct token/target pairs even where a token or target repeats separately.
- All 164 distinct sites map into file-backed `.data`. At each site, the raw DWORD matches the catalog string VA and the following DWORD matches the catalog adjacent target VA; there were zero mismatches. The adjacent addresses have 162 distinct values.
- 149 of the 166 token/target pairs have target VAs that exactly match an indexed function entry. These rows cover 145 distinct indexed target VAs. The other 17 pairs point to 17 distinct target addresses that do not match indexed starts. All 17 lie in `.text` and outside every indexed function body range. Raw x86 decoding at each target begins with `push ebx; mov ebx, esp; sub esp, 8; and esp, 0xfffffff0`. The indexed function CSV supplies no body bounds for these addresses; EXP-0162 separately recovers static boundary candidates without editing that index.
- The catalog maps Core token `129` (`Not_PreBool`) to indexed `FUN_00405F90` at `0x00405F90`, and token `130` (`AndAnd_BoolBool`) to indexed `FUN_00406140` at `0x00406140`.
- Cached decompiler output for `FUN_00405F90` reads a byte from `[param_1+0x18]`, advances that pointer by one, then performs an indirect call through `(&DAT_014068f0)[token]`, passing the frame-like first argument and a local result pointer. It later advances the bytecode pointer and checks an `A` marker before an additional indirect call through `DAT_014069f4`.
- Cached decompiler output for `FUN_00406140` likewise reads a byte token from `[param_1+0x18]` and indirect-calls `(&DAT_014068f0)[token]`. Its remaining bytecode parsing and conditional behavior are not interpreted by this experiment.
- Cached decompiler output for `FUN_00426C60` fills 4,096 DWORD entries at `0x014068F0` with fallback `FUN_00425E60` when its guard is clear, then accepts non-sentinel indices and stores the DWORD pointed to by its second argument at the indexed slot. EXP-0160 separately records the corresponding exact-build raw-x86 path and 33 Engine registrations.

## Interpretation and claim limits

- **Confirmed static consumer samples:** two indexed Core handler targets read a byte from the frame-like bytecode cursor and use it as an index into table `0x014068F0` before an indirect call. This establishes the shared table as a static bytecode-token dispatch structure for these samples.
- **Confirmed static table initialization relation:** the cached initializer body fills 4,096 slots with the common fallback and has a non-sentinel indexed pointer-store path; EXP-0160 verifies the corresponding exact-build raw-x86 path and Engine registration census.
- **Observed catalog coverage:** 149/166 distinct Core token/target pairs point at exact indexed function starts, representing 145 distinct indexed target VAs. Seventeen pairs point to 17 unindexed `.text` addresses. EXP-0162 supports static boundary candidates for all 17 from entry bytes, return exits, local control flow, and padding; those candidates remain outside the function index and their semantics/ownership remain unknown. Six token values map to multiple targets, and four target addresses are shared across token values; token count, pair count, row count, and target count are therefore separate denominators.
- **Inferred, limited subsystem label:** the table and sampled consumers are consistent with UE3 native bytecode handler dispatch. This does not prove that all catalogued Core `NativeToken` values are populated by this initializer or that a particular script/gameplay path reaches them.
- **Unknown:** full Core wrapper-to-initializer mapping; concrete ownership and semantics of the 17 boundary-recovered candidates; actual runtime table contents; exact semantics of the two sampled operators; and runtime reachability/behavior.
- **Limit:** consumer observations use cached Ghidra decompiler output, not a fresh raw-instruction transcription in this experiment. Catalog joins are static address relations. Neither cache output nor catalog membership establishes execution.

## Reproduction

With the matching build and repository environment available, rerun the raw PE pair verification over the Core rows in `research/executable/evidence/native-token-dispatch-catalog.csv`. The read-only decompilation endpoints are `dishonored_static.decompile_function` for `0x00405F90`, `0x00406140`, and `0x00426C60`. Existing cached output may be returned; record the cache/source identity when reproducing. Do not run broad analysis or modify the project database solely for this experiment.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Native-token catalog and limits: [EXP-0066](EXP-0066-uelib-native-token-to-executable-handler-join.md)
- Static table handoff examples: [EXP-0067](EXP-0067-native-exec-class-table-handoff.md)
- Selector consumer and unresolved field owner: [EXP-0159](EXP-0159-native-class-table-static-consumer-lookup.md)
- Raw-x86 table initialization and Engine registrations: [EXP-0160](EXP-0160-native-selector-table-static-registration-census.md)
- Static boundary candidates for the 17 unindexed Core targets: [EXP-0162](EXP-0162-core-native-unindexed-target-boundaries.md)
- Catalog: [native-token-dispatch-catalog.csv](../research/executable/evidence/native-token-dispatch-catalog.csv)
