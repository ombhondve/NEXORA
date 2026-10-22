"""
Investigation API Integration Tests.
Verifies full end-to-end flow: creation, discovery start, evidence query, report generation, and security.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_investigation_lifecycle(client: AsyncClient):
    # 1. Create an investigation
    payload = {
        "title": "Operation Sovereign Shield",
        "description": "Investigating public domain infrastructure and related entities",
        "target_clue": "NEXORA Intelligence",
        "clue_type": "text",
        "max_depth": 2,
        "max_total_queries": 6,
        "max_execution_seconds": 60,
    }
    create_res = await client.post("/api/v1/investigations", json=payload)
    assert create_res.status_code == 201
    inv_data = create_res.json()
    inv_id = inv_data["id"]
    assert inv_data["status"] == "pending"

    # 2. Get investigation
    get_res = await client.get(f"/api/v1/investigations/{inv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Operation Sovereign Shield"

    # 3. Start discovery
    start_res = await client.post(f"/api/v1/investigations/{inv_id}/start")
    assert start_res.status_code == 200

    # 4. Check events
    events_res = await client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 1

    # 5. Check direct search endpoint
    search_payload = {
        "query": "Cybersecurity Open Framework",
        "max_results": 5,
    }
    search_res = await client.post("/api/v1/search", json=search_payload)
    assert search_res.status_code == 200
    assert search_res.json()["total_results"] > 0

    # 6. Check sources endpoint
    sources_res = await client.get("/api/v1/sources")
    assert sources_res.status_code == 200
    sources = sources_res.json()
    assert len(sources) >= 1

    # 7. Check report endpoint
    report_res = await client.get(f"/api/v1/investigations/{inv_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert "summary_markdown" in report_data
    assert "OSINT Investigation Report" in report_data["summary_markdown"]

    # 8. Check lead graph endpoint (valid investigation)
    graph_res = await client.get(f"/api/v1/investigations/{inv_id}/graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["investigation_id"] == inv_id
    assert graph_data["target_clue"] == "NEXORA Intelligence"
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert isinstance(graph_data["nodes"], list)
    assert isinstance(graph_data["edges"], list)
    assert graph_data["total_nodes"] >= 1
    assert graph_data["nodes"][0]["type"] == "seed"


@pytest.mark.asyncio
async def test_investigation_graph_nonexistent(client: AsyncClient):
    """Confirm 404 is returned when querying graph for nonexistent investigation."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await client.get(f"/api/v1/investigations/{fake_id}/graph")
    assert res.status_code == 404
    body = res.json()
    assert body["error"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_investigation_graph_with_leads_and_entities(client: AsyncClient, db_session):
    """Confirm lead graph accurately correlates leads and entity relationships."""
    from recursive_osint.db.models.investigation import Investigation
    from recursive_osint.db.models.lead_and_query import DiscoveryLead
    from recursive_osint.db.models.entity import ExtractedEntity, EntityRelationship

    # Create investigation
    inv = Investigation(
        title="Operation Cyber Mesh",
        target_clue="domain:mesh-intel.org",
        clue_type="domain",
        status="completed",
        max_depth=3,
        current_depth=2,
    )
    db_session.add(inv)
    await db_session.flush()

    # Add child leads
    lead1 = DiscoveryLead(
        investigation_id=inv.id,
        lead_type="domain",
        lead_value="api.mesh-intel.org",
        depth=1,
        priority_score=0.9,
        status="expanded",
        discovery_reason="Discovered via DNS lookup",
    )
    db_session.add(lead1)
    await db_session.flush()

    lead2 = DiscoveryLead(
        investigation_id=inv.id,
        parent_lead_id=lead1.id,
        lead_type="entity",
        lead_value="Dr. Helena Vance",
        depth=2,
        priority_score=0.85,
        status="queued",
        discovery_reason="Discovered in certificate WHOIS",
    )
    db_session.add(lead2)

    # Add entities and relationship
    ent1 = ExtractedEntity(
        investigation_id=inv.id,
        entity_type="domain",
        entity_value="mesh-intel.org",
        normalized_value="mesh-intel.org",
        confidence=0.95,
    )
    ent2 = ExtractedEntity(
        investigation_id=inv.id,
        entity_type="person",
        entity_value="Helena Vance",
        normalized_value="helena vance",
        confidence=0.88,
    )
    db_session.add_all([ent1, ent2])
    await db_session.flush()

    rel = EntityRelationship(
        investigation_id=inv.id,
        source_entity_id=ent1.id,
        target_entity_id=ent2.id,
        relationship_type="registered_by",
        confidence=0.90,
    )
    db_session.add(rel)
    await db_session.commit()

    # Query graph
    res = await client.get(f"/api/v1/investigations/{inv.id}/graph")
    assert res.status_code == 200
    data = res.json()
    assert data["investigation_id"] == inv.id
    assert data["is_empty"] is False
    assert data["total_nodes"] >= 4
    assert data["total_edges"] >= 3

    # Ensure edge connects lead1 -> lead2
    lead_edge = next((e for e in data["edges"] if e["source"] == lead1.id and e["target"] == lead2.id), None)
    assert lead_edge is not None
    assert lead_edge["label"] == "expanded_to"

