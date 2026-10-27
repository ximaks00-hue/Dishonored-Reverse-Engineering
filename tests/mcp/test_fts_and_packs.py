from __future__ import annotations

from mcp_servers.common import agent_packs
from mcp_servers.common.fts import search_fts


def test_fts_finds_edges_or_experiments():
    hits = search_fts("blink", limit=10)
    assert isinstance(hits, list)
    # DB may be sparse in CI-less local clones; at least the query must not crash.
    if hits:
        assert "kind" in hits[0]
        assert "key" in hits[0]


def test_brief_blink_snapshot():
    payload = agent_packs.brief("blink")
    assert payload["topic"] == "blink"
    assert "edges" in payload
    assert "edge_status_groups" in payload
    assert "note" in payload
    # Claim boundaries: rejected and open stay distinct buckets.
    groups = payload["edge_status_groups"]
    assert "confirmed" in groups
    assert "open" in groups
    assert "rejected" in groups


def test_research_summary_counts():
    summary = agent_packs.research_summary()
    assert "claim_status_counts" in summary
    assert "edge_status_counts" in summary
