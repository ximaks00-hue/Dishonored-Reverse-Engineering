from __future__ import annotations


def test_gateway_module_loads():
    from mcp_servers.gateway import server as gateway

    assert gateway.server.name == "dishonored-gateway"
    # Spot-check that composite + callgraph tools were registered.
    tools = getattr(gateway.server, "_tool_manager", None)
    # Fallback: ensure callables exist on module.
    assert callable(gateway.health)
    assert callable(gateway.callers)
    assert callable(gateway.callees)
    assert callable(gateway.xrefs_to)
    assert callable(gateway.path)
    _ = tools
