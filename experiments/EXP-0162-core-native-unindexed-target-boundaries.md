---
id: EXP-0162
title: Static boundary recovery for unindexed Core NativeToken targets
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Can the 17 Core NativeToken target addresses absent from the checked-in function index be separated as static x86 function-boundary candidates using exact-build bytes and control flow?"
---

# EXP-0162 — Static boundary recovery for unindexed Core NativeToken targets

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching the [build record](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: all distinct Core catalog target VAs that do not equal a `functions.csv` start and lie outside its indexed body ranges; raw `.text` entry bytes; conservative candidate boundaries, return exits, relative branches, and post-return padding.
- Exclusions: no modification to the Ghidra project or 72,437-row function index; no runtime dispatch, class ownership, exact UE operator semantics, or claim that these functions are executed.
- Tools: Python 3.12.10, `pefile` 2024.8.26, Capstone 5.0.7, the exact-build function index, and the EXP-0066 native-token catalog; [recovery script](../tools/recover_core_native_token_unindexed_targets.py).
- Durable outputs: [17 boundary candidates](../research/executable/evidence/EXP-0162-core-native-unindexed-target-boundaries.csv), [instruction listing](../research/executable/evidence/EXP-0162-core-native-unindexed-target-disassembly.csv), and [input/output provenance](../research/executable/evidence/EXP-0162-core-native-unindexed-target-boundaries.json).

## Procedure

1. Re-read the research status, Blink activation graph, and build record. Require Steam build `10256413`; verify the executable SHA-256 against both the build record and the full-install file manifest.
2. Read Core rows from the EXP-0066-derived catalog. Select distinct target addresses that are not exact function starts; require 166 Core rows and 17 such target addresses, and confirm each address lies outside every indexed body interval.
3. Map each target and candidate range through the PE section table. Require `.text` and the full repeated 16-byte entry prologue `53 8B DC 83 EC 08 83 E4 F0 83 C4 04 55 8B 6B 04`.
4. Search only up to the next indexed function start for subsequent occurrences of that complete prologue. Treat a subsequent prologue as a boundary only when Capstone decodes continuously from the target, every return is `ret 8`, relative jump targets stay on decoded instructions before the final return, and bytes after the final return through the candidate boundary are all `int3` (`0xCC`).
5. Emit one boundary row per target and each decoded instruction through the return exit(s). Record hashes for the executable, index, catalog, build record, tool, and generated outputs. The output directory may be overridden to avoid replacing unrelated artifacts.

## Observations

| Token | Catalog name | Target VA | End (exclusive) | `ret 8` exits | `int3` bytes | Next full prologue |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 198 | `MultiplyEqual_ByteFloat` | `0x00406400` | `0x004064D8` | 1 | 8 | `0x004064E0` |
| 159 | `MultiplyEqual_IntFloat` | `0x00407090` | `0x00407167` | 1 | 9 | `0x00407170` |
| 160 | `DivideEqual_IntFloat` | `0x00407170` | `0x00407257` | 1 | 9 | `0x00407260` |
| 167 | `Rand` | `0x00407610` | `0x004076B8` | 2 | 8 | `0x004076C0` |
| 199 | `Round` | `0x00408460` | `0x004084EE` | 1 | 2 | `0x004084F0` |
| 275 | `LessLess_VectorRotator` | `0x00408D80` | `0x00408EC0` | 1 | 0 | `0x00408EC0` |
| 276 | `GreaterGreater_VectorRotator` | `0x00408EC0` | `0x0040900E` | 1 | 2 | `0x00409010` |
| 226 | `Normal` | `0x00409870` | `0x004099F7` | 1 | 9 | `0x00409A00` |
| 320 | `RotRand` | `0x00409CE0` | `0x00409DCA` | 1 | 6 | `0x00409DD0` |
| 300 | `MirrorVectorByNormal` | `0x00409DD0` | `0x00409FBF` | 1 | 1 | `0x00409FC0` |
| 287 | `Multiply_RotatorFloat` | `0x0040A280` | `0x0040A354` | 1 | 12 | `0x0040A360` |
| 288 | `Multiply_FloatRotator` | `0x0040A360` | `0x0040A434` | 1 | 12 | `0x0040A440` |
| 229 | `GetAxes` | `0x0040A7A0` | `0x0040A99E` | 1 | 2 | `0x0040A9A0` |
| 230 | `GetUnAxes` | `0x0040A9A0` | `0x0040AB9E` | 1 | 2 | `0x0040ABA0` |
| 270 | `Add_QuatQuat` | `0x0040C080` | `0x0040C14E` | 1 | 2 | `0x0040C150` |
| 271 | `Subtract_QuatQuat` | `0x0040C150` | `0x0040C21E` | 1 | 2 | `0x0040C220` |
| 289 | `Divide_RotatorFloat` | `0x00426920` | `0x00426A21` | 1 | 15 | `0x00426A30` |

- The executable hash matches the registered build. All 17 targets are `.text` addresses outside the indexed function starts and body ranges. They correspond to 17 distinct catalog rows/tokens in this target subset.
- All 17 start with the same full 16-byte prologue. The script recovered 17 candidate extents; each had continuous instruction decoding, one or two `ret 8` exits, only in-range branch destinations before the final return, and `int3`-only bytes between the final return and the next full prologue. One candidate has zero padding because its next entry starts immediately after the return.
- The intervals to the next *indexed* function start can contain additional unindexed entries. In particular, the Round target at `0x00408460` is followed by another full prologue at `0x004084F0`, and more code follows before the next indexed start at `0x00408620`. The output therefore records the closer repeated-prologue boundary instead of attributing the whole interval to Round.
- The generated instruction listing contains 1,579 decoded rows. The provenance JSON records tool and input hashes, versions, denominators, and output hashes.

## Interpretation and claim limits

- **Observed:** each exact catalog target begins with the repeated entry bytes and ends at a decoded `ret 8` exit (two exits for `Rand`); instruction decoding is contiguous and the listed local branch targets remain within the decoded body.
- **Confirmed, static boundary candidates:** for this exact build, the combined catalog pointer, entry prologue, return exit(s), control-flow, `int3` padding, and next full prologue support the listed start/end candidates for all 17 targets. They remain outside the checked-in function index and are not saved Ghidra function definitions.
- **Unknown:** concrete UE class ownership; exact semantics of every operator despite catalog names; table population/reachability at runtime; and whether any target executes in a particular game path.
- **Limit:** a repeated compiler prologue is not sufficient by itself to establish a function. The boundary claim uses it together with the other recorded byte/control-flow criteria and remains a static recovery, not runtime evidence.

## Reproduction

From repository root, with the matching local build available:

```powershell
python tools\recover_core_native_token_unindexed_targets.py
```

The script writes the three listed artifacts under `research/executable/evidence/`. Use `--output-dir <path>` to write elsewhere. It fails if the build SHA, Core catalog denominator, target set, or indexed-body exclusions differ. The output does not alter `functions.csv` or the Ghidra database.

## Links

- Build identity: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Core token catalog, pair denominators, and raw data pointer checks: [EXP-0161](EXP-0161-core-native-selector-consumer-samples.md)
- Static table initialization and Engine registration calls: [EXP-0160](EXP-0160-native-selector-table-static-registration-census.md)
- Catalog source: [native-token-dispatch-catalog.csv](../research/executable/evidence/native-token-dispatch-catalog.csv)
