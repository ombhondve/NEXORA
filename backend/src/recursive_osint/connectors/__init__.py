"""
Source Connectors package.
"""

from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.connectors.registry import connector_registry
from recursive_osint.connectors.wikipedia import WikipediaConnector
from recursive_osint.connectors.internet_archive import InternetArchiveConnector
from recursive_osint.connectors.open_datasets import OpenDatasetsConnector
from recursive_osint.connectors.mock_demo import MockDemoConnector

__all__ = [
    "BaseSourceConnector",
    "connector_registry",
    "WikipediaConnector",
    "InternetArchiveConnector",
    "OpenDatasetsConnector",
    "MockDemoConnector",
]
