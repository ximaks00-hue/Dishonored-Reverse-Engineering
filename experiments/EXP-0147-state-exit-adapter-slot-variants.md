---
id: EXP-0147
title: Byte-matched state-exit adapters with adjacent virtual slots
experiment_status: done
claim_status: mixed
build: "10256413"
question: "Are the adjacent state-exit callback targets at 0x009E47A0 and 0x009E4A20 the same exact-build body except for their receiver virtual-call displacement?"
---

# EXP-0147 — Byte-matched state-exit adapters with adjacent virtual slots

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: compare the already reviewed four-edge target `0x009E47A0` with the three-edge target `0x009E4A20`; inspect exact exports, class/function Super relations, decompiler bodies, and raw indexed code bytes.
- Exclusions: no identity assigned to virtual slots `+0x1A8` or `+0x1AC`; no semantic interpretation of callback suffixes, runtime dispatch, or gameplay effect; no UFunction override relation inferred from class inheritance.
- Inputs: EXP-0139 class-table/UELib join and target catalog; EXP-0071 inheritance catalog; exact-build function index and read-only decompiler caches.
- Durable outputs: [one-row manual review addition](../research/executable/evidence/function-triage/manual-review-overlay-EXP-0147.csv), [37-row cumulative review overlay](../research/executable/evidence/function-triage/manual-review-overlay-cumulative-EXP-0147.csv), and [summary](../research/executable/evidence/function-triage/manual-review-overlay-summary-EXP-0147.json).

## Procedure

1. Re-read research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Resolve the three EXP-0139 edges to `0x009E4A20` and the four existing EXP-0146 edges to `0x009E47A0`; compare NativeFlag, NativeToken, script size, declarations, and source rows.
3. Resolve both indexed 96-byte ranges and verify both decompiler cache records match the exact build/hash.
4. Read both raw `.text` ranges by VA-to-RVA mapping, compare each byte, and disassemble the differing instruction neighborhood with Capstone 5.0.7.
5. Join all seven class paths to `UClass.Super` chains and each exact method path separately to `UFunction.Super` rows. Keep the two relation types separate.
6. Add only the previously unreviewed `0x009E4A20` address as an L1 role candidate.

## Observations

- Both addresses are exact-build indexed starts, each 96 bytes in `.text`: `FUN_009e47a0` at `0x009E47A0` and `FUN_009e4a20` at `0x009E4A20`. Their cached pseudocode SHA-256 values are `845ED930CBE38B048952084345E2F2C9C7BB4557088622789BAB058395E61AEE` and `EE64E01C0D334B491B5DDC598CA7B4FA2F30C647A878301C0F82F773882F6CEE`; both cache records state build `10256413` and the exact executable SHA above.
- Four EXP-0139 edges target `0x009E47A0`; three target `0x009E4A20`. All seven exports are `NativeFlag=true`, `NativeToken=0`, script size 7, and declare one `DishonoredNativeState` parameter. Method names differ among `RequestStateExitCallback_GenericAction`, `RequestStateExitCallback_TakeActorPosition`, `RequestStateExitCallback_TakePosition`, `RequestStateExitCallback_LieInWait`, and `RequestStateExitCallback_TentacleAttack`.
- The four first-target UELib JSONL rows are 210, 237, 240, and 914; the three second-target rows are 157, 239, and 952. All are from the source file with SHA-256 `09F41841F403B8A1CAE11D2C80E075E4563454C5DC295DA6A81D309156DBF1D4`; EXP-0139 preserves package source/hash provenance.
- All seven class `Super` chains converge on `Class'DishonoredGame.DishonoredAIBehavior'`. Six class paths pass through `Class'DishonoredGame.DisAIBehaviorWithDesires'`; `DisDLC06BehaviorSummonedAssassinIdle` is a direct child. The EXP-0071 catalog contains no `UFunction.Super` row for any of the seven exact callback methods. The catalog SHA-256 is `B00ADE7AC2321C38FFD3A37EAF494E4E41DCC061EEDBACCF853E63BFB0562D0B`.
- After normalizing function labels and PC literals to function-relative offsets, the two pseudocodes differ only at the final virtual-call displacement: `+0x1A8` for `0x009E47A0`, `+0x1AC` for `0x009E4A20`.
- The raw `.text` range SHA-256 values are `51463C62F1E938436D868F06CA5C3318D707EB5C6E8F2FFA0881718CAF0B784B` (`0x009E47A0`) and `2B29CFB0418BE8E1E079CB9D3BEB0DE5076D21099C247858BA16BD5129FA1C08` (`0x009E4A20`). A bytewise comparison finds exactly one differing offset, `0x4F`, with byte values `0xA8` and `0xAC`; the other 95 of 96 bytes are equal.
- Capstone decodes the changed instruction operands as `mov edx, dword ptr [eax + 0x1a8]` at `0x009E47ED` and `mov edx, dword ptr [eax + 0x1ac]` at `0x009E4A6D`. Each function decodes one frame value, conditionally handles an `A` marker, and passes the decoded dword to the selected receiver-vtable entry.
- `0x009E4A20` was subsystem-unknown and absent from the EXP-0146 manual overlay. The new row adds one L1 review; the previously reviewed `0x009E47A0` remains unchanged. Neither receives a confirmed semantic claim, inter-function L3 edge, or runtime record.

## Interpretation and claim limits

- **Observed:** seven exact class-table edges across two indexed targets share the same native/token-zero, one-object signature family. Their class Super paths converge at `DishonoredAIBehavior`; no exact target-method UFunction.Super rows appear in the catalog.
- **Observed:** the two 96-byte machine-code bodies are byte-identical except for one byte in the receiver vtable displacement operand, changing `+0x1A8` to `+0x1AC`. Both pass the same decoded dword as the explicit virtual-call argument.
- **Inferred, limited:** the two targets are adjacent-slot native-exec adapter candidates for the seven exact callback exports. Shared byte shape, matching declarations, and table joins support the adapter grouping.
- **Unknown:** the concrete methods and receiver vtables behind either slot, the meaning of each callback suffix, runtime reachability, and behavior.
- **Not established:** the class-level common ancestor does not prove one common callback UFunction, and byte identity except for a slot operand does not prove shared gameplay semantics.

## Reproduction and limitations

1. Rebuild EXP-0139 and select the seven raw table rows for `0x009E47A0` and `0x009E4A20`.
2. Resolve both entries in the 10256413 function index; verify each decompiler cache build ID and executable SHA.
3. Read each 96-byte range from the exact EXE `.text` section, verify both recorded hashes, and compare all offsets. Disassemble offsets `0x4A`–`0x55` with Capstone 5.0.7.
4. Rebuild EXP-0071's catalog and trace the seven class `Super` chains; query the exact callback function paths separately in the `UFunction.Super` relation rows.
5. Verify the cumulative review overlay contains 37 unique indexed addresses and includes `009E4A20`.

The UELib relations and function export joins derive from a common parser corpus, not independent runtimes or parsers. Static byte/code evidence does not demonstrate table use in a running game. No game launch or runtime test was performed.

## Links

- Build: [Steam build 10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Parent class-table join: [EXP-0139](EXP-0139-native-class-table-zero-token-handler-join.md)
- UELib relation catalogs: [EXP-0071](EXP-0071-all-install-uelib-object-class-inheritance-reference-catalogs.md)
- Prior callback target review: [EXP-0146](EXP-0146-shared-state-exit-callback-thunk.md)
- Function triage baseline: [EXP-0072](EXP-0072-exact-build-internal-function-subsystem-triage.md)
