"""
Mock / Demonstration Connector for Deterministic Offline Testing.
Clearly labeled as simulated data.
"""

from typing import List, Any
import hashlib
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.schemas.search import SearchResultItem


class MockDemoConnector(BaseSourceConnector):
    """Provides deterministic, mock discovery records for offline tests and demos."""

    def __init__(self):
        super().__init__(
            name="mock_demo",
            display_name="Mock Demo Source (Hermetic)",
            connector_type="mock",
            rate_limit_per_minute=200,
            requires_api_key=False,
        )

    @property
    def coverage_info(self) -> str:
        return (
            "[DEMO / TEST ONLY] Deterministic simulated records representing "
            "public organizations, research papers, news reports, and domains for offline testing."
        )

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def is_simulated(self) -> bool:
        return True

    async def check_health(self) -> tuple[bool, str]:
        return True, "simulated"

    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        q_lower = query.lower().strip()
        results: List[SearchResultItem] = []

        # Simulated records based on query patterns
        seed_hash = int(hashlib.md5(query.encode("utf-8")).hexdigest(), 16) % 1000

        results.append(
            SearchResultItem(
                title=f"[Simulated Record] Public Registry profile for '{query}'",
                url=f"https://example.org/registry/{seed_hash}",
                snippet=f"Official open registry entry regarding {query}. Entity was registered in Geneva with verified public filings.",
                source_name=self.name,
                publication_date="2024-03-15",
                relevance_score=0.92,
                metadata={"type": "corporate_registry", "simulated": True},
            )
        )

        results.append(
            SearchResultItem(
                title=f"[Simulated Record] Technical Whitepaper citing '{query}'",
                url=f"https://example.org/papers/{seed_hash}_analysis",
                snippet=f"In-depth research paper analyzing infrastructure associated with {query} and partner consortium NEXORA Alliance.",
                source_name=self.name,
                publication_date="2024-06-20",
                relevance_score=0.88,
                metadata={"type": "scholarly_paper", "simulated": True},
            )
        )

        results.append(
            SearchResultItem(
                title=f"[Simulated Record] Press Release: Strategic Announcement concerning '{query}'",
                url=f"https://example.org/news/{seed_hash}_announcement",
                snippet=f"Global consortium updates regarding operations related to {query}. Highlights ongoing open-source initiatives and domain network.",
                source_name=self.name,
                publication_date="2024-08-01",
                relevance_score=0.79,
                metadata={"type": "press_release", "simulated": True},
            )
        )

        return results[:max_results]
