---
id: EXP-0117
title: AKMAP trailing DWORD string-pool offset audit
experiment_status: done
claim_status: mixed
build: "10256413"
question: Do the candidate 12-byte AKMAP groups contain DWORD values that address the bounded printable string region?
---

# EXP-0117 — AKMAP trailing DWORD string-pool offset audit

- Date: 2026-10-27 (Europe/Kiev).
- Build context: Steam app 217980, build 10256413; executable SHA-256 `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`, matching [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md).
- Scope: test the EXP-0116 candidate groups by treating each DWORD as a byte offset relative to byte 8, the start of the EXP-0115 bounded string region; record bounds, exact NUL-token starts, printable suffixes, and ungrouped trailing DWORDs.
- Exclusions: no field names or row semantics, no claim that a suffix is a full resource name, no runtime selection/dependency claim, and no independent confirmation of the 12-byte record boundary.
- Durable outputs: [per-field offset and decoded-suffix catalog](../research/builds/BUILD-STEAM-10256413/akmap-string-offset-audit.csv), [per-file summary](../research/builds/BUILD-STEAM-10256413/akmap-string-offset-summary.json), and [reproduction tool](../tools/akmap_string_offset_audit.py).

## Procedure

1. Re-read `AGENTS.md`, research status, Blink activation graph, and build record; verify build 10256413 and its EXE SHA-256.
2. Verify all four AKMAP files against the saved install manifest. Use the EXP-0115 string span `[8, field_04 + 8)` and the candidate 12-byte groups after the first four post-string DWORDs measured in EXP-0116.
3. Interpret each candidate DWORD as an offset from file byte 8. Check whether the address falls inside the string span; record whether it is at a NUL-delimited token start or inside a token and preserve the NUL-terminated printable suffix.
4. Audit the candidate-group remainder separately. Compare raw header DWORD 1 with the number of distinct string values that exactly match manifest `.upk` basenames; retain this as a numeric equality only.
5. Run `python tools/akmap_string_offset_audit.py` to regenerate both catalogs and recheck build identity, file hashes, and denominators.

## Observations

- All 22,905 DWORD values across the EXP-0116 candidate groups fall within the corresponding bounded string-region byte span when interpreted as offsets relative to byte 8. Of those, 22,877 point to a nonempty printable NUL-terminated suffix and 28 point at a NUL byte.
- For the middle field of each candidate group, the offset equals an exact token start in 2,591/2,592 base groups, 892/893 DLC05 groups, 1,557/1,558 DLC06 groups, and 2,591/2,592 DLC07 groups. The other middle-field values also fall in bounds and decode to printable suffixes.
- For each outer field, exact token-start counts are 2,438/2,592 (base and DLC07), 837/893 (DLC05), and 1,461/1,558 (DLC06). Other in-bounds values decode to printable suffixes, often beginning partway through a token; the catalog preserves the suffix instead of labeling it as the full token.
- Base and DLC07 each have one DWORD left after the candidate groups: `3553`. Under the same offset interpretation it points to the exact token start at file offset `3561`, value `BK_70D947D44D90C9FAF55C35A9554EA8A8`. DLC05 and DLC06 have no trailing DWORD remainder.
- Raw header DWORD 1 is `160`, `61`, and `100` for base/DLC07, DLC05, and DLC06 respectively. These equal the respective counts of distinct exact `.upk` basename string matches recorded in EXP-0115; the semantic relationship is unknown.
- Base and DLC07 have identical AKMAP hashes, so their matching measurements are duplicate-file observations.

## Interpretation and claim limits

- **Observed:** all candidate fields are addressable within the bounded string span under one consistent byte-8-relative interpretation; almost all middle-field values land exactly on token starts, and the remaining fields still decode to printable NUL-terminated suffixes or an empty slot.
- **Inferred, bounded:** the measurements support interpreting the candidate 12-byte groups as three string-pool-relative offsets. The agreement is strong across all four files, but the record boundary and meanings of the three positions are not independently decoded.
- **Observed, unexplained:** header DWORD 1 equals the exact `.upk` basename-match count in each file. This equality does not establish that the value counts UPK references.
- **Unknown:** why some offsets point inside tokens, what the three positions represent, whether the leftover base/DLC07 DWORD belongs to another structure, and whether any candidate name is selected or loaded at runtime.
- **Limit:** this is a byte-level addressability audit of four AKMAP files from one recorded build. Text offsets do not prove dependency semantics or runtime behavior.

## Reproduction

```powershell
python tools/akmap_string_offset_audit.py `
  --game-root "Dishonored RHCP" `
  --manifest research/builds/BUILD-STEAM-10256413/files.csv `
  --build-record research/builds/BUILD-STEAM-10256413/build.md `
  --output research/builds/BUILD-STEAM-10256413/akmap-string-offset-audit.csv `
  --summary-output research/builds/BUILD-STEAM-10256413/akmap-string-offset-summary.json
```

## Links

- [EXP-0115 AKMAP string and basename catalog](EXP-0115-akmap-string-and-resource-name-catalog.md)
- [EXP-0116 trailing DWORD alignment audit](EXP-0116-akmap-trailing-dword-alignment-audit.md)
- [Build inventory](../research/builds/BUILD-STEAM-10256413/files.csv)
- [Offset audit tool](../tools/akmap_string_offset_audit.py)
