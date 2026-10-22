"""
Source connectors discovery status endpoint.
"""

from typing import List
from fastapi import APIRouter
from recursive_osint.schemas.evidence import SourceConnectorStatusResponse
from recursive_osint.services.search_service import SearchService

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=List[SourceConnectorStatusResponse])
async def list_sources():
    """Returns coverage and operational status for all registered source connectors."""
    return SearchService.get_source_statuses()
