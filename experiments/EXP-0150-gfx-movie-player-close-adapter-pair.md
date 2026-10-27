---
id: EXP-0150
title: GFx movie-player close callback adapter pair
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do five GFx movie-player close exports and the exact-build targets at 0x009F6BA0 and 0x009F82F0 establish about their shared adapters?"
---

# EXP-0150 — GFx movie-player close callback adapter pair

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect five exact EXP-0139 exports mapped to targets `0x009F6BA0` and `0x009F82F0`, compare declarations and class Super paths, and byte-compare both indexed bodies.
- Exclusions: no names assigned to receiver slots `+0x1F0` or `+0x1FC`; no relation between UI close event names and concrete runtime effects inferred; no runtime reachability or visible UI behavior claim.
- Inputs: EXP-0139 class-table/UELib join; EXP-0071 UELib class inheritance catalog; exact-build function index; read-only decompilation caches; exact-build executable.
- Durable outputs: [two-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0150.csv), [42-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0150.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0150.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Resolve all EXP-0139 rows for the two targets; compare exact names, declarations, native flags/tokens, script sizes, source rows, and source hashes.
3. Resolve both functions in the exact-build index and confirm their read-only decompilation caches carry the same build ID and executable SHA.
4. Map both indexed VAs into `.text` using the PE32 image base and section table; hash each 53-byte range and compare them byte-for-byte.
5. Trace each export owner's `UClass.Super` chain from EXP-0071. Do not use class inheritance to infer function override relations or runtime UI behavior.
6. Add both targets as inferred L1 adapter candidates only.

## Observations

- The executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; PE32 image base is `0x00400000`. Both targets are exact-build indexed functions in `.text`, each 53 bytes.
- Three exact exports target `0x009F6BA0`: `DisGFxMoviePlayerGamma.OnGammaImageClosed`, `DisGFxMoviePlayerNote.OnReadableNoteClosed`, and `DisDLC05MoviePlayerBrief.OnBriefScreenClosed`.
- Two exact exports target `0x009F82F0`: `DisGFxMoviePlayerMissionStats.OnClosed` and `DisGFxMoviePlayerPowerWheel.OnClosed`.
- All five exports are `NativeFlag=true`, `NativeToken=0`, script size 2, and declare zero explicit parameters. Their source JSONL rows are 303, 377, 871, 375, and 389, respectively; they are recorded in the exact-source catalog identified by SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`.
- All five `UClass.Super` chains pass through `Class'DishonoredGame.DisGFxMoviePlayerBase'` and then `Class'GFxUI.GFxMoviePlayer'`. The class relation catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The decompilation caches for `0x009F6BA0` and `0x009F82F0` record build `10256413` and the exact executable SHA above. Their pseudocode SHA-256 values are `6824581440FC8C48B317F3F7E462373E2056862EF1D767B018FF1452C5A85504` and `E821C298FF56B5FF73AD5A554FDB15AD1EACBF116EE44F706B697B06930B1DDC`.
- The raw `.text` range SHA-256 values are `78EC0EB9298592B123A6AC883C5675CC4F06BE457372BF1D25D19E5B0AF2FC91` for `0x009F6BA0` and `8AB7DFF1FDA46DD39F7628F629DE96B4CA0F412E3FDEE0554256F7A7D1904B20` for `0x009F82F0`. A bytewise comparison finds one difference at offset `0x28`: `0xF0` versus `0xFC`; the other 52 bytes are equal.
- The changed instruction reads the receiver vtable displacement `+0x1F0` in `0x009F6BA0` and `+0x1FC` in `0x009F82F0`. Both bodies advance the script cursor, conditionally process the `A` marker, and make an indirect receiver call with no explicit arguments.
- Neither target appeared in the EXP-0149 cumulative overlay. This addition records two L1 reviews only; it creates no confirmed semantic claim, inter-function L3 edge, or runtime record.

## Interpretation and claim limits

- **Observed:** five exact zero-parameter exports map to two indexed native/token-zero targets. Their class Super paths pass through `DisGFxMoviePlayerBase` and `GFxMoviePlayer`.
- **Observed:** the two 53-byte bodies match at 52 of 53 byte offsets. Their only byte difference selects receiver displacements `+0x1F0` and `+0x1FC`; both issue a no-explicit-argument indirect call.
- **Inferred, limited:** the two targets are shared native-exec adapter candidates for the five export names. Exact table/export joins, matching declarations, and byte-level evidence support the grouping.
- **Unknown:** the virtual members at either displacement, whether the exported names share a semantic contract, runtime reachability, and resulting UI behavior.
- **Not established:** common class ancestry or shared adapter shape does not prove a common UFunction override or a particular movie-close effect.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select its rows for `0x009F6BA0` and `0x009F82F0`.
2. Resolve both functions in `research/executable/functions.csv`; verify their decompilation cache build ID and executable SHA.
3. Read each 53-byte range from the exact executable `.text` section using `RVA = VA - 0x00400000`; verify both hashes and the sole difference at offset `0x28`.
4. Trace all five class paths in EXP-0071's UClass inheritance catalog. Do not treat these relations as UFunction override evidence.
5. Verify the cumulative manual overlay contains 42 unique addresses and includes both new target addresses.

The class relations and export declarations derive from the same UELib corpus. Static table and code evidence does not demonstrate runtime use. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior class-table native adapters: [EXP-0144](EXP-0144-navmesh-goal-recycle-thunk.md) and [EXP-0148](EXP-0148-state-exit-single-argument-adapter-pair.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
