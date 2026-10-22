"""
Wikidata Structured Public Knowledge Graph Connector.
Queries open semantic entities, identifiers, relationships, and descriptions without requiring an API key.
"""

from typing import List, Any
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connector.wikidata")


class WikidataConnector(BaseSourceConnector):
    """Searches Wikidata's public semantic entity API."""

    def __init__(self):
        super().__init__(
            name="wikidata",
            display_name="Wikidata Knowledge Graph",
            connector_type="knowledge_graph",
            rate_limit_per_minute=45,
            requires_api_key=False,
        )
        self.endpoint = "https://www.wikidata.org/w/api.php"

    @property
    def coverage_info(self) -> str:
        return (
            "Accesses structured public knowledge records, entity identifiers (Q-numbers), "
            "aliases, corporate parentage, and entity descriptions across Wikidata's open graph."
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
                params={"action": "wbsearchentities", "search": "entity", "language": "en", "format": "json", "limit": 1},
                timeout=4.0,
            )
            return (True, "online") if res.status_code == 200 else (False, "offline")
        except Exception:
            return False, "offline"

    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        if not query or not query.strip():
            return []

        limit = min(max_results, 20)
        params = {
            "action": "wbsearchentities",
            "search": query.strip(),
            "language": "en",
            "format": "json",
            "limit": limit,
            "type": "item",
        }

        try:
            res = await self._safe_http_get(self.endpoint, params=params)
            data = res.json()
            search_items = data.get("search", [])

            results: List[SearchResultItem] = []
            for item in search_items:
                qid = item.get("id", "")
                label = item.get("label", qid)
                description = item.get("description", "Wikidata entity")
                aliases = item.get("aliases", [])
                alias_str = f" (Also known as: {', '.join(aliases[:3])})" if aliases else ""

                item_url = item.get("concepturi") or f"https://www.wikidata.org/wiki/{qid}"
                snippet = f"Entity [{qid}]: {description}{alias_str}."

                results.append(
                    SearchResultItem(
                        title=f"{label} ({qid})",
                        url=item_url,
                        snippet=snippet,
                        source_name=self.name,
                        publication_date=None,
                        relevance_score=0.86,
                        metadata={
                            "qid": qid,
                            "label": label,
                            "description": description,
                            "aliases": aliases,
                        },
                    )
                )

            return results
        except Exception as e:
            logger.warning("Wikidata search '%s' failed: %s", query, str(e))
            return []
