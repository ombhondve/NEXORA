"""
Abstract Base Class for all Source Connectors.
Enforces SSRF validation, rate limiting, and standard error handling.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

from recursive_osint.config import settings
from recursive_osint.core.exceptions import ConnectorError
from recursive_osint.core.logging import get_logger
from recursive_osint.core.rate_limit import SlidingWindowRateLimiter
from recursive_osint.core.security import validate_url_safe
from recursive_osint.schemas.search import SearchResultItem

logger = get_logger("connectors")


class BaseSourceConnector(ABC):
    """Abstract base connector for discovering public internet data."""

    def __init__(
        self,
        name: str,
        display_name: str,
        connector_type: str,
        rate_limit_per_minute: int = 30,
        requires_api_key: bool = False,
    ):
        self.name = name
        self.display_name = display_name
        self.connector_type = connector_type
        self.rate_limit_per_minute = rate_limit_per_minute
        self.requires_api_key = requires_api_key
        self.rate_limiter = SlidingWindowRateLimiter(
            max_requests=rate_limit_per_minute, window_seconds=60
        )

    @property
    @abstractmethod
    def coverage_info(self) -> str:
        """Documentation of the connector's source coverage, capabilities, and restrictions."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the connector has all necessary credentials/configurations to operate."""
        pass

    @property
    def is_simulated(self) -> bool:
        """Indicates whether this connector yields simulated / demo records rather than real external data."""
        return False

    async def check_health(self) -> tuple[bool, str]:
        """
        Actively checks whether the provider endpoint is healthy and reachable.
        Returns: (is_healthy, status_message)
        """
        if not self.is_configured:
            return False, "unconfigured"
        return True, "online"

    @abstractmethod
    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> List[SearchResultItem]:
        """Execute a search query against the source."""
        pass

    def check_rate_limit(self) -> None:
        """Checks and enforces the connector rate limit."""
        self.rate_limiter.check(self.name)

    async def _safe_http_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """
        Executes a secure outbound GET request with pre-flight SSRF validation.
        """
        self.check_rate_limit()
        safe_url = validate_url_safe(url)

        req_headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "application/json, text/html, */*",
        }
        if headers:
            req_headers.update(headers)

        req_timeout = timeout or settings.CRAWLER_TIMEOUT_SECONDS

        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=settings.CRAWLER_MAX_REDIRECTS,
            timeout=req_timeout,
        ) as client:
            try:
                response = await client.get(safe_url, params=params, headers=req_headers)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                logger.warning("Connector %s received HTTP %d for %s", self.name, e.response.status_code, safe_url)
                raise ConnectorError(f"HTTP {e.response.status_code} from {self.name}: {e.response.text[:200]}")
            except httpx.RequestError as e:
                logger.warning("Connector %s network error: %s", self.name, str(e))
                raise ConnectorError(f"Network error in {self.name}: {str(e)}")
