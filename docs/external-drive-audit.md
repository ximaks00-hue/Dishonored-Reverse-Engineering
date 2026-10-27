# External D: drive audit

**State: in progress.** This record tracks the read-only audit of `D:\Dishonored` for material that can answer open questions or improve work in this repository. The source drive has not been modified.

## File census

The first complete filesystem pass enumerated and SHA-256 hashed every regular file reachable without following directory symlinks/junctions. It completed with no file read errors:

| Measure | Result |
| --- | ---: |
| Directories visited | 44,000 |
| Regular files hashed | 379,912 |
| Bytes read for SHA-256 | 281,375,587,774 |
| Directory links recorded and not traversed | 33 |
| Exact-content duplicate groups | 38,027 |
| Duplicate copies beyond one per group | 272,928 |

The per-file path, size, extension, timestamps, SHA-256, and scan status are in the local generated SQLite manifest at `build/d-drive-audit/manifest.sqlite3`; aggregate counts are in `build/d-drive-audit/report.json`. These are local audit outputs and are not research evidence by themselves. The scanner refuses to overwrite existing outputs unless `--overwrite` is explicitly supplied; this option replaces the selected database/report. Reproduce the inventory with:

```powershell
python tools/audit_external_tree.py D:\Dishonored `
  --database build/d-drive-audit/manifest.sqlite3 `
  --report build/d-drive-audit/report.json `
  --overwrite
