# REV-0011 — EXP-0039–0041 progress audit

Date: 2026-10-26. Source: user-supplied descriptions of EXP-0039, EXP-0040, EXP-0041. **Primary local E: source files, Ghidra binary/project and script output were not available to this GitHub connector. This review does not claim independent reanalysis.**

## Findings

- `FUN_00BFAE60` and `FUN_00BFAFD0` call `FUN_00BF8C00` on their same receiver object. The helper reportedly computes/validates a candidate point and writes three scalar coordinates to receiver `+0x60/+0x64/+0x68`.
- `FUN_00BFC990` reads these same object-relative offsets as stored Blink destination (per earlier EXP-0030). **This is a layout coincidence with meaningful dataflow potential, but there is no verified receiver identity between producer and consumer.**
- Blink vtable at `0x01168698` has a Ghidra symbol and two constructor xrefs. Nearby proposed starts around `FUN_00BFAE60` and `FUN_00BF8DD0` lack analogous constructor references. No owner attribution of their virtual tables follows from adjacency.
- Independently clarified by EXP-0041 in the user's read-only Ghidra: `72,437` internal + `488` external = `72,925` total functions. User reports an exact set match between `functions.csv` and non-external function addresses. This **resolves the earlier count discrepancy at the report-evidence level**, but primary export is not mirrored here.
- Experiment metadata validation reports 41 experiments and 0 errors/warnings. This is a locally reported test, not rerun on current GitHub tree.

## Why the target producer→consumer join is not yet proven

A matching `+0x60/+0x64/+0x68` triple can occur in different class types, inherited subobjects or memory layouts. Show receiver provenance (constructor/vptr, allocation, how `this` is passed) and the concrete runtime call chain. Even if the *same class* is proven, **same instance and order of execution** still require further evidence. A position candidate is not the authoritative Pawn Location: preserve separation from earlier conditional write through `FUN_006539C0`.

## Next experiment

**EXP-0042** should establish producer `FUN_00BF8C00` object's owner and whether the same instance reaches consumer `FUN_00BFC990`: find direct/virtual callers, record vptr installation, exact pointer chains, normalize `this` including any adjusted secondary interface pointer, and document possible aliasing. Only then link computed candidate to `FUN_006539C0` if concrete flow exists.

## Governance and source of truth

The user's local repository now reportedly contains 41 EXP records, a knowledge DB, MCP v2 gateway and new Ghidra exporters. The connected GitHub branch here is still an older research scaffold and must not be treated as source of truth for local EXP-0039–0041. Do not overwrite the user's files with derivative summaries. Retain strict separate claim/evidence statuses; do not treat no xrefs as conclusive negative evidence.
