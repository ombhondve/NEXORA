"""
Search and Discovery endpoints.
"""

from fastapi import APIRouter, Depends
from recursive_osint.api.dependencies import get_current_user
from recursive_osint.db.models.user import User
from recursive_osint.schemas.search import SearchRequest, SearchResponse
from recursive_osint.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def execute_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Executes on-demand multi-source OSINT discovery search."""
    return await SearchService.execute_search(request)
