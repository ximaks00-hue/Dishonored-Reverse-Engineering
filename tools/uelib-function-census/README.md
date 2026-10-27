# UELib function census

Read-only helper to decompress selected UPKs into an ignored output directory, initialize them with Eliot.UELib 1.13.3, and report function/export/decompiler-output and initialized-object counts as JSON. It never writes to source UPKs.

Run from the repository root in PowerShell:

```powershell
$env:NUGET_PACKAGES = (Join-Path (Get-Location) '.nuget\packages')
dotnet run --project tools\uelib-function-census -- `
  --decompressor tools\ue-package-decompressor\decompress.exe `
  --output-root assets\extracted\uelib-census `
  --emit-decompiled-jsonl `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\Core.upk' `
  'Dishonored RHCP\DishonoredGame\CookedPCConsole\Engine.upk'
```

Each run uses a new timestamped child directory under `--output-root`; package outputs are further separated by argument index and filename. Keep this output under `assets/extracted/` (ignored by Git). The tool records each input's SHA-256, decompressed size, UELib export-table `ClassName` counts, object counts, Native-flag counts, and a text-only non-comment-body-line heuristic. Compare `exportTableFunctionClassNames` with the independently generated UModel object catalog when reconciling labels.

Use `--json-output <path>` to save the complete package result (including `objectTypeCounts`, CLR `objectTypes`, export class-label counts, export-object resolution failures, and diagnostics) under ignored extracted data instead of printing it to the console. This is an API initialization profile: object counts and absence of UELib wrappers do not prove that serialized payloads or exports are absent. In particular, `UnknownObject` means UELib did not produce a more specific wrapper in this run.

Pass `--emit-decompiled-jsonl` to write every exported UFunction's UELib decompiler output to `<package>.functions.jsonl` beside its decompressed copy. Each JSON object includes the source package/hash, object path/name, Native flag, `NativeToken`, operator precedence, script-size field, and decompiled text. `NativeToken` is emitted as UELib's parsed property; a nonzero token and a matching `native(N)` declaration do not by themselves identify an executable handler. The read-only join procedure in [native token dispatch catalog tool](../../tools/native_token_dispatch_catalog.py) checks that separately against exact-build Ghidra string xrefs and raw PE pointers. These are generated decompiler artifacts, not original source; inspect diagnostics and unresolved tokens such as `__NFUN_*` before relying on a body.

`nonNativeWithBodyLines` is only a reproducible triage count. It does not establish complete or correct bytecode decompilation; inspect `diagnostics` and individual decompiler output before making semantic claims. The implementation reads UELib's raw `FunctionFlag` value and applies bit `0x400` as Native for Eliot.UELib 1.13.3.
