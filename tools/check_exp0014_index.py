#!/usr/bin/env python3
"""Validate the report-derived EXP-0014 index against the committed Markdown.
This does not validate game binary memory, executable provenance or Ghidra output.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments" / "EXP-0014-native-owner-triage.md"
INDEX = ROOT / "research" / "indexes" / "EXP-0014-report-derived-index.json"

def table(text, heading, num_cols):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    rows = []
    for line in lines[start + 1:]:
        if not line.startswith("|"):
            if rows: break
            continue
        cells = [x.strip(" `") for x in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", c) for c in cells): continue
        if len(cells) != num_cols: raise ValueError("column mismatch")
        rows.append(cells)
    return rows

def canonical_source(source: bytes) -> bytes:
    """Hash Markdown independent of Git checkout line-ending conversion."""
    return source.replace(b"\r\n", b"\n")


def validate(source, index):
    source = canonical_source(source)
    if hashlib.sha256(source).hexdigest() != index["source_sha256"]:
        raise ValueError("source sha256 differs")
    text = source.decode("utf-8")
    reg = table(text, "| Key | Registrar VA", 6)
    ctrl = table(text, "| Controller native exec | Record VA", 4)
    ptr = table(text, "| Table VA | RVA | Pointer target VA", 5)
    if (len(reg),len(ctrl),len(ptr)) != (21,9,10):
        raise ValueError("wrong row counts")
    if list(map(len, (index["registry"],index["controller"],index["lookat_table"]))) != [21,9,10]:
        raise ValueError("index row counts differ")
    if len({int(r[0]) for r in reg}) != 21: raise ValueError("duplicate factory keys")
    for r,v in zip(reg,index["registry"]):
        if v["key"] != int(r[0]) or v["type_name"] != r[5]: raise ValueError("registry identity")
        if [v[k] for k in ("registrar_va","factory_va","constructor_va")] != [r[i] for i in (1,2,4)]:
            raise ValueError("registry addresses")
        number = r[3].replace("`","")
        alloc = int(number.split()[0], 10 if "(decimal)" in number else (16 if number.startswith("0x") else 10))
        if v["allocation_bytes"] != alloc: raise ValueError("allocation radix")
    for r,v in zip(ctrl,index["controller"]):
        if (v["name"],v["record_va"],v["wrapper_va"]) != tuple(r[:3]):
            raise ValueError("wrapper mismatch")
        if v["receiver_slot_offset"] not in r[3]: raise ValueError("virtual offset mismatch")
    if next(x for x in index["controller"] if x["name"]=="OnTeleport_Native")["wrapper_va"] != "0x009EDC30":
        raise ValueError("OnTeleport correction regression")
    for r,v in zip(ptr,index["lookat_table"]):
        if [v[k] for k in ("slot_va","slot_rva","target_va","target_rva","function")] != r:
            raise ValueError("pointer table mismatch")
        if int(r[0],16)-0x400000 != int(r[1],16) or int(r[2],16)-0x400000 != int(r[3],16):
            raise ValueError("RVA mismatch")
    if index["lookat_table"][7]["target_va"] != "0x00956660": raise ValueError("Lookat slot")
    return True

if __name__ == "__main__":
    validate(SRC.read_bytes(), json.loads(INDEX.read_text(encoding="utf-8")))
    print("EXP-0014 report/index consistency OK; game binary NOT independently verified")
