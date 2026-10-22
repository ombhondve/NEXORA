"""
Direct Search and Lead schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    source_categories: Optional[List[str]] = None
    max_results: int = Field(default=10, ge=1, le=50)
    language: Optional[str] = "en"


class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str
    source_name: str
    publication_date: Optional[str] = None
    relevance_score: float = 0.5
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    query: str
    total_results: int
    execution_time_ms: float
    results: List[SearchResultItem]


class DiscoveryLeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    parent_lead_id: Optional[str] = None
    lead_type: str
    lead_value: str
    depth: int
    priority_score: float
    status: str
    discovery_reason: str
    created_at: datetime
