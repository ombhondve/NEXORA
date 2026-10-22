"""
Search and Discovery endpoints.
"""

from fastapi import APIRouter, Request
from recursive_osint.core.rate_limit import search_rate_limiter
from recursive_osint.schemas.search import SearchRequest, SearchResponse
from recursive_osint.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def execute_search(
    request: Request,
    body: SearchRequest,
):
    """Executes on-demand multi-source OSINT discovery search without requiring authentication."""
    # Enforce client rate limiting based on remote IP
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    search_rate_limiter.check(f"search:{client_ip}")

    return await SearchService.execute_search(body)

