"""
Connector Integration Tests.
"""

import pytest
from recursive_osint.connectors.mock_demo import MockDemoConnector
from recursive_osint.connectors.registry import connector_registry


@pytest.mark.asyncio
async def test_mock_demo_connector():
    connector = MockDemoConnector()
    assert connector.is_configured is True
    assert connector.requires_api_key is False

    results = await connector.search("NEXORA Cyber Operations", max_results=3)
    assert len(results) > 0
    assert results[0].source_name == "mock_demo"
    assert "Simulated Record" in results[0].title
    assert results[0].relevance_score > 0.7


def test_connector_registry_lists_connectors():
    connectors = connector_registry.list_all()
    assert len(connectors) >= 1
    names = [c.name for c in connectors]
    assert "mock_demo" in names
    assert "searxng" in names


@pytest.mark.asyncio
async def test_searxng_connector_integration():
    searxng = connector_registry.get("searxng")
    assert searxng is not None
    assert searxng.name == "searxng"
    assert searxng.connector_type == "metasearch"

    # When local SearXNG is running, verify end-to-end result retrieval
    if searxng.is_configured:
        results = await searxng.search("Python FastAPI", max_results=3)
        assert len(results) > 0
        assert results[0].url.startswith("http")
        assert len(results[0].title) > 0
        assert "searxng" in results[0].source_name


@pytest.mark.asyncio
async def test_new_connectors_registered_and_configured():
    for name in ("openalex", "wikidata", "github_public"):
        conn = connector_registry.get(name)
        assert conn is not None, f"Connector {name} not registered"
        assert conn.is_configured is True
        assert conn.is_simulated is False
        assert conn.coverage_info is not None


@pytest.mark.asyncio
async def test_connector_health_check_methods():
    for conn in connector_registry.list_all():
        assert hasattr(conn, "check_health")
        if conn.is_simulated:
            healthy, status = await conn.check_health()
            assert healthy is True
            assert status == "simulated"


@pytest.mark.asyncio
async def test_sources_api_returns_health_status(client):
    res = await client.get("/api/v1/sources")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5

    mock_entry = next((item for item in data if item["name"] == "mock_demo"), None)
    assert mock_entry is not None
    assert mock_entry["is_simulated"] is True
    assert mock_entry["health_status"] == "simulated"

    wiki_entry = next((item for item in data if item["name"] == "wikipedia"), None)
    assert wiki_entry is not None
    assert wiki_entry["is_simulated"] is False
    assert wiki_entry["health_status"] in ("online", "offline", "unconfigured")


