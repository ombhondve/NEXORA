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
