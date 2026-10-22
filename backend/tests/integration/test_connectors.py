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

