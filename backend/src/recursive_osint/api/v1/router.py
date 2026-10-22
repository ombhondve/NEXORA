"""
API v1 root router aggregator.
"""

from fastapi import APIRouter
from recursive_osint.api.v1.endpoints import (
    auth,
    investigations,
    search,
    sources,
    health,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(investigations.router)
api_v1_router.include_router(search.router)
api_v1_router.include_router(sources.router)
