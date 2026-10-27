---
id: EXP-0002
title: Core package header byte triage
experiment_status: done
claim_status: observed
build: "10256413"
question: "What are the opening bytes / package-tag shape of DishonoredGame.upk and Core.upk?"
---
# EXP-0002 — Core package header byte triage

- Status: observed; structural parse pending
- Build: [BUILD-STEAM-10256413](../research/builds/BUILD-STEAM-10256413/build.md)
- Question: Can the configured package tooling parse a central game package, and what bytes are directly observable at the file start?
- Tools: PowerShell `Format-Hex`; local file manifest; Dishonored asset-index and UModel tools.

## Procedure

1. Select `DishonoredGame/CookedPCConsole/DishonoredGame.upk` from the local manifest.
2. Record its size and SHA-256 and display its first 64 bytes.
3. Repeat for `DishonoredGame/CookedPCConsole/Core.upk`.
4. Request `get_package_info` and `list_package_objects` for manifest-listed package paths.

## Observations

- `DishonoredGame.upk`: 5,928,252 bytes; SHA-256 `EC64BD36BE12D7063199CF2722A2B8F280100F1ED3F3C63404AC34980D7141E2`.
- `Core.upk`: 45,534 bytes; SHA-256 `F432ACD67890BB7B02D355543E2EBA2830B0FFDE5CC4F2416312769BB49981C9`.
- Both begin `C1 83 2A 9E 21 03 1E 00`.
- The asset index returns `DishonoredGame.upk` as a manifest-listed package. Initial calls through the Assets MCP package operations return a generic execution error; direct UModel CLI parsing was successful (see EXP-0004).

## Interpretation and limits

The bytes are recorded without assigning field meanings. A later direct UModel CLI invocation parsed the package successfully and reported version `801/30`. In the main package, the two 16-bit little-endian values following the 4-byte tag decode to `801` and `30`, matching the parser report. This supports, but does not independently specify, that field interpretation. See [EXP-0004](EXP-0004-umodel-blink-triage.md) for the follow-up. The initial error was a connector limitation, not evidence that the format is unsupported.

## Reproduction

```powershell
Format-Hex -LiteralPath 'Dishonored RHCP\DishonoredGame\CookedPCConsole\DishonoredGame.upk' -Count 64
Format-Hex -LiteralPath 'Dishonored RHCP\DishonoredGame\CookedPCConsole\Core.upk' -Count 64
```

The configured package calls may still be retried after diagnosing the connector error.
