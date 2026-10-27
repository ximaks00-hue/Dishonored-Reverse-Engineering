---
id: EXP-0164
title: Blink PDB-donor symbol candidate crosswalk to the retail function index
experiment_status: done
claim_status: inferred
build: "10256413"
question: "Can Blink method signatures attributed to a 2012 PDB be mapped to exact retail addresses and the local Ghidra index with their transfer quality preserved?"
---

# EXP-0164 — Blink PDB-donor symbol candidate crosswalk

- Date: 2026-10-27 (Europe/Kiev).
- Build: Steam app `217980`, x86 build `10256413`; EXE SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E` from the registered exact-build function index.
- Scope: 38 PDB-attributed Blink method comments in an import-generated source stub; 2012 RVA → 2013 RVA transfer through the external snapshot's `match_2012_2013.csv`; exact-start and body-interval comparison against the local 72,437-function index.
- Exclusions: no Ghidra renaming; no assumption that the stub contains original implementation; no decompilation, owner execution, runtime behavior, or gameplay reachability claim.
- Tools: Python 3.12; local `research/executable/functions.csv`; external community snapshot stub and 2012→2013 match export; [crosswalk script](../tools/audit_external_blink_symbol_candidates.py).
- Durable outputs: [38-row crosswalk](../research/executable/evidence/EXP-0164-blink-pdb-symbol-crosswalk.csv) and [source hashes/counts/limits](../research/executable/evidence/EXP-0164-blink-pdb-symbol-crosswalk.json).

## Procedure

1. Read the PDB-attributed function comments in `dishonoredactivepowercomponent_blink.cpp`. The file itself states it is an import-generated stub and the listed source RVAs are from the 2012 PDB.
2. Join each 2012 RVA exactly to `match_2012_2013.csv`; retain the matcher method, ratio, and both sizes.
3. Add image base `0x00400000` to non-empty 2013 RVAs and compare the resulting VA to the exact-build Ghidra function index. If no entry exists, check whether the VA lies inside a recorded indexed function body.
4. Preserve all candidate and unmatched rows; do not rename or edit the function index.

## Observations

- The stub lists 38 Blink-related function signatures. The 2012→2013 match export has a non-empty 2013 RVA for 30; eight are marked unmatched there.
- Of the 30 transferred addresses, 29 are exact entries in the local retail function index. All 29 local function sizes equal the 2013 exported sizes. One additional transferred address, `0x00BE7570` (`CanBeCanceled_Derived` in the 2012 PDB comment), is absent both as an indexed entry and from every indexed body interval. The external matcher row gives it method `order`, ratio `1.000`, and equal 12-byte sizes; the function index remains unchanged.
- The 30 transferred rows use methods: `bytes` 5, `callee` 4, `neighbours` 15, `order` 3, `string` 2, and `vtable` 1. Eight `neighbours`/`vtable` rows have ratio below 0.9. The row-level details remain in the CSV; this experiment does not flatten them into a single confidence score.
- The mapped names align with existing address-level Blink investigations, including `OwnerCanBlink` → `FUN_00BE8D60`, `MoveActorToPos` → `FUN_00BECDF0`, `LimitDirection` → `FUN_00BF52E0`, `SetupTargetFromPlayer` → `FUN_00BF5520`, `Tick_Move` → `FUN_00BFC160`, `Tick_Warmup` → `FUN_00BFA270`, `Tick` → `FUN_00BFC5D0`, and `Execute` → `FUN_00BFC020`. This is a cross-source naming overlay, not a substitute for the raw-instruction evidence already recorded in EXP-0022 through EXP-0051.
- Eight names without a 2013 match include `OnPhysModeChanged`, `GetBackupDistance`, `DisableEffects`, `EndBlink`, `BeginWarmup`, and `Blink`; “unmatched” means the donor matcher did not produce a 2013 row, not that retail code is proven absent.
- The external source snapshot has no `.git` metadata. The stub, match CSV, local function index hashes, and limitations are recorded in the JSON sidecar.

## Interpretation and claim limits

- **Inferred, candidate symbol associations:** for the 30 transferred rows, the 2012 PDB method signature is a candidate label for the mapped 2013 address at the recorded method/ratio. The 29 exact local starts and equal sizes strengthen address correspondence; methods with `bytes` and ratio `1.000` have the strongest transfer evidence in this set.
- **Confirmed, index coverage result:** the local exact-build index contains 29 of those 30 transferred function starts. `0x00BE7570` is not indexed or inside an indexed body under the recorded intervals; this does not prove it is a valid function boundary.
- **Unknown:** implementation semantics beyond the existing EXP raw-code observations, whether any method executes in a particular session, runtime behavior, and the identity of unmatched retail counterparts (if any).
- **Limit:** PDB names originate in the 2012 donor build and are transferred by an external similarity matcher. The community project's output is not original game source; address/name candidates must remain separate from confirmed function semantics.

## Reproduction

```powershell
python tools\audit_external_blink_symbol_candidates.py `
  --stub <path-to-dishonoredactivepowercomponent_blink.cpp> `
  --matches <path-to-match_2012_2013.csv> `
  --local-index research\executable\functions.csv `
  --output-csv research\executable\evidence\EXP-0164-blink-pdb-symbol-crosswalk.csv `
  --output-json research\executable\evidence\EXP-0164-blink-pdb-symbol-crosswalk.json
```

The script reports status counts and records source SHA-256 values. It does not modify Ghidra data, EXP evidence, or source files.

## Links

- Blink static evidence graph: [activation graph](../docs/gameplay/blink/activation-graph.md)
- Existing address-level Blink investigations: EXP-0022, EXP-0024, EXP-0030, EXP-0045
- External D: audit and provenance: [external-drive audit](../docs/external-drive-audit.md)
- Crosswalk script: [audit_external_blink_symbol_candidates.py](../tools/audit_external_blink_symbol_candidates.py)
