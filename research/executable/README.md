# Static analysis artifacts

Canonical read-only static MCP server: [`mcp_servers/static/server.py`](../../mcp_servers/static/server.py).

`mcp/server.py` in this folder is only a compatibility launcher for older configs.

## Contents

- `functions.csv` — exported Ghidra function index for build 10256413
- `ghidra-project/` — local Ghidra project (ignored analysis DB / locks)
- `scripts/` — headless helper scripts (`DecompileFunction.java`, export triage)
- `evidence/native-token-dispatch-catalog.csv` — partial UELib NativeToken → exact-build `.data` name-pointer / adjacent `.text` address join (EXP-0066)
- `evidence/function-triage/` — one row per exact-build internal function with conservative name-label bucket, direct-call role, incoming data-xref context, and explicit unknown/unreviewed status (EXP-0072)
- `evidence/EXP-0073-wwise-function-probes.csv` — selected exact-address decompiler observations for four `AK::SoundEngine` functions (EXP-0073)

Executable SHA-256: `66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E`.

Headless runs use `-noanalysis -readOnly`. Prefer workspace Python under `.venv` when launching the MCP server. Path defaults: [`mcp_servers/_paths.py`](../../mcp_servers/_paths.py).

Reproduce the native-token join from the UELib JSONL corpus with [`native_token_dispatch_catalog.py`](../../tools/native_token_dispatch_catalog.py). It invokes [`ExportNativeTokenStringRefs.java`](scripts/ExportNativeTokenStringRefs.java) through read-only Ghidra headless mode and cross-checks raw PE pointers against the exact-build function index. The catalog is a partial static join; it does not establish token-table consumption at runtime.

Reproduce the internal function triage with [`function_subsystem_triage.py`](../../tools/function_subsystem_triage.py). It covers the 72,437-row function denominator for accounting, but only 439 rows receive narrow symbol-name candidates and none are semantically reviewed by that pass; see [EXP-0072](../../experiments/EXP-0072-exact-build-internal-function-subsystem-triage.md).

EXP-0073 probes four audio API-like functions with the exact-build decompiler. The namespaced results strengthen those addresses only and do not promote the remaining 181 audio-like labels or establish runtime use.

EXP-0076 joins the 135 class-key/pointer-symbol pairs visible in `FUN_00A0DBF0` to exact class paths in the derived all-install UELib catalog. Reproduce with [`native_class_table_uelib_join.py`](../../tools/native_class_table_uelib_join.py). This exact-name join does not establish native table layout, dispatch, or runtime use.

EXP-0077 parses HIRC structures from all 503 PCK banks and `Init.bnk` with a pinned wwiser checkout. Reproduce with [`wwise_bank_hirc_census.py`](../../tools/wwise_bank_hirc_census.py). It generates bank/object/edge/media CSVs; these are parser-derived IDs and relations, not runtime event evidence. Forty Sound media IDs have no exact DIDX/WEM catalog match.

EXP-0078 adds same-bank `ulChildID` edges and event/action/Sound/media paths through seven parsed container types. The base EXP-0077 edge catalog remains separate from the extended container-child catalog; see `wwise-hirc-edges-with-container-children.csv` and `wwise-event-hirc-sound-paths.csv` in the build directory.

EXP-0079 compares locally unresolved action target IDs with all parsed HIRC object IDs across the 503 PCK banks and `Init.bnk`. EXP-0080 audits zero-valued `ulTargetID` fields and corrects the denominator: 1,007 zero values are excluded from 618 nonzero unresolved fields, of which 526 have exact-ID candidates and 92 have none. Exact matches are written to `wwise-action-target-global-id-candidates.csv`; repeated IDs and runtime semantics remain explicitly unresolved.

EXP-0081 joins the 40 Sound media IDs without same-bank DIDX or catalog WEM matches to the EXP-0078 event path catalog. All 40 occur in 79 same-bank event paths; this establishes graph connectivity only, not media payload validity or runtime invocation. Reproduce with [`wwise_unmatched_media_paths.py`](../../tools/wwise_unmatched_media_paths.py); output is in the exact-build catalog directory.

EXP-0106–0108 record eight selected `AK::SoundEngine` wrapper families, the shared critical-section-protected buffer, and a static consumer that reads length/discriminator fields and dispatches matching cases. This is not runtime behavior evidence. See [EXP-0108](../../experiments/EXP-0108-audio-record-consumer-opcode-matches.md) and its [producer/consumer case map](evidence/EXP-0108-audio-record-consumer-opcode-map.csv).

EXP-0109 reconciles 50 direct writer callsite edges from 48 functions with all 37 visible dispatcher cases; the case-0 RenderAudio marker is a separate route. Reproduce the cohort and coverage tables with [`audio_record_producer_cohort.py`](../../tools/audio_record_producer_cohort.py) after generating the local ignored decompile dump with [`DecompileAddressBatch.java`](scripts/DecompileAddressBatch.java). Static accounting does not prove runtime reachability or sound output. The knowledge dossier returns only 30 callers here; use the exact-build SQLite edge table for this denominator. See [EXP-0109](../../experiments/EXP-0109-audio-record-dispatch-case-coverage.md).

EXP-0110 decompiles all 181 EXP-0072 audio API name candidates in one read-only Ghidra batch and records exact-name AK namespace signatures and direct callgraph edges. 181 signature/name pairs match across eight paths: `SoundEngine`, `SoundEngine::Query`, `MemoryMgr`, `StreamMgr`, `SoundEngine::DynamicSequence`, `MotionEngine`, `SoundEngine::DynamicDialogue`, and `MusicEngine`. See the [per-function catalog](evidence/EXP-0110-audio-api-candidate-cohort.csv), [summary](evidence/EXP-0110-audio-api-candidate-cohort.json), and [reproduction tool](../../tools/audio_api_candidate_cohort.py). This does not prove runtime reachability or vendor provenance.

EXP-0111 decompiles the 126 distinct indexed internal callees (401 direct edges) from the 181 audio API name candidates. 29 callee signatures exactly match a qualified owner/name; 96 targets remain in the EXP-0072 `unknown` triage bucket. Six visible helper operations are recorded with pseudocode limits. See the [callee catalog](evidence/EXP-0111-audio-api-direct-callee-cohort.csv), [summary](evidence/EXP-0111-audio-api-direct-callee-cohort.json), and [reproduction tool](../../tools/audio_api_direct_callee_cohort.py). A call from an API candidate does not assign subsystem ownership or establish runtime use.
