#!/usr/bin/env python3
"""Validate source-bounded REV-0005 findings. NOT independent EXE validation."""
import argparse, json, re
from pathlib import Path
EXPECTED_SHA="66443F3D68A6C658B0ED943260C3EB2F4CC9E3400D5809A94D6EC41EB725E17E"

def number(value):
    if not isinstance(value,str) or re.fullmatch(r"0x[0-9a-fA-F]{1,8}",value) is None:
        raise ValueError("Invalid hex address: %r" % (value,))
    return int(value,16)

def validate(data):
    if data["source_type"]!="user_report_summary" or data["independently_reproduced"] is not False:
        raise ValueError("Must not claim independent EXE confirmation")
    if data["reported_sha256"]!=EXPECTED_SHA or number(data["image_base"])!=0x400000:
        raise ValueError("Build identity mismatch")
    names=set()
    known={}
    for e in data["classes"]:
        name=e["name"]
        if name in names: raise ValueError("Duplicate class")
        names.add(name)
        for key in ("descriptor_va","constructor_va","vtable_va"): number(e[key])
        if e["slot_offset"] is not None:
            table,offset,slot,target=map(number,[e["vtable_va"],e["slot_offset"],e["slot_va"],e["target_va"]])
            if table+offset!=slot or target<=0x400000: raise ValueError("Slot/target inconsistency")
            known[name]=(offset,target)
    if known.get("DisGFxMoviePlayerPowerWheel")!=(0x1F0,0x00BCD800):
        raise ValueError("PowerWheel target mismatch")
    if known.get("DishonoredPlayerController")!=(0x560,0x00AB4680):
        raise ValueError("Controller target mismatch")
    if data["gameplay_position_update_confirmed"] is not False:
        raise ValueError("Relocation has not been proven")
    if not any(m["value"]==24 and m["result"]==2 and m["scope"]=="PowerWheel OnSelectionChanged only"
               for m in data["known_mappings"]):
        raise ValueError("Observed wheel conversion changed or broadened")
    fam=data["blink_family"]
    if len(fam)!=4 or len({x["function_va"] for x in fam})!=4:
        raise ValueError("Expected four distinct family candidates")
    for x in fam: number(x["function_va"])
    counts=data["function_counts"]
    if counts["total"]-counts["non_external"]!=488 or counts["external_number_measured"] is not False:
        raise ValueError("488 external-function hypothesis must remain unverified")
    return known

def summarize(data):
    known=validate(data)
    result=["# REV-0005 — report-derived vtable evidence","",
            "> User report only; original Ghidra program and binary not independently accessed.","",
            "| Class | vtable VA | Slot VA | Target RVA |","|---|---|---|---|"]
    for e in data["classes"]:
        if e["name"] in known:
            result.append("| %s | `%s` | `%s` | `0x%08X` |" %
                          (e["name"],e["vtable_va"],e["slot_va"],number(e["target_va"])-0x400000))
    result.extend(["","Wheel code 24→2 is an observed UI path, NOT a demonstrated Blink cast.",
                   "No authenticated player relocation, native tweak field layout or _iPower index mapping."])
    return "\n".join(result)+"\n"

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("index",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    text=summarize(json.loads(args.index.read_text(encoding="utf-8")))
    if args.output:args.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
