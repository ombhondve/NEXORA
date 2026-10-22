"""
Wikipedia Open Knowledge API Connector.
Queries open public encyclopedic articles and metadata without requiring an API key.
"""

from typing import List, Any
import urllib.parse
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connector.wikipedia")


class WikipediaConnector(BaseSourceConnector):
    """Searches Wikipedia's public MediaWiki action API."""

    def __init__(self):
        super().__init__(
            name="wikipedia",
            display_name="Wikipedia Open Knowledge",
            connector_type="open_data",
            rate_limit_per_minute=45,
            requires_api_key=False,
        )
        self.endpoint = "https://en.wikipedia.org/w/api.php"

    @property
    def coverage_info(self) -> str:
        return (
            "Accesses public Wikipedia articles, biographical records, organizations, "
            "and historical events. Free public API with standard polite user-agent header."
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
                params={"action": "query", "meta": "siteinfo", "format": "json"},
                timeout=4.0,
            )
            return (True, "online") if res.status_code == 200 else (False, "offline")
        except Exception:
            return False, "offline"

    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "",
            "format": "json",
            "srlimit": min(max_results, 20),
        }

        try:
            res = await self._safe_http_get(self.endpoint, params=params)
            data = res.json()
            search_items = data.get("query", {}).get("search", [])

            results: List[SearchResultItem] = []
            for item in search_items:
                title = item.get("title", "")
                snippet_raw = item.get("snippet", "")
                # Clean basic HTML tags from snippet
                snippet = snippet_raw.replace('<span class="searchmatch">', "").replace("</span>", "")
                timestamp = item.get("timestamp", "")
                encoded_title = urllib.parse.quote(title.replace(" ", "_"))
                page_url = f"https://en.wikipedia.org/wiki/{encoded_title}"

                results.append(
                    SearchResultItem(
                        title=title,
                        url=page_url,
                        snippet=snippet,
                        source_name=self.name,
                        publication_date=timestamp[:10] if timestamp else None,
                        relevance_score=0.85,
                        metadata={"wordcount": item.get("wordcount", 0), "pageid": item.get("pageid")},
                    )
                )
            return results
        except Exception as e:
            logger.warning("Wikipedia query '%s' failed: %s", query, str(e))
            return []
