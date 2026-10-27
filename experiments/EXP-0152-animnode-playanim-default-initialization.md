---
id: EXP-0152
title: AnimNode PlayAnim parameter initialization and shared adapter
experiment_status: done
claim_status: mixed
build: "10256413"
question: "What do three PlayAnim class-table exports and the body at 0x005DB790 establish about parameter initialization and dispatch?"
---

# EXP-0152 — AnimNode PlayAnim parameter initialization and shared adapter

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: inspect the three EXP-0139 `PlayAnim` class-table edges to `0x005DB790`, compare exact declarations and class Super paths, and trace local initialization and decoded values through the indirect call.
- Exclusions: no identity assigned to receiver slot `+0x134` or global `DAT_0140A948`; no claim that optional defaults are used for omitted runtime arguments; no animation playback result, exact UFunction override, or runtime reachability inferred.
- Inputs: EXP-0139 class-table/UELib join; EXP-0071 UELib class inheritance catalog; exact-build function index; read-only decompilation cache; exact-build executable.
- Durable outputs: [manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0152.csv), [44-row cumulative overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0152.csv), and [coverage summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0152.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Select the three exact EXP-0139 edges at `0x005DB790`; compare owner paths, declarations, NativeFlag, NativeToken, script size, source rows, and source hash.
3. Resolve the target in the exact-build function index; verify the read-only cache build ID and executable hash.
4. Map its indexed byte range into `.text` using the PE32 image base and section table; hash the body. Read the referenced `.rdata` float constant by VA-to-RVA and decode its raw IEEE-754 value.
5. Trace local initialization, decoder calls, global bit-mask writes, and the indirect receiver call in the decompilation/raw instruction flow.
6. Resolve each exact export owner's `UClass.Super` path in EXP-0071; do not treat class ancestry as function override or runtime behavior evidence.
7. Add one inferred L1 adapter candidate only.

## Observations

- The executable SHA-256 is `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`; PE32 image base is `0x00400000`. The exact-build function index records `FUN_005db790` at `0x005DB790`, size 221 bytes in `.text`.
- The read-only decompilation cache records build `10256413` and the exact executable SHA above. Pseudocode SHA-256: `A88088CFE5EB3FEAF3C6E8243D00A3DF687F92ABDDD847EBCCE66994574E4940`. Raw `.text` range SHA-256: `28C883A2327527FB4CB896FB0B370976FE0B5B055D90B80522B8B8249CAC3387`.
- Three exact EXP-0139 edges target the body: `DishonoredAnimNodeSeq.PlayAnim`, `DisAnimNodeSeqPlayer.PlayAnim`, and `DishonoredAnimNodeSeqAttack.PlayAnim`.
- All three exports are `NativeFlag=true`, `NativeToken=0`, script size 40, and declare `native function PlayAnim(optional bool _bLoop = false, optional float _fInRate = 1.0000000, optional float _fStartTime = 0.0000000);`. Their UELib JSONL rows are 154, 155, and 401, all in source SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`.
- The three class `UClass.Super` paths converge at `Class'Engine.AnimNodeSequence'`. `DisAnimNodeSeqPlayer` and `DishonoredAnimNodeSeqAttack` pass through `Class'DishonoredGame.DishonoredAnimNodeSeq'`; that class also has `AnimNodeSequence` as its direct Super. The relation catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- The body initializes the first local to zero, the second to `DAT_011F1340`, and the third to zero before their respective decoder calls. The raw `.rdata` bytes at `0x011F1340` are `00 00 80 3F`, which decode as IEEE-754 `1.0`.
- The body clears bit `0x02` in the dword at `DAT_0140A948` before each of the three decoder calls. Its purpose and state ownership are not identified here.
- The body normalizes the first decoded dword to 0/1, retains the other two decoded dwords, and passes the three values to the receiver's indirect call at displacement `+0x134`. The exports declare those parameters as bool/float/float in the same order.
- The target was absent from the EXP-0151 overlay. This addition creates one L1 review only; it adds no confirmed semantic claim, L3 dataflow edge, or runtime record.

## Interpretation and claim limits

- **Observed:** three exact class-table edges share one indexed native/token-zero target. Their declarations and source metadata match exactly.
- **Observed:** all three class Super paths converge on `AnimNodeSequence`.
- **Observed:** the adapter initializes local storage to 0, raw float constant 1.0, and 0 before three decoder calls; it then passes the decoded values to unresolved receiver displacement `+0x134`.
- **Inferred, limited:** `0x005DB790` is a shared `PlayAnim` native-exec adapter candidate for the three exports. Exact table/name/export joins, matching signatures, and body flow support the grouping.
- **Unknown:** the receiver virtual method, the meaning of `DAT_0140A948`, how omitted optional parameters are represented or consumed at runtime, playback effects, and runtime reachability.
- **Not established:** matching initial local values to declaration defaults does not prove the defaults are used when arguments are omitted; class ancestry and static dispatch do not establish a runtime playback result.

## Reproduction and limitations

1. Rebuild the EXP-0139 join and select its three rows targeting `0x005DB790`.
2. Resolve the 221-byte function in `research/executable/functions.csv`; verify cache build ID and executable SHA.
3. Map the function and `0x011F1340` into the exact executable sections using `RVA = VA - 0x00400000`; verify the code hash and the four constant bytes.
4. Inspect decoder order, the `DAT_0140A948` bit-mask operations, and the call through `+0x134` in read-only decompilation/raw disassembly.
5. Trace the three class paths in EXP-0071's UClass inheritance catalog; verify the cumulative overlay contains 44 unique addresses and includes `005DB790`.

The class relations and export declarations derive from the same UELib corpus. Static code and initializer bytes do not establish optional-argument runtime behavior or animation playback. No game launch or runtime experiment was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior animation adapter review: [EXP-0151](EXP-0151-animnode-set-blend-target-adapter.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