```

The hash pass proves which bytes were present during the scan and detects exact copies among regular files; symbolic-link target strings are recorded separately and excluded from duplicate-byte totals. The traversal is a live filesystem scan, not a point-in-time snapshot, and does not constitute semantic review. Directory links are recorded but not traversed. Text candidates, extracted package data, and binary indexes need separate content review, recorded below as it proceeds.

## Top-level inventory

| Area | Files | Approx. size | Likely relevance |
| --- | ---: | ---: | --- |
| `00_VAULT` | 10,166 | 48.22 GiB | Registered 2012 donor builds, PDBs, archives, and retail baseline manifest |
| `01_REFERENCE` | 8,010 | 1.72 GiB | Community reverse-engineering snapshot and reference SDK/tooling |
| `10_EDITOR_RESTORATION` | 204,262 | 183.86 GiB | Large reconstructed editor/build workspace, task evidence, and generated copies |
| `20_MOD_STUDIO` | 11,320 | 11.65 GiB | Package/mod tooling and related datasets |
| `30_VULKAN_RENDERER` | 134,366 | 12.88 GiB | Renderer implementation, build/deploy files, and generated artifacts |
| `40_BROWSER_PORT` | 9,228 | 2.23 GiB | Independent binary/PDB and porting analysis |
| `50_THIRD_PERSON_MOD` | 2,479 | 0.99 GiB | Dishonored camera research and UE3 package tooling |
| `INVENTORY` | 68 | 0.50 GiB | Build/file inventory and custody records |
| `90_SHARED_TOOLS` | 7 | <0.01 GiB | Shared project utilities |
| Root and `99_INBOX` | 6 | <0.01 GiB | Hub documentation and one untriaged item |

The high duplicate count matters: findings should be deduplicated by hash and traced to their original project/task, rather than counted once per copied workspace. Conversely, a duplicate file's path may encode task provenance and should not be discarded from the manifest.

## High-value evidence already reviewed

### Retail native/function exports

`01_REFERENCE/community/dishonoredrecompiled-main` contains `functions_2013.csv`, `natives_2013.csv`, `match_2012_2013.csv`, and the producer `resources/tools/ida/export_natives.py`. Its local source snapshot has no `.git` metadata, so the commit identity is unavailable. The three selected CSV SHA-256 values and the producer hash are preserved in `research/executable/evidence/EXP-0163-retail-native-crosswalk.json`.

The two non-sentinel selector initializer rows found in EXP-0163 join exactly to the retail exports:

| Index | Target | Export association | 2012→2013 match |
| ---: | ---: | --- | --- |
| `0x180` | `0x006CC1D0` | `AActor::PollSleep` | Byte match, ratio 1.000, 56-byte size in each export |
| `0x181` | `0x0058C820` | `AActor::PollFinishAnim` | Byte match, ratio 1.000, 43-byte size in each export |

The retail native exporter documents extraction from numbered `GRegisterNative` calls and the `GNatives` table. These joins support the static native-binding identification. They do not prove the selector helper's runtime consumers, wrapper execution, or gameplay effects. The project’s 207-row EXP-0066 NativeToken catalog is partial; its absence of these indices is not global evidence.

The full 2013 symbol export has 65,841 function rows. A preliminary exact-VA comparison with the project’s 72,437-row Ghidra index found 56,770 matching starts; 54,382 rows also have equal exported/indexed sizes. The 2012→2013 matcher marks 15,235 matches as `bytes` with ratio 1.000. This suggests a high-value name-candidate overlay for triage, but names must not be applied to the Ghidra index until a reproducible row-level audit handles duplicate/COMDAT names, size differences, match method, and source provenance. The remaining 9,071 retail-export VAs absent from the local index require separate boundary/range analysis.

The import-generated Blink stub `source/Development/Src/DishonoredGame/Src/dishonoredactivepowercomponent_blink.cpp` contains 38 method signatures attributed to the 2012 PDB. EXP-0164 maps 30 through the retail match file; 29 are exact starts in the local index and all 29 exported sizes agree. The signatures align with several existing Blink EXP addresses and provide a focused, quality-labeled method-name overlay. One 12-byte address (`0x00BE7570`) remains outside the function index and should be checked as a boundary candidate. Eight unmatched 2012 signatures are unresolved, not evidence of retail absence. The source stub is explicitly marked as a placeholder for future decompilation, not original implementation.

### Camera and package tooling

`50_THIRD_PERSON_MOD/docs/TP-CAMERA-02-package-command-path.md` and `TP-CAMERA-03-command-to-camera-path.md` contain exact-build RHCP camera/package evidence and carefully scoped unknowns. The package analysis distinguishes the Dishonored-specific `DishonoredPlayerCamera` CDO from generic `GameThirdPersonCamera` defaults. This is a useful warning against transferring generic UE3 camera assumptions into Blink or player-camera claims.

The same project documents a Dishonored-oriented UE3 package parser that handles this build's outer compressed chunks and inner LZO blocks. The notes say the generic UELib pass did not inflate these particular `StoreCompressed` packages correctly. This is a possible parser cross-check for package-level investigations; it does not replace the project’s existing exact-build sources or validate a parser without reproduction.

### Independent package corpus and parser evidence

`20_MOD_STUDIO/repo/docs/evidence/corpus-profiles/corpus-rhcp-904.json` describes 904 packages (470 base + 434 DLC), profile `Dishonored1/801/30`, and names the same RHCP install used by the registered build. A scripted path/size/SHA-256 comparison of all 904 catalog rows with the E-repository build manifest found 903 exact matches and one discrepancy. The row-level output is retained locally at `build/d-drive-audit/dms-package-crosswalk.csv` (SHA-256 `C3FD54A56016B6A48AEFBAC7EFC2592918308864E1B2E0CFE5FADC0B3FB51440`). The discrepant catalog row, `CookedPCConsole/pickups_twk_Keys_SF.upk`, is 41,074 bytes with SHA-256 `F2F68BCF…E70D3233`; DMS DATA-04 evidence records those exact bytes as its **installed/modified** package. The same evidence records pristine SHA-256 `9DA5C888…14C69F31`, which exactly matches the E-repository manifest's 40,098-byte package. Thus the discrepancy is explained by the DMS catalog capturing an intentionally modified runtime-test package, not by a different corpus. All 904 pristine package identities are therefore accounted for: 903 directly from the catalog and the final one from the DATA-04 pristine record. This is a crucial provenance caveat: the DMS package catalog is not uniformly a pristine-build manifest.

The DMS package notes are unusually careful about parser limits: package summaries and chunk descriptors were scanned across all 904 files; the parser claims exact-size LZO decoding only for blocks touched by name/import/export reads, not every payload block. It distinguishes confirmed on-disk framing from the codec hypothesis until decoded bytes and names validate it, and explicitly leaves fully compressed summaries unsupported. This is a strong independent design/review reference for UPK tooling and a candidate source for a read-only parser cross-check. Its runtime writer tests do not transfer as proof for the E project's package parser or runtime claims.

### Gameplay data candidate: key pickup tweak record

DMS `docs/architecture/ObjectPropertyGameplay.md` identifies `pickups_twk_Keys_SF.upk` export 16, `Prison_YardWalkwayKey_twk` (`DisTweaks_Key`), with three serialized Float32 fields and original values: `m_fTravelToUserTime=0.1`, `m_TravelCameraOffset=-50`, `m_fMaxDrawDistance=2000`. It records modified values and an install/restore check, but explicitly leaves the new-game pickup observation as not performed; do not cite the modified values as proven gameplay semantics. Its DATA-04 JSON binds the pristine package to SHA-256 `9DA5C888…14C69F31`, which matches this project's build manifest exactly. The current project already sees the class and these property names in the corpus census (`DisTweaks_Key` field-frequency rows: 80 each) and the object name in two packages (`pickups_twk_Keys_SF.upk` export 16 and `L_Prison_Script.upk` export 9679). This supplies a concrete, build-bound candidate for a future source-of-value/dataflow investigation, with a duplicate package placement to resolve before inferring which object instance is loaded or consumed. Our configured UELib MCP currently refuses this object because the UPK is compressed; the DMS notes describe a parser path that may provide an independent cross-check after its exact input and decoder boundaries are reproduced.

The preserved DMS `artifacts/data04-work/tweak-inventory.json` has 62 editable tagged values from seven base tweak packages, covering 18 objects; nine key objects are present. All nine report the same three key defaults (`0.1`, `-50`, `2000`) and `m_fMaxDistance=300`. The DATA-04 runtime artifact separately binds the tested package's pristine bytes to the exact build-manifest hash and confirms write→install→restore, but the standalone 62-row inventory does not carry its own source-manifest hash. Treat it as a build-profile corroborating lead pending a reproducible scan on the registered installation, not as independently source-pinned evidence for every row.

The DMS primitive-property corpus is a second reusable lead: its `PrimitivePropertyValues.md` documents 9,015,978 successful primitive decodes (including 1,011,773 FloatProperty values, all size 4, with IEEE-754 bits retained), and its `PropertyStream.md` reports 2,812,713 framed streams ending at `None` across 904 packages. The current repository's UELib diagnostics flag array decode failures for `DisTweaks_Key` fields such as `m_BaseClassVersions` and `m_FallbackChainCooked`, while the DMS scanner intentionally leaves ArrayProperty and StructProperty values unsupported and reports them as unsupported rather than malformed. That difference offers a concrete triage path: compare only shared primitive tags and framing first, then use DMS's value-boundary/property-writer code as an independent implementation reference; do not treat its unsupported arrays as decoded evidence.

### Editor restoration workspace: useful boundary and evidence source

The editor-restoration archive is a separate, large research program, not a directly portable Dishonored retail finding set. Its current `STATUS.md` reports work on a different Win32 PE/PDB and a mutable reconstructed editor LAB; current tasks, build identities, and runtime authorizations are distinct from the RHCP retail baseline. Its own ledgers repeatedly separate static, fixture-only, and bounded LAB runtime evidence. This material can inform evidence discipline and potentially supply specific UE3/editor hypotheses, but must not be imported into retail gameplay/native findings without matching binary identity and reproducing the relevant analysis.

The archive has 26 Markdown restoration docs in its canonical `docs/` tree, alongside a much larger task/evidence archive. The first control-document review confirms the project preserves unresolved gates (factory/UI, package ABI, shader/runtime state), refuses to call a LAB stable, and warns that dated audit chronology is not current authorization. Treat its task/evidence chain as a separate corpus with its own pinned executable hashes and state rules.

The review found concrete synchronization problems: `docs/STATUS.md` records later bounded P3/P4 and partial P5 outcomes through FACT-0247–0256, including DrawMesh BasePass/Depth, while `docs/ROADMAP.md` still says P3 is blocked, P4 is not reached, and P5 is open/not reached. `docs/FULL_RESTORATION_PLAN.md` also contains an older baseline (M0–M3/P0–P2 state) and two U+FFFD replacement characters in otherwise valid UTF-8 Russian text; it must be reconciled with STATUS and its encoding defects corrected before it can guide contributors. `docs/DEPENDENCIES.md` still says runtime hits/frame were not observed for the DrawHUD/materials/DrawMesh path despite bounded DrawMesh hits in FACT-0256; it should distinguish the observed hits from the still-unproven complete rendered frame. `docs/LIBRARY.md` describes FACTS as ending at FACT-0236 and lists 236 ledger rows, while `docs/FACTS.md` says the ledger now runs through FACT-0256. `docs/TEST_MATRIX.md` has some later TASK-0231 evidence but still marks T-030 open/not reached, which may be an intentional end-to-end criterion rather than contradiction; its criterion needs alignment with the partial viewport facts. No files on D: were changed.

### Other workspaces

- `40_BROWSER_PORT` has PDB identity and native symbol work for a different/unresolved image set. Its own report lists distinct executable hashes and says exact build identity remains open. Treat its symbol rows as donors only after matching addresses/bytes against build `10256413`.
- `00_VAULT` preserves June/August 2012 PDB builds separately from the registered retail RHCP build. The 2012 material is useful for names and historical comparison, not for retail layouts without exact-build validation.
- `10_EDITOR_RESTORATION` and `30_VULKAN_RENDERER` dominate the file count. They contain large generated/copied workspaces; task records and unique source files need a per-project review after duplicate grouping. No editor executable was launched and no game binary was modified.

### Browser-port Kismet and native-symbol work

The authored browser-port analysis contains a useful extraction method and a set of June-2012 candidate semantics. Its local `DishonoredGame-Shipping.exe` SHA-256 is `0A093164DC7E0666FE1783D74B503D6ABD32C0E08676006DEFE344E739C5C162` (the same image is retained under the June 2012 vault build, changelist 254295 / engineVersion 9014); this is not the registered retail executable (`66443F3D…725E17E`). All 39 browser `_Script.upk` stems occur in the retail manifest, but none of the compared script packages has the same SHA-256. Therefore the browser graph counts and June code layouts are research leads only, not retail findings.

The method is directly reusable: `scripts/package-analysis/enrich_kismet_graph.py` joins object properties by exact object path, parses indexed input/output link descriptors (labels, disabled flags, PIE flags, delays), and annotates graph edges with endpoint link properties. For `SetTaskState`, it follows a typed variable link toward `DisSeqVar_Task` and records task/objective references when exact object paths resolve. `analyze_remote_event_scopes.py` validates package identity and object types, groups activator/receiver pairs by package + root sequence + event name, and labels them “same-root event-name candidate; not a runtime trace”; it also emits receiver outgoing graph edges. This is a concrete contributor workflow for reducing false links. Reproduce it against retail exports before using its output, and audit path fallbacks in the task-variable join because one fallback searches property values heuristically.

June PDB-backed candidates include StoryFlag set/check flows, task-state dispatch through `UDishonoredTask_Base::SetTaskState`, and RemoteEvent receiver lookup/dispatch by event name under the source object's root sequence. The browser archive itself reports 4,110 bytecode-bearing functions / 185,922 script bytes, successful parser decompiles (parser success only), 31,138 transitions, and 200 cross-package same-name RemoteEvent pairs; those totals and exact offsets are June-corpus-specific. The current retail index already contains classes such as `SeqAct_ActivateRemoteEvent` and `DisSeqAct_SetTaskState`, so a high-value next investigation is a retail exact-build package graph for these classes, including link descriptors and object ownership, followed by a native code byte/control-flow crosswalk. Generic Ghidra symbol search returned no direct named matches; absence of names is not negative evidence.

### Vulkan renderer findings on the registered retail build

Unlike the browser port, the Vulkan renderer documents Steam buildid `10256413` and the exact registered EXE SHA-256 `66443F3D…725E17E` in both `COMPATIBILITY.md` and `docs/baseline/BASELINE_PLAN.md`. Its runtime evidence is therefore build-bound to the same retail executable, although it concerns D3D9/rendering behavior and should remain a separate subsystem evidence source. The renderer is still an active, incomplete proxy/research implementation: current state says G0/G4 gates pass, M5B-FULL is open, and a same-Present combined texkill/VP0 capture is still required.

Several precise findings can guide project questions and future tooling:

- Frame boundary: `Present` is confirmed as the presentation edge. A 1280×720 fullscreen device uses X8R8G8B8 / D3DFMT format 21, immediate presentation, no MSAA, and auto depth-stencil disabled. Surface 7 is a high-confidence 1280×720 D24S8 scene-depth candidate; the backbuffer identity and exact UE3 render-thread enqueue boundary remain open.
- Depth architecture: same-Present G0+G4 D3D9 suppression accounts for 73,129 newly passing geometry pixels with zero newly failing pixels, about 43% of baseline geometry occlusion. The full-resolution ZWRITE population explains 169,256 geometric pixels in a separate causal census; the classic CB shader hash alone is negligible there. These are renderer-probe results, not gameplay mechanics.
- Native G4 mapping: the captured constants and transform audit show a required clip-space Y negate for the Vulkan port; applying it overlaps 21,019/21,841 D3D9 causal pixels (96.2%). G0 was intentionally left unchanged because empirical overlap already matched. This is strong evidence about the translation contract, not a generic statement that all UE3 shaders need Y negation.
- Current failure localization: native cumulative depth first diverges at CB local draw 5, then amplifies at locals 6 and 46; local 5 has no w-sign clip issue, while ~31.2% and 27.5% of vertices at locals 6 and 46 respectively have w≤0. The archive explicitly keeps the root cause open because a draw-local hardware depth oracle is not yet wired. This gives a sharply bounded next experiment rather than a settled explanation.
- Instrumentation coverage: the renderer's required-surface inventory records calls observed through its proxy and explicitly lists unobserved/unknown device paths. This is reusable as a method for distinguishing captured API coverage from assumed engine usage.

The renderer's accepted baseline is the retail RHCP build, but most capture/runtime claims are also conditioned on a particular environment (Windows 10.0.26100, RTX 5070 Ti Laptop, driver 32.0.15.9597, fullscreen 1280×720) and renderer proxy revision. Cross-reuse should carry the cited experiment/capture identity and these limits. The renderer project includes an extensive evolving tool/capture corpus; this pass has reviewed the core identity, status, frame-contract, required-surface, and selected depth-causality documents, not every renderer document or source file.

Further renderer documents expose several important evidence-handling lessons and narrower reusable facts:

- **Hardware oracle is a visibility oracle, not a depth dump.** The diagnostic white-PS draw immediately before VP0 was checked against `output_post != output_pre` with IoU 1.000 on three captures. But `INTZ LockRect` contents were shown not to represent the value used by the hardware LESSEQUAL test: some hardware-pass samples had raw zero while `frag_z≈0.997`. Oracle provenance is therefore strong for pass/fail masks, while direct depth-value recovery remains open. This distinction is useful for any future runtime instrumentation in this repository: label exactly what the probe measures.
- **Draw-removal causality has an interference condition.** Setting `ZWRITEENABLE=FALSE` across a range is not an isolated readout of that range's contribution if later draws in the range consume earlier depth. The renderer accordingly tracks both newly passing and newly failing pixels and treats large new-fail counts as structural interference. This is a valuable causal-analysis pattern for our call/dataflow and package experiments too: record side effects of the intervention and define a falsifier.
- **Renderer pass graph remains partly unresolved.** Observed RT/depth binds support a full-resolution geometry group, half-resolution 640×360 surfaces, quarter-resolution 320×180 surfaces and a VP0 composition draw. The input/sample relation for some half/quarter stages remains inferred; missing Draw calls may reflect unhooked StretchRect/Clear paths. VP0's sampled fmt-113 surface, fmt-21 target and depth7 binding are directly observed for the named capture. Avoid presenting all pass labels as recovered UE3 pass names.
- **State capture found scope-specific details.** In the cited 8,000-DIP G0 New-Game apitrace, stream frequencies were default on every DIP; no `SetRenderState(D3DRS_CLIPPING/CLIPPLANEENABLE)` or `SetClipPlane` occurred; depth and slope bias were zero; scissor was usually off; stencil was enabled on 1,274 DIPs and disabled on 3,726. This closes only that trace/scope; stencil remains explicitly deferred for other phases.
- **The shader database has a strong identity rule.** Runtime pointers are session-local and cleared on Reset, while D3D9 shader bytecode SHA-256 is the cross-session key; Release pointer reuse is not tracked. H-idle/HUD labels remain explicitly unproven. This is a useful model for exact-build analysis caches: content hashes plus session/build provenance, rather than pointer or short label alone.
- **The newer VP0 model corrected a major false lead.** V2 uses full D3D9 frustum clipping (`-w≤x,y≤w`, `0≤z≤w`) and screen-linear post-divide NDC Z. It improved the modeled hardware-depth MAE from about `3.33e-3` to `1.39e-3` and collapsed local5 false blocks from 42,280 to 81 in the cited comparison. Subsequent fidelity analysis found that 5,249/5,416 local5 causal FN pixels were already blocked before local5 (prefix timing); only about 167 were true local5 misses. The older `VP0_FRAGMENT_DEPTH.md` still states “CB native depth was substantially correct for local 5” as its architectural correction; read it alongside the later `LOCAL5_FN_FIDELITY.md`, which reclassifies the FN and requires locating the first end-state divergence under V2. Do not carry V1 local6/over-occlusion attribution into current conclusions.
- **The integration maturity boundary is clear.** A captured `s2_cap1` frame replays one indexed draw offscreen with clean Vulkan validation and about 98.3% of pixels within tolerance 2; a 24-package translated corpus also executes, but the corpus pixel/readback gate is still a diagnostic fail. A separate Win32 Vulkan Present micro-test passed, while the full game still presents through D3D9 and the Vulkan swapchain is opt-in/off. These are strong subsystem milestones, not a full-game Vulkan renderer.

Actionable reuse for the current project: consider a `Present`-scoped runtime record keyed by exact executable SHA + session + frame, with separate fields for observed device state, probe result, and inferred render role. If extending native-function evidence to rendering, start with the renderer's exact binary baseline and trace-linked shader hashes; do not mix its shader family IDs or game-specific pass labels into generic native-function status. This suggestion is methodological and does not alter the current L0–L4 semantics.

### Editor-restoration data crosswalk to retail 10256413

The editor archive has a different identity family: its pinned June `DishonoredGame.exe` SHA-256 is `5bcac99d74850fb45e5553fec923ca60b2cc6f854104c0afbf7ba89f373e14aa` with PDB GUID/Age `7BB0B798-A902-4521-A2B8-A385BEA9593C/1`; the current FULL_EDITOR runtime candidate is a modified image (`403155801a7bb891b8bab23235fd4fc5e841a5dfda37115a2b36c4f8fa63e035`). Its FACT-0237–0256 records are useful, carefully scoped observations about that LAB, not direct runtime facts for the retail game. However, a crosswalk can still identify exact questions to test.

One concrete crosswalk is already available in the retail package index. Editor TASK-0230 reports that its June EngineMaterials candidate contained one `MaterialInstanceConstant`, `EngineMaterials.PPVolumeMaterialInstance` (slot 365), and that candidate work removed this export while investigating an Expressions/PostLoad problem. In retail `10256413`, the indexed `Startup.upk` contains both `PPVolumeMaterial` (export 3707) and `PPVolumeMaterialInstance` (export 4304, class `MaterialInstanceConstant`). The package manifest binds `Startup.upk` to 9,267,293 bytes and SHA-256 `7B82FF1C3560F9B867D57EF5219F0FE9D10378DE705EE92A68FB9B2D1877BBBA`; UModel reports package version 801/30, engine 9098, 8,378 exports. UELib's object-decompile call refuses this compressed package, so the parent reference, serialized expression arrays, and runtime load/use remain **unknown**. This disproves only the broad transfer claim “the retail corpus has no PPVolumeMaterialInstance”; it does not imply the retail object is corrupt or used by the same editor path.

The local UModel reader was independently run directly in read-only `-pkginfo` and `-list` modes after checking the input SHA against the retail manifest. Both returned exit code 0; `-pkginfo` reported 20 compressed chunks, and full `-list` produced 8,382 lines including all 8,378 exports. The exact row is `4304 5ACD6B 29C MaterialInstanceConstant PPVolumeMaterialInstance`; the full listing contains 118 `MaterialInstanceConstant` rows. The reader binary is SHA-256 `44F8F1DA90A225554338328E1A2B24BE0B166A34CDFBEEB3C81DA9949E7675D0`. The repository MCP wrapper caps combined subprocess output at 200,000 characters, so its cached/list response had truncated the beginning of this 581,058-byte listing (it started around export 5,428); filtered direct invocation was needed to see export 4,304. This is a tooling-output limit, not package corruption. The test covered package summary and export listing/search only, as required for compressed UPKs; no property dump or asset extraction was performed.

This yields three high-value, build-bound EXP candidates (proposals, not yet experiments):

1. **Retail material-instance crosswalk.** UModel proves package/export-list parsing for exact-hash `Startup.upk`; the configured policy still limits compressed UPKs to summary/search, so do not request property decompilation under the current workflow. A future read-only parser capability would need explicit authorization in project policy and parser validation before recovering parent/property boundaries for exports 3707/4304. Runtime loading remains separate and unknown.
2. **Retail shader-cache identity and lookup.** The editor's static chain `FStaticParameterSet` → `FindId` → `TMap::FindRef` suggests auditing retail `RefShaderCache-PC-D3D-SM3.upk` and `SeekFreeShaderCache*` exports for serialized key/value structure and build-specific shader IDs. Retail package index shows a one-export `ShaderCache` in the base RefShaderCache (package version 801/30, engine 9098), and many cooked packages expose a `SeekFreeShaderCache00` export. First prove parser field boundaries and source hashes; do not infer an actual cache hit from the archive's static/editor tests.
3. **Named UE3 method crosswalk.** Select a bounded set of June PDB methods already represented by current retail subsystem evidence, then compare full function bytes or normalized instruction/control-flow signatures in the retail executable before using June names as labels. The existing EXP-0164 approach (candidate matching followed by exact range/size/byte checks) is a suitable starting method. Prioritize `FName`/object loader and material/shader dispatch only where a retail evidence question exists; do not import editor offsets or the modified candidate image's addresses.

The archive's DrawHUD/DrawMesh/BasePass facts are a separate graphics lead: FACT-0256 reports 19 bounded DrawMesh hits across BasePassOpaque, Depth and HitProxy on the modified June LAB, while BoneMatrices Set was still not reached. These can guide trace-site selection and expected renderer vocabulary, but not retail call rates or addresses. The renderer archive's own retail-bound D3D9 traces are the stronger source for actual retail draw behavior.

## Audit queue

- [x] Enumerate files without traversing directory links.
- [x] Hash every regular file and record exact duplicate content groups.
- [x] Read hub-level project/build/storage/timeline summaries and the retail vault manifest.
- [x] Review the selected community retail native exports and camera/package reports.
- [x] Compare two DMS package-catalog entries with the registered build manifest; exact SHA matches confirmed for both samples.
- [x] Compare all 904 DMS package-catalog hashes and paths with the registered build manifest; resolve the one modified-package row against DATA-04 pristine hash.
- [ ] Semantically review all 26 canonical editor-restoration docs and prioritize linked primary evidence by relevance to the retail project.
- [ ] Review every unique Markdown/text research document, recording project/task provenance and useful exact-build evidence.
- [ ] Review unique source/tool files for reusable parsers, export scripts, schema details, and reproducible indexes.
- [ ] Inventory binary/database/archive formats and run only suitable read-only parsers; record unsupported/opaque files explicitly.
- [ ] Compare any additional useful retail-target datasets against build `10256413` by hash, RVA, and bytes before importing claims.
- [ ] Reproduce browser Kismet property/link extraction on retail 10256413 package exports and audit task-variable path resolution.
- [x] Verify a supported read-only compressed-UPK summary/export-list path on exact-hash retail `Startup.upk`; preserve the compressed-UPK summary/search boundary for deeper property reads.
- [ ] For editor crosswalk candidate 2, map retail RefShaderCache/SeekFreeShaderCache serialized fields before comparing the June `FStaticParameterSet` hypothesis.
- [ ] For editor crosswalk candidate 3, select June PDB methods only when a matching retail subsystem question exists; verify each transferred name on exact retail bytes/control flow.
- [ ] Read remaining authored browser-port and Vulkan-renderer research docs; inspect high-value source tools and capture manifests, then record dispositions and exact provenance.
- [ ] Reconcile older Vulkan depth write-ups with the later V2/local5 reclassification before citing any depth root-cause claim.
- [ ] Publish a final disposition table: imported as evidence, reusable method, reference only, duplicate/generated, or out of scope.

Until those remaining passes are complete, this report is a partial audit, not a claim that every document has been semantically reviewed.
