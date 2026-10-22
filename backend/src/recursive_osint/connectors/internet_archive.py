"""
Internet Archive Wayback Machine & Metadata Connector.
Queries public historical web captures and metadata without requiring an API key.
"""

from typing import List, Any
import urllib.parse
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connector.internet_archive")


class InternetArchiveConnector(BaseSourceConnector):
    """Searches the Internet Archive's public metadata search API."""

    def __init__(self):
        super().__init__(
            name="internet_archive",
            display_name="Internet Archive Historical Data",
            connector_type="archive",
            rate_limit_per_minute=30,
            requires_api_key=False,
        )
        self.endpoint = "https://archive.org/advancedsearch.php"

    @property
    def coverage_info(self) -> str:
        return (
            "Searches millions of public archived web pages, public domain books, documents, "
            "and historical datasets maintained by archive.org."
        )

    @property
    def is_configured(self) -> bool:
        return True

    async def check_health(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "unconfigured"
        try:
            res = await self._safe_http_get(
                self.endpoint,
                params={"q": "collection:test", "rows": 1, "output": "json"},
                timeout=4.0,
            )
            return (True, "online") if res.status_code == 200 else (False, "offline")
        except Exception:
            return False, "offline"

    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        # Construct search query across metadata
        q_encoded = f'({query}) AND mediatype:(texts OR web OR data)'
        params = {
            "q": q_encoded,
            "fl[]": ["identifier", "title", "description", "publicdate", "mediatype"],
            "sort[]": "publicdate desc",
            "rows": min(max_results, 15),
            "output": "json",
        }

        try:
            res = await self._safe_http_get(self.endpoint, params=params)
            data = res.json()
            docs = data.get("response", {}).get("docs", [])

            results: List[SearchResultItem] = []
            for doc in docs:
                identifier = doc.get("identifier", "")
                title = doc.get("title", identifier)
                description = doc.get("description", "")
                if isinstance(description, list):
                    description = " ".join(description)
                snippet = description[:300] if description else f"Archived record: {identifier}"
                pub_date = doc.get("publicdate", "")
                item_url = f"https://archive.org/details/{identifier}"

                results.append(
                    SearchResultItem(
                        title=title,
                        url=item_url,
                        snippet=snippet,
                        source_name=self.name,
                        publication_date=pub_date[:10] if pub_date else None,
                        relevance_score=0.75,
                        metadata={"identifier": identifier, "mediatype": doc.get("mediatype")},
                    )
                )
            return results
        except Exception as e:
            logger.warning("Internet Archive query '%s' failed: %s", query, str(e))
            return []
