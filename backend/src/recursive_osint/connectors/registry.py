"""
Connector Registry for discovering and dispatching across active connectors.
"""

from typing import Dict, List, Optional
from recursive_osint.config import settings
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.connectors.wikipedia import WikipediaConnector
from recursive_osint.connectors.internet_archive import InternetArchiveConnector
from recursive_osint.connectors.open_datasets import OpenDatasetsConnector
from recursive_osint.connectors.mock_demo import MockDemoConnector
from recursive_osint.connectors.searxng import SearXNGConnector
from recursive_osint.core.logging import get_logger

logger = get_logger("connectors.registry")


class ConnectorRegistry:
    """Manages active source connectors."""

    def __init__(self):
        self._connectors: Dict[str, BaseSourceConnector] = {}
        self._register_default_connectors()

    def _register_default_connectors(self) -> None:
        if settings.ENABLE_WIKIPEDIA_CONNECTOR:
            self.register(WikipediaConnector())

        if settings.ENABLE_INTERNET_ARCHIVE_CONNECTOR:
            self.register(InternetArchiveConnector())

        if settings.ENABLE_CROSSREF_CONNECTOR:
            self.register(OpenDatasetsConnector())

        if settings.ENABLE_MOCK_DEMO_CONNECTOR:
            self.register(MockDemoConnector())

        if settings.ENABLE_SEARXNG_CONNECTOR:
            self.register(SearXNGConnector())

    def register(self, connector: BaseSourceConnector) -> None:
        self._connectors[connector.name] = connector
        logger.info("Registered source connector: %s", connector.name)

    def get(self, name: str) -> Optional[BaseSourceConnector]:
        return self._connectors.get(name)

    def list_all(self) -> List[BaseSourceConnector]:
        return list(self._connectors.values())

    def list_enabled(self) -> List[BaseSourceConnector]:
        return [c for c in self._connectors.values() if c.is_configured]


connector_registry = ConnectorRegistry()
