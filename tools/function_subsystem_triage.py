#!/usr/bin/env python3
"""Partition the exact-build internal function index into conservative label/graph triage buckets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from callgraph_coverage import read_build_identity, read_pe_sections


ROOT = Path(__file__).resolve().parents[1]
ADDRESS = re.compile(r"^[0-9A-Fa-f]{8}$")
FUN = re.compile(r"^FUN_[0-9A-Fa-f]+$")
THUNK_FUN = re.compile(r"^thunk_FUN_[0-9A-Fa-f]+$")
UNWIND = re.compile(r"^Unwind@[0-9A-Fa-f]{8}$")
CALL_LABEL = re.compile(r"^Catch(?:_All)?@[0-9A-Fa-f]{8}$")

# These are exact labels observed in this build's index. A match identifies a
# symbol-name family only; it does not prove implementation ownership or use.
WWISE_LABELS = {
    "AddBehavioralExtension", "AddLanguageChangeObserver", "AddPlayerMotionDevice",
    "BypassEnvironment", "CancelBankCallbackCookie", "CancelEventCallback",
    "CancelEventCallbackCookie", "ClearBanks", "ClearPreparedEvents", "CreateDevice",
    "DestroyDevice", "ExecuteActionOnEvent", "GetActiveGameObjects", "GetActiveListeners",
    "GetDefaultDeviceSettings", "GetDefaultInitSettings", "GetDefaultPlatformInitSettings",
    "GetDefaultSettings", "GetEnvironmentBypass", "GetEnvironmentVolume",
    "GetEnvironmentVolumes", "GetEventIDFromPlayingID", "GetGameObjectDryLevelValue",
    "GetGameObjectEnvironmentsValues", "GetGameObjectFromPlayingID", "GetIDFromString",
    "GetIsGameObjectActive", "GetListenerPosition", "GetListenerSpatialization",
    "GetMaxRadius", "GetMaxNumVoicesLimit", "GetObjectObstructionAndOcclusion",
    "GetPanningRule", "GetPlayingIDsFromGameObject", "GetPlayingSegmentInfo",
    "GetPoolAttributes", "GetPoolID", "GetPoolMemoryUsed", "GetPoolName", "GetPoolStats",
    "GetPosition", "GetPositioningInfo", "GetRTPCValue", "GetSourcePlayPosition",
    "GetSpeakerConfiguration", "GetState", "GetSwitch", "LoadBank", "LockPlaylist",
    "Open", "Pause", "Play", "PlaySourcePlugin", "PostEvent", "PostTrigger",
    "PrepareBank", "PrepareEvent", "PrepareGameSyncs", "QueryAudioObjectIDs",
    "RegisterCodec", "RegisterGameObj", "RegisterGlobalCallback", "RegisterMotionDevice",
    "RegisterPlugin", "RemoveBehavioralExtension", "RemoveLanguageChangeObserver",
    "RemovePlayerMotionDevice", "RenderAudio", "ResetRTPCValue", "ResolveDialogueEvent",
    "Resume", "SeekOnEvent", "SetActiveListeners", "SetAttenuationScalingFactor",
    "SetBankLoadIOSettings", "SetCurrentLanguage", "SetEffect", "SetEnvironmentVolume",
    "SetEnvironmentVolumes", "SetGameObjectDryLevelValue", "SetGameObjectEnvironmentsValues",
    "SetListenerPipeline", "SetListenerPosition", "SetListenerScalingFactor",
    "SetListenerSpatialization", "SetMaxNumVoicesLimit", "SetMultiplePositions",
    "SetObjectObstructionAndOcclusion", "SetPanningRule", "SetPlayerListener",
    "SetPlayerVolume", "SetPosition", "SetPositionInternal", "SetRTPCValue", "SetState",
    "SetSwitch", "SetVolumeThreshold", "Stop", "StopAll", "StopPlayingID",
    "StopSourcePlugin", "Term", "UnloadBank", "UnregisterAllGameObj", "UnregisterGameObj",
    "GetCurrentLanguage", "GetFileLocationResolver", "SetFileLocationResolver",
    "SetPoolName", "CheckPoolId", "GetBlock", "GetBlockSize", "GetMaxPools",
    "GetNumPools", "CreatePool", "DestroyPool", "Malloc", "Falign", "Malign",
    "ReleaseBlock", "Create", "Destroy", "SetGameObjectEnvironmentsValues",
}
WINSOCK_LABELS = {
    "accept", "bind", "closesocket", "connect", "gethostbyname", "gethostname",
    "getsockname", "getsockopt", "htonl", "htons", "inet_addr", "ioctlsocket",
    "listen", "ntohl", "ntohs", "recv", "recvfrom", "select", "send", "sendto",
    "setsockopt", "socket", "WSAGetLastError", "WSAStartup",
}
CRT_RUNTIME_LABELS = {
    "_atexit", "_controlfp_s", "_errno", "_itoa_s", "_lock", "_onexit", "_stricmp",
    "_unlock", "_vsnprintf_s", "_wfopen_s", "_wstat64", "abs", "atof", "atoi", "ceil",
    "closesocket", "fclose", "fflush", "floor", "fread", "free", "fseek", "ftell",
    "fwrite", "initterm", "initterm_e", "isdigit", "isspace", "isxdigit", "localeconv",
    "malloc", "memcpy", "memmove", "memset", "rewind", "strchr", "strcmp", "strcpy_s",
    "strcspn", "strncpy_s", "strrchr", "strspn", "strstr", "strtod", "strtol", "strtoul",
    "strncmp", "wcscoll", "wcscpy_s", "wcsncpy_s", "_New_Locimp", "operator_new",
    "purecall", "___tmainCRTStartup", "___report_gsfailure", "___security_init_cookie",
    "__security_check_cookie", "__CxxThrowException", "_CxxThrowException",
}


def label_bucket(name: str) -> tuple[str, str, str]:
    if FUN.fullmatch(name):
        return "address_derived_function_label", "unknown", "address-derived index label only"
    if THUNK_FUN.fullmatch(name):
        return "address_derived_thunk_label", "unknown", "address-derived thunk label only"
    if UNWIND.fullmatch(name):
        return "unwind_address_label", "unknown", "Unwind@address index label; handler semantics not verified"
    if CALL_LABEL.fullmatch(name):
        return "catch_address_label", "exception_handler_candidate", "Catch@address label only"
    if name in WWISE_LABELS:
        return "wwise_audio_api_name", "audio_middleware_candidate", "exact symbol-name match only"
    if name in WINSOCK_LABELS:
        return "winsock_api_name", "network_candidate", "exact symbol-name match only"
    if name in {"D3DPERF_BeginEvent", "D3DPERF_EndEvent", "D3DPERF_SetOptions", "Direct3DCreate9"}:
        return "direct3d_api_name", "graphics_candidate", "exact symbol-name match only"
    if name in {"DirectInput8Create", "XInputGetState", "XInputSetState"}:
        return "input_api_name", "input_candidate", "exact symbol-name match only"
    if name.startswith("DelayLoad_Nx"):
        return "physx_delayload_name", "physics_candidate", "exact DelayLoad_Nx symbol-name match only"
    if name in CRT_RUNTIME_LABELS or name.startswith(("__", "_CI")):
        return "crt_cpp_runtime_name", "runtime_library_candidate", "exact symbol-name pattern only"
    if name.startswith("FID_conflict:"):
        return "fid_conflict_label", "unknown", "Ghidra FID conflict label; identity unresolved"
    if name.startswith(("Catch", "Catch_All")):
        return "catch_or_catch_all_label", "exception_handler_candidate", "catch-like label; address pattern differs"
    if "scalar_deleting_destructor" in name or "vector_deleting_destructor" in name or name.startswith("~"):
        return "constructor_destructor_name", "runtime_or_object_lifecycle_candidate", "name suggests lifecycle operation; owner unassigned"
    if name in {"Construct", "CreateObject", "Create", "Destroy", "Init", "Term"}:
        return "generic_lifecycle_name", "unknown", "generic name; owner unresolved"
    return "named_symbol_owner_unknown", "unknown", "name is not enough to establish subsystem"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--functions", type=Path, default=ROOT / "research/executable/functions.csv")
    parser.add_argument("--callgraph", type=Path, default=ROOT / "knowledge/database/callgraph.sqlite")
    parser.add_argument("--exe", type=Path, default=ROOT / "Dishonored RHCP/Binaries/Win32/Dishonored.exe")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "research/executable/evidence/function-triage")
    args = parser.parse_args()
    functions_path = args.functions.resolve(strict=True)
    callgraph_path = args.callgraph.resolve(strict=True)
    exe_path = args.exe.resolve(strict=True)
    build_id, expected_hash = read_build_identity()
    exe_hash = hashlib.sha256(exe_path.read_bytes()).hexdigest().upper()
    if exe_hash != expected_hash:
        raise SystemExit("EXE SHA-256 differs from build record")
    image_base, sections = read_pe_sections(exe_path)

    with functions_path.open(newline="", encoding="utf-8-sig") as stream:
        function_rows = list(csv.DictReader(stream))
    by_address = {row["address"].strip().upper(): row for row in function_rows}
    if len(by_address) != len(function_rows) or not all(ADDRESS.fullmatch(address) for address in by_address):
        raise SystemExit("function index has duplicate or invalid addresses")
    with sqlite3.connect(callgraph_path) as db:
        metadata = dict(db.execute("SELECT key,value FROM meta"))
        if metadata.get("build_id") != build_id or metadata.get("exe_sha256", "").upper() != expected_hash:
            raise SystemExit("callgraph build/hash does not match build record")
        edges = db.execute("SELECT kind,from_addr,to_addr,site_addr FROM edges")
        callers: set[str] = set()
        callees: set[str] = set()
        data_source_targets: Counter[str] = Counter()
        data_source_sections: dict[str, Counter[str]] = defaultdict(Counter)
        call_edge_rows = 0
        data_edge_rows = 0
        for kind, source, target, site in edges:
            source = source.strip().upper()
            target = target.strip().upper()
            if kind == "call":
                call_edge_rows += 1
                if source in by_address:
                    callers.add(source)
                if target in by_address:
                    callees.add(target)
            elif kind == "data":
                data_edge_rows += 1
                if target in by_address:
                    data_source_targets[target] += 1
                    try:
                        site_value = int(str(site), 16)
                    except ValueError:
                        section_name = "symbolic"
                    else:
                        section_name = next((name for name, start, end in sections if start <= site_value < end), "outside_image")
                    data_source_sections[target][section_name] += 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = args.output_dir / "internal-function-triage.csv"
    fieldnames = ["address", "name", "signature", "size_bytes", "size_bucket", "name_label_family", "subsystem_candidate", "label_claim", "direct_call_role", "incoming_data_xref_edges", "incoming_data_xref_sections", "semantic_review_status"]
    group_counts: Counter[tuple[str, str, str]] = Counter()
    call_roles: Counter[str] = Counter()
    data_target_count = 0
    unknown_subsystem_count = 0
    with catalog_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for address, row in sorted(by_address.items()):
            name = row["name"]
            family, candidate, claim = label_bucket(name)
            if address in callers and address in callees:
                role = "caller_and_target"
            elif address in callers:
                role = "caller_only"
            elif address in callees:
                role = "target_only"
            else:
                role = "neither_direct_call_role"
            size = int(row["size"])
            size_bucket = "0-16" if size <= 16 else "17-32" if size <= 32 else "33-64" if size <= 64 else "65-128" if size <= 128 else "129-256" if size <= 256 else "257-512" if size <= 512 else "513-1024" if size <= 1024 else "1025+"
            incoming = data_source_targets[address]
            sections_json = json.dumps(dict(sorted(data_source_sections[address].items())), ensure_ascii=False, separators=(",", ":"))
            writer.writerow({
                "address": address,
                "name": name,
                "signature": row["signature"],
                "size_bytes": size,
                "size_bucket": size_bucket,
                "name_label_family": family,
                "subsystem_candidate": candidate,
                "label_claim": claim,
                "direct_call_role": role,
                "incoming_data_xref_edges": incoming,
                "incoming_data_xref_sections": sections_json,
                "semantic_review_status": "not_reviewed_by_this_triage",
            })
            group_counts[(family, candidate, role)] += 1
            call_roles[role] += 1
            data_target_count += int(incoming > 0)
            unknown_subsystem_count += int(candidate == "unknown")

    summary = {
        "build_id": build_id,
        "exe_sha256": exe_hash,
        "function_index_rows": len(function_rows),
        "function_index_unique_addresses": len(by_address),
        "callgraph_call_edges_read": call_edge_rows,
        "callgraph_data_edges_read": data_edge_rows,
        "direct_call_role_counts": dict(sorted(call_roles.items())),
        "functions_with_incoming_data_xref_edges": data_target_count,
        "functions_assigned_unknown_subsystem_bucket": unknown_subsystem_count,
        "functions_assigned_symbol_name_candidate_bucket": len(by_address) - unknown_subsystem_count,
        "function_catalog_rows": sum(group_counts.values()),
        "group_counts_by_label_candidate_and_call_role": [
            {"name_label_family": family, "subsystem_candidate": candidate, "direct_call_role": role, "functions": count}
            for (family, candidate, role), count in sorted(group_counts.items())
        ],
        "limits": [
            "All 72,437 records are reconciled to the exact-build index address set; label families are index strings, not proof of function behavior or implementation owner.",
            "Subsystem candidate labels derived from API-like names remain candidates only. The large unknown bucket is intentional and should shrink only with function-body, xref, vtable-owner, or package/native evidence.",
            "Callgraph role and data-xref fields describe the existing static export; they do not establish runtime execution, indirect-call completeness, or reachability.",
            "The semantic_review_status column is explicitly not_reviewed_by_this_triage for every row.",
        ],
    }
    summary_path = args.output_dir / "internal-function-triage-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "group_counts_by_label_candidate_and_call_role"}, indent=2, ensure_ascii=False))
    print(f"catalog={catalog_path}")
    print(f"summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
