"""
GitHub Public Technical & Code Metadata Connector.
Queries public software repositories, organizations, releases, and development artifacts.
Respects GitHub's API rate limits and terms of service.
"""

from typing import List, Any, Dict, Optional
from recursive_osint.config import settings
from recursive_osint.connectors.base import BaseSourceConnector
from recursive_osint.core.logging import get_logger
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connector.github")


class GitHubPublicConnector(BaseSourceConnector):
    """Searches GitHub's public repository and developer metadata API."""

    def __init__(self):
        super().__init__(
            name="github_public",
            display_name="GitHub Public Repositories & Tech",
            connector_type="code_repository",
            rate_limit_per_minute=30 if settings.GITHUB_TOKEN else 10,
            requires_api_key=False,
        )
        self.endpoint = "https://api.github.com/search/repositories"

    @property
    def coverage_info(self) -> str:
        return (
            "Accesses public open-source software repositories, developer organizations, "
            "licenses, and release metadata indexed across GitHub. Uses public unauthenticated "
            "or token-authenticated API."
        )

    @property
    def is_configured(self) -> bool:
        return True

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.GITHUB_TOKEN and settings.GITHUB_TOKEN.strip():
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN.strip()}"
        return headers

    async def check_health(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "unconfigured"
        try:
            res = await self._safe_http_get(
                "https://api.github.com/zen",
                headers=self._get_headers(),
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

        limit = min(max_results, 15)
        params = {
            "q": query.strip(),
            "per_page": limit,
            "sort": "stars",
            "order": "desc",
        }

        try:
            res = await self._safe_http_get(
                self.endpoint,
                params=params,
                headers=self._get_headers(),
            )
            data = res.json()
            items = data.get("items", [])

            results: List[SearchResultItem] = []
            for item in items:
                full_name = item.get("full_name") or item.get("name", "Unknown Repository")
                html_url = item.get("html_url") or f"https://github.com/{full_name}"
                desc = item.get("description") or "No description provided."
                stars = item.get("stargazers_count", 0)
                forks = item.get("forks_count", 0)
                lang = item.get("language") or "General"
                updated_at = item.get("updated_at")
                pub_date = updated_at[:10] if updated_at else None

                license_info = (item.get("license") or {}).get("spdx_id") or "Unspecified"
                snippet = (
                    f"Repository: {full_name} | Language: {lang} | "
                    f"Stars: {stars} | Forks: {forks} | License: {license_info}. {desc}"
                )

                results.append(
                    SearchResultItem(
                        title=f"{full_name} ({lang})",
                        url=html_url,
                        snippet=snippet,
                        source_name=self.name,
                        publication_date=pub_date,
                        relevance_score=0.80,
                        metadata={
                            "stars": stars,
                            "forks": forks,
                            "language": lang,
                            "license": license_info,
                            "owner": (item.get("owner") or {}).get("login"),
                        },
                    )
                )

            return results
        except Exception as e:
            logger.warning("GitHub public search '%s' failed: %s", query, str(e))
            return []
