"""
Search Service for on-demand multi-source search and connector management.
"""

import time
from typing import List, Dict, Any
from recursive_osint.connectors.registry import connector_registry
from recursive_osint.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from recursive_osint.schemas.evidence import SourceConnectorStatusResponse


class SearchService:
    @staticmethod
    async def execute_search(request: SearchRequest) -> SearchResponse:
        start_time = time.perf_counter()
        results: List[SearchResultItem] = []

        active_connectors = connector_registry.list_enabled()
        # Filter connectors if categories are specified
        if request.source_categories:
            active_connectors = [
                c for c in active_connectors
                if c.name in request.source_categories or c.connector_type in request.source_categories
            ]

        for connector in active_connectors:
            try:
                res = await connector.search(request.query, max_results=request.max_results)
                results.extend(res)
            except Exception:
                continue

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            execution_time_ms=duration_ms,
            results=results,
        )

    @staticmethod
    def get_source_statuses() -> List[SourceConnectorStatusResponse]:
        connectors = connector_registry.list_all()
        return [
            SourceConnectorStatusResponse(
                name=c.name,
                display_name=c.display_name,
                connector_type=c.connector_type,
                is_enabled=True,
                rate_limit_per_minute=c.rate_limit_per_minute,
                coverage_info=c.coverage_info,
                requires_api_key=c.requires_api_key,
                is_configured=c.is_configured,
            )
            for c in connectors
        ]
