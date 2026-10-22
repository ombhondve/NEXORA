"""
OpenAlex Scholarly & Technical Research Graph Connector.
Queries open bibliographic records, authors, institutions, and citations across 250M+ scientific works.
Free public API with polite rate limits.
"""

from typing import List, Any, Optional
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connector.openalex")


class OpenAlexConnector(BaseSourceConnector):
    """Queries OpenAlex's open public academic knowledge graph API."""

    def __init__(self):
        super().__init__(
            name="openalex",
            display_name="OpenAlex Scholarly Knowledge Graph",
            connector_type="scholarly",
            rate_limit_per_minute=60,
            requires_api_key=False,
        )
        self.endpoint = "https://api.openalex.org/works"

    @property
    def coverage_info(self) -> str:
        return (
            "Accesses 250M+ open scientific works, author affiliations, citations, datasets, "
            "and research institutions indexed across the global scholarly knowledge graph. Free public API."
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
                params={"per_page": 1},
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

        limit = min(max_results, 25)
        params = {
            "search": query.strip(),
            "per_page": limit,
            "mailto": "osint-discovery@nexora.org",
        }

        try:
            res = await self._safe_http_get(self.endpoint, params=params)
            data = res.json()
            works = data.get("results", [])

            results: List[SearchResultItem] = []
            for work in works:
                title = work.get("display_name") or work.get("title") or "Untitled Scholarly Work"
                doi = work.get("doi")
                landing_url = (
                    (work.get("primary_location") or {}).get("landing_page_url")
                    or doi
                    or work.get("id")
                    or f"https://openalex.org/{work.get('id', '')}"
                )

                # Extract authors
                authorships = work.get("authorships", [])
                author_names = [
                    (a.get("author") or {}).get("display_name", "")
                    for a in authorships[:3]
                    if (a.get("author") or {}).get("display_name")
                ]
                author_str = ", ".join(author_names) if author_names else "Unknown Author"

                # Publication metadata
                pub_year = work.get("publication_year")
                pub_date = work.get("publication_date")
                cited_by = work.get("cited_by_count", 0)
                concepts = [
                    c.get("display_name", "")
                    for c in work.get("concepts", [])[:3]
                    if c.get("display_name")
                ]
                concepts_str = f" | Topics: {', '.join(concepts)}" if concepts else ""

                snippet = (
                    f"Authors: {author_str} ({pub_year or 'n.d.'}). "
                    f"Cited by {cited_by} works{concepts_str}."
                )

                results.append(
                    SearchResultItem(
                        title=title,
                        url=landing_url,
                        snippet=snippet,
                        source_name=self.name,
                        publication_date=pub_date or (str(pub_year) if pub_year else None),
                        relevance_score=0.82,
                        metadata={
                            "openalex_id": work.get("id"),
                            "doi": doi,
                            "cited_by_count": cited_by,
                            "type": work.get("type"),
                        },
                    )
                )

            return results
        except Exception as e:
            logger.warning("OpenAlex search '%s' failed: %s", query, str(e))
            return []
