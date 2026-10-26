#!/usr/bin/env python3
"""Compare exact 32-bit Ghidra function ENTRY addresses, one hex VA per line."""
import argparse, json
from pathlib import Path
def load(path):
    result=set()
    for n,line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(),1):
        t=line.split("#",1)[0].split(",",1)[0].strip()
        if not t or t.lower() in ("va","address","entry_va"):continue
        try:v=int(t,16)
        except ValueError as e:raise ValueError(f"{path}:{n}: invalid VA {t}") from e
        if v<0 or v>0xffffffff or v in result:raise ValueError(f"{path}:{n}: invalid/duplicate x86 entry")
        result.add(v)
    return result
def compare(first,second):
    return {"first_count":len(first),"second_count":len(second),
            "shared_count":len(first&second),
            "only_first":[f"0x{x:08X}" for x in sorted(first-second)],
            "only_second":[f"0x{x:08X}" for x in sorted(second-first)]}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("old");p.add_argument("new");p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=json.dumps(compare(load(a.old),load(a.new)),ensure_ascii=False,indent=2)+"\n"
    if a.output:a.output.write_text(result,encoding="utf-8")
    else:print(result,end="")
