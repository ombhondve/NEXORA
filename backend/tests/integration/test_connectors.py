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
