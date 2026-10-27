from __future__ import annotations

from mcp_servers.common.package_cache import parse_object_list


def test_parse_object_list_basic():
    output = """
Loading package...
   12 Class DisPowerBlink
   34 Function Blink.Activate
Class
Found 2 objects
"""
    items = parse_object_list(output)
    assert {"class": "Class", "name": "DisPowerBlink"} in items
    assert {"class": "Function", "name": "Blink.Activate"} in items
    assert all(i["class"].lower() != "found" for i in items)
