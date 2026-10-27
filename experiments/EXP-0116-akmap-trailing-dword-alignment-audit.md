---
id: EXP-0116
title: AKMAP trailing DWORD alignment and candidate triplet check
experiment_status: done
claim_status: observed
build: "10256413"
question: Do the trailing AKMAP DWORDs support a consistent 12-byte grouping whose raw values can be directly labeled through the EXP-0115 local string catalogs?
---

# EXP-0116 — AKMAP trailing DWORD alignment and candidate triplet check

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: after the candidate NUL-separated string region established in EXP-0115, read the remaining bytes as little-endian DWORDs; preserve the first four values separately; test a 12-byte grouping hypothesis on remaining DWORDs; count first/third-field equality and values that fall within each file's local string-count range.
- Exclusions: no assignment of field meanings, no claim that an in-range DWORD is a string index, no runtime dependency or selection claim, and no changes to game data.
- Durable outputs: [per-file alignment census](../research/builds/BUILD-STEAM-10256413/akmap-tail-structure-census.csv), [raw-pattern summary](../research/builds/BUILD-STEAM-10256413/akmap-tail-structure-summary.json), and [reproduction tool](../tools/akmap_tail_structure_audit.py).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify build 10256413 and executable SHA-256.
2. Verify all four AKMAP file sizes/hashes against the saved manifest and locate the EXP-0115 candidate string-region end.
3. Decode only little-endian DWORD values. Separate the first four post-string DWORDs, then measure the remainder under a candidate three-DWORD grouping without assigning structure semantics.
4. Compare candidate group columns only to arithmetic properties (first equals third; value is less than local string count). Inspect the same numeric positions in each local token list to test whether the apparent indices are stable across files.
5. Run `python tools/akmap_tail_structure_audit.py` to regenerate outputs.

## Observations

- All four trailing regions are DWORD-aligned. After the first four raw DWORDs, candidate three-DWORD grouping yields 2,592 groups plus one DWORD remainder in base and DLC07, 893 complete groups in DLC05, and 1,558 complete groups in DLC06.
- Under this candidate grouping, field 0 equals field 2 in 163/2,592 base/DLC07 groups, 62/893 DLC05 groups, and 102/1,558 DLC06 groups (about 6.3–6.9%). This equality is not consistent across most candidate groups.
- Counts of candidate-group values below each file's local string count are: base/DLC07 `[226,199,237]` of 2,592 groups by column; DLC05 `[17,8,16]` of 893; DLC06 `[49,42,58]` of 1,558. Most values in each column exceed the local token count; the range test alone does not identify string references.
- The first candidate group is `[19,310,19]` in all four files. Local token index 19 is `BANK_AI_RAT` in each file; token index 310 is `BANK_DLC06_AI_WHALE` in base/DLC06/DLC07 but `WWISEDEFAULTBANK_WWISEGLOBAL` in DLC05. The repeated integer therefore does not identify one globally stable token across all four local catalogs.
- Base and DLC07 have identical hashes and therefore identical measured tail patterns. The first four post-string DWORDs are `[12,160,0,0]` for base/DLC07, `[12,61,0,0]` for DLC05, and `[12,100,0,0]` for DLC06.

## Interpretation and claim limits

- **Observed:** arithmetic grouping into 12-byte candidates is complete for two files and leaves a one-DWORD remainder in the other two; first/third equality is sparse, and raw numeric values do not consistently fall within the local string count. This does not provide enough evidence to label the candidate groups as a universal three-field record schema or to treat their values as local string indices.
- **Unknown:** the actual record boundaries, field types, semantics of the first four DWORDs, whether values reference a global/shared name pool, and whether any entries encode dependencies or runtime selection.
- **Limit:** this is a raw DWORD alignment audit over four files, not a format decoder. The candidate grouping is a diagnostic lens only; other structures could explain the same byte patterns.

## Reproduction

```powershell
python tools/akmap_tail_structure_audit.py `
  --game-root "Dishonored RHCP" `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --output research/builds/BUILD-STEAM-10256413/akmap-tail-structure-census.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/akmap-tail-structure-summary.json
```

## Links

- [EXP-0115 AKMAP string and basename catalog](EXP-0115-akmap-string-and-resource-name-catalog.md)
- [EXP-0064 non-UPK resource header census](EXP-0064-non-upk-resource-header-signatures.md)
- [Candidate audit tool](../tools/akmap_tail_structure_audit.py)
