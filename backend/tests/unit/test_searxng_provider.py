"""
Unit tests for the SearXNG Provider and SearXNGConnector.
Tests result normalization, URL deduplication, timeouts, and error handling using mocked responses.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from recursive_osint.config import Settings
from recursive_osint.connectors.searxng import SearXNGProvider, SearXNGConnector
from recursive_osint.schemas.search import SearchResultItem


MOCK_SEARXNG_PAYLOAD = {
    "query": "Python FastAPI",
    "number_of_results": 3,
    "results": [
        {
            "title": "FastAPI - FastAPI",
            "url": "https://fastapi.tiangolo.com/",
            "content": "FastAPI is a modern, high-performance web framework for Python.",
            "engine": "duckduckgo",
            "engines": ["brave", "duckduckgo", "google cse"],
            "score": 9.0,
            "category": "general",
            "publishedDate": "2026-01-15T12:00:00",
            "thumbnail": "https://example.org/thumb1.png",
        },
        {
            "title": "FastAPI GitHub Repository",
            "url": "https://github.com/fastapi/fastapi",
            "content": "FastAPI framework, high performance, easy to learn, fast to code.",
            "engine": "github",
            "engines": ["github"],
            "score": 6.5,
            "category": "it",
            "publishedDate": None,
        },
        {
            "title": "FastAPI Docs Duplicate URL with Trailing Slash",
            "url": "https://fastapi.tiangolo.com/?utm_source=searxng",
            "content": "Duplicate entry pointing to the same canonical FastAPI documentation.",
            "engine": "brave",
            "engines": ["brave"],
            "score": 5.0,
            "category": "general",
        },
    ],
}


class TestSearXNGProvider:
    def test_provider_initialization(self):
        """Verify URL trailing slash normalization and defaults."""
        provider = SearXNGProvider(base_url="http://localhost:8082/", timeout=5.0, max_results=15)
        assert provider.base_url == "http://localhost:8082"
        assert provider.timeout == 5.0
        assert provider.max_results == 15

    @pytest.mark.asyncio
    async def test_search_normalization_and_deduplication(self):
        """Confirm SearXNG responses are normalized into SearchResultItem with URL deduplication."""
        provider = SearXNGProvider(base_url="http://localhost:8082")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SEARXNG_PAYLOAD

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            results = await provider.search("Python FastAPI", max_results=10)

            # Confirm 2 results returned (the 3rd item has canonical URL matching item 1)
            assert len(results) == 2

            first = results[0]
            assert isinstance(first, SearchResultItem)
            assert first.title == "FastAPI - FastAPI"
            assert first.url == "https://fastapi.tiangolo.com/"
            assert "modern, high-performance" in first.snippet
            assert first.source_name == "searxng:duckduckgo"
            assert first.publication_date == "2026-01-15"
            assert first.relevance_score >= 0.8
            assert first.metadata["primary_engine"] == "duckduckgo"
            assert "brave" in first.metadata["engines"]
            assert first.metadata["thumbnail"] == "https://example.org/thumb1.png"

            second = results[1]
            assert second.title == "FastAPI GitHub Repository"
            assert second.url == "https://github.com/fastapi/fastapi"
            assert second.source_name == "searxng:github"

    @pytest.mark.asyncio
    async def test_search_max_results_limit(self):
        """Confirm max_results bounds the returned list."""
        provider = SearXNGProvider(base_url="http://localhost:8082")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SEARXNG_PAYLOAD

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await provider.search("Python FastAPI", max_results=1)
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_timeout_handling(self):
        """Confirm timeout returns empty list without raising."""
        provider = SearXNGProvider(base_url="http://localhost:8082", timeout=0.1)

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Connection timed out")
            results = await provider.search("Python FastAPI")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_connection_error_handling(self):
        """Confirm connection error returns empty list without raising."""
        provider = SearXNGProvider(base_url="http://localhost:8082")

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Failed to connect")
            results = await provider.search("Python FastAPI")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_http_status_error_handling(self):
        """Confirm non-200 HTTP response returns empty list."""
        provider = SearXNGProvider(base_url="http://localhost:8082")

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await provider.search("Python FastAPI")
            assert results == []

    @pytest.mark.asyncio
    async def test_check_health_mocked(self):
        """Confirm check_health correctly detects instance reachability."""
        provider = SearXNGProvider(base_url="http://localhost:8082")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            assert await provider.check_health() is True

            mock_get.side_effect = httpx.ConnectError("Unreachable")
            assert await provider.check_health() is False


class TestSearXNGConnector:
    def test_connector_configuration_development(self, monkeypatch):
        """Confirm connector is configured in development with localhost."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("ENABLE_SEARXNG_CONNECTOR", "true")
        monkeypatch.setenv("SEARXNG_URL", "http://localhost:8082")

        connector = SearXNGConnector()
        assert connector.name == "searxng"
        assert connector.connector_type == "metasearch"
        assert connector.is_configured is True
        assert connector.requires_api_key is False
        assert "SearXNG" in connector.display_name

    def test_connector_configuration_production_guard(self, monkeypatch):
        """Confirm production rejects localhost SearXNG URL to prevent broken cloud deployments."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ENABLE_SEARXNG_CONNECTOR", "true")
        monkeypatch.setenv("SEARXNG_URL", "http://localhost:8082")

        connector = SearXNGConnector()
        assert connector.is_configured is False

        # But remote production URL is allowed
        monkeypatch.setenv("SEARXNG_URL", "https://searxng.secure-intel.internal")
        connector_remote = SearXNGConnector()
        assert connector_remote.is_configured is True

    @pytest.mark.asyncio
    async def test_connector_recursion_depth_limit(self, monkeypatch):
        """Confirm connector enforces recursion budget depth limits."""
        monkeypatch.setenv("DEFAULT_MAX_DEPTH", "3")
        connector = SearXNGConnector()

        # Depth 4 exceeds max depth 3 -> should skip immediately
        results = await connector.search("Test Lead", max_results=5, depth=4)
        assert results == []
