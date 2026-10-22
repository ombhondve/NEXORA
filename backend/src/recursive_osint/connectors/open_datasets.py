"""
Open Academic & Scientific Datasets Connector (CrossRef).
Queries open metadata for millions of published papers, technical reports, and authors.
"""

from typing import List, Any
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connector.open_datasets")


class OpenDatasetsConnector(BaseSourceConnector):
    """Queries CrossRef's open scholarly infrastructure API."""

    def __init__(self):
        super().__init__(
            name="open_datasets",
            display_name="Open Scholarly & Technical Datasets",
            connector_type="open_data",
            rate_limit_per_minute=50,
            requires_api_key=False,
        )
        self.endpoint = "https://api.crossref.org/works"

    @property
    def coverage_info(self) -> str:
        return (
            "Accesses public research literature, preprints, patents, authors, and technical affiliations. "
            "Operated by CrossRef with open public access."
        )

    @property
    def is_configured(self) -> bool:
        return True

    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        params = {
            "query": query,
            "rows": min(max_results, 10),
            "select": "DOI,title,URL,author,created,publisher",
        }

        try:
            res = await self._safe_http_get(self.endpoint, params=params)
            data = res.json()
            items = data.get("message", {}).get("items", [])

            results: List[SearchResultItem] = []
            for item in items:
                titles = item.get("title", [])
                title = titles[0] if titles else "Untitled publication"
                url = item.get("URL") or f"https://doi.org/{item.get('DOI', '')}"
                
                # Format authors for snippet
                authors = item.get("author", [])
                author_names = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors[:3]]
                author_str = ", ".join(author_names) if author_names else "Unknown Author"
                publisher = item.get("publisher", "Academic Publisher")
                snippet = f"Authors: {author_str}. Published by: {publisher}."

                created_parts = item.get("created", {}).get("date-parts", [[]])[0]
                pub_date = "-".join(str(p).zfill(2) for p in created_parts[:3]) if created_parts else None

                results.append(
                    SearchResultItem(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source_name=self.name,
                        publication_date=pub_date,
                        relevance_score=0.70,
                        metadata={"doi": item.get("DOI"), "publisher": publisher},
                    )
                )
            return results
        except Exception as e:
            logger.warning("Open datasets query '%s' failed: %s", query, str(e))
            return []
