"""
SearXNG Meta-Search Engine Connector & Reusable Async Provider.
Queries a local or private SearXNG instance using httpx and normalizes
results into NEXORA SearchResultItem models.
"""

import os
from typing import List, Dict, Any, Optional
import httpx

from recursive_osint.config import settings
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem
from recursive_osint.search.deduplication import canonicalize_url

logger = get_logger("connector.searxng")


class SearXNGProvider:
    """
    Reusable asynchronous client for querying SearXNG JSON API endpoints.
    Provides robust timeouts, error resilience, result normalization,
    and intra-batch URL deduplication.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_results: Optional[int] = None,
        default_language: Optional[str] = None,
    ):
        raw_url = base_url or settings.SEARXNG_URL
        self.base_url = (raw_url or "http://localhost:8082").rstrip("/")
        self.timeout = timeout if timeout is not None else settings.SEARXNG_TIMEOUT_SECONDS
        self.max_results = max_results if max_results is not None else settings.SEARXNG_MAX_RESULTS
        self.default_language = default_language or settings.SEARXNG_LANGUAGE

    async def check_health(self) -> bool:
        """Checks if the SearXNG instance is reachable and responsive."""
        if not self.base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 5.0)) as client:
                res = await client.get(f"{self.base_url}/healthz")
                if res.status_code == 200:
                    return True
                # Fallback to root endpoint check
                root_res = await client.get(f"{self.base_url}/")
                return root_res.status_code == 200
        except Exception as e:
            logger.debug("SearXNG health check failed for %s: %s", self.base_url, str(e))
            return False

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        categories: Optional[List[str]] = None,
        engines: Optional[List[str]] = None,
        language: Optional[str] = None,
        pageno: int = 1,
    ) -> List[SearchResultItem]:
        """
        Executes an asynchronous search query against SearXNG.
        Normalizes and deduplicates results into SearchResultItem objects.
        """
        if not query or not query.strip():
            return []

        limit = min(max_results or self.max_results, 50)
        search_endpoint = f"{self.base_url}/search"

        params: Dict[str, Any] = {
            "q": query.strip(),
            "format": "json",
            "language": language or self.default_language,
            "pageno": pageno,
        }

        if categories:
            params["categories"] = ",".join(categories)
        if engines:
            params["engines"] = ",".join(engines)

        headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=settings.CRAWLER_MAX_REDIRECTS,
            ) as client:
                response = await client.get(search_endpoint, params=params, headers=headers)

                if response.status_code != 200:
                    logger.warning(
                        "SearXNG query '%s' returned HTTP %d: %s",
                        query,
                        response.status_code,
                        response.text[:200],
                    )
                    return []

                data = response.json()
                raw_results = data.get("results", [])

                normalized: List[SearchResultItem] = []
                seen_urls: set[str] = set()

                for raw in raw_results:
                    if len(normalized) >= limit:
                        break

                    item = self._normalize_item(raw)
                    if not item:
                        continue

                    canonical = canonicalize_url(item.url)
                    if canonical in seen_urls:
                        continue
                    seen_urls.add(canonical)

                    normalized.append(item)

                return normalized

        except httpx.TimeoutException:
            logger.warning("SearXNG query '%s' timed out after %.1fs", query, self.timeout)
            return []
        except httpx.ConnectError as e:
            logger.warning("SearXNG connection error at %s: %s", self.base_url, str(e))
            return []
        except httpx.HTTPStatusError as e:
            logger.warning("SearXNG HTTP status error: %s", str(e))
            return []
        except Exception as e:
            logger.warning("SearXNG unexpected search error: %s", str(e))
            return []

    def _normalize_item(self, raw: Dict[str, Any]) -> Optional[SearchResultItem]:
        """Normalizes a raw SearXNG JSON result item into a SearchResultItem."""
        url = (raw.get("url") or "").strip()
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return None

        title = (raw.get("title") or "Untitled Document").strip()
        snippet = (raw.get("content") or raw.get("snippet") or "").strip()

        # Engine provenance
        primary_engine = raw.get("engine") or "searxng"
        engines_list = raw.get("engines", [])
        if not engines_list and primary_engine:
            engines_list = [primary_engine]

        source_name = f"searxng:{primary_engine}"

        # Date extraction
        pub_date = raw.get("publishedDate") or raw.get("pubdate") or None
        if pub_date and isinstance(pub_date, str):
            pub_date = pub_date[:10]  # Normalize YYYY-MM-DD

        # Score normalization (SearXNG scores vary by engine, map to 0.0 - 1.0)
        raw_score = raw.get("score")
        if isinstance(raw_score, (int, float)) and raw_score > 0:
            relevance_score = min(1.0, max(0.3, float(raw_score) / 10.0))
        else:
            relevance_score = 0.80

        metadata: Dict[str, Any] = {
            "primary_engine": primary_engine,
            "engines": engines_list,
            "category": raw.get("category", "general"),
            "score": raw.get("score"),
            "thumbnail": raw.get("thumbnail") or None,
        }

        return SearchResultItem(
            title=title,
            url=url,
            snippet=snippet,
            source_name=source_name,
            publication_date=pub_date,
            relevance_score=relevance_score,
            metadata=metadata,
        )


class SearXNGConnector(BaseSourceConnector):
    """
    Integrates SearXNG into the NEXORA Source Connector framework.
    Enables autonomous recursive investigations to utilize SearXNG's multi-engine
    federated discovery capabilities.
    """

    def __init__(self, provider: Optional[SearXNGProvider] = None):
        super().__init__(
            name="searxng",
            display_name="SearXNG Meta-Search Engine",
            connector_type="metasearch",
            rate_limit_per_minute=60,
            requires_api_key=False,
        )
        self.provider = provider or SearXNGProvider()

    @property
    def coverage_info(self) -> str:
        return (
            "Aggregates search results across multiple web search engines (Google, Brave, "
            "DuckDuckGo, Wikipedia, etc.) without tracking or profiling. Configured via local "
            "or internal SearXNG endpoint."
        )

    @property
    def is_configured(self) -> bool:
        """
        Determines if SearXNG is active.
        Guards against serverless production deployments accidentally targeting localhost.
        """
        enable = os.getenv("ENABLE_SEARXNG_CONNECTOR", str(settings.ENABLE_SEARXNG_CONNECTOR)).lower() in ("true", "1")
        if not enable:
            return False

        url = os.getenv("SEARXNG_URL", settings.SEARXNG_URL)
        if not url or not url.strip():
            return False

        # Localhost/127.0.0.1 cannot be reached in serverless cloud production (e.g., Vercel)
        env_name = os.getenv("ENVIRONMENT", settings.ENVIRONMENT).strip().lower()
        if env_name == "production":
            url_lower = url.lower()
            if "localhost" in url_lower or "127.0.0.1" in url_lower or "::1" in url_lower:
                return False
        return True

    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        """Executes search with rate-limiting and recursion depth guards."""
        depth = kwargs.get("depth", 0)
        if depth > settings.DEFAULT_MAX_DEPTH:
            logger.debug("SearXNG search skipped: depth %d exceeds max %d", depth, settings.DEFAULT_MAX_DEPTH)
            return []

        self.check_rate_limit()

        categories = kwargs.get("categories")
        engines = kwargs.get("engines")
        language = kwargs.get("language")

        return await self.provider.search(
            query=query,
            max_results=max_results,
            categories=categories,
            engines=engines,
            language=language,
        )
