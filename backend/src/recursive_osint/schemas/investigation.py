"""
Investigation schemas.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: Optional[str] = None
    target_clue: str = Field(min_length=2, max_length=500, description="Target entity, domain, phrase, or clue")
    clue_type: str = Field(default="text", description="text, name, domain, url, image, pdf")
    max_depth: int = Field(default=3, ge=1, le=5)
    max_total_queries: int = Field(default=25, ge=1, le=100)
    max_execution_seconds: int = Field(default=600, ge=30, le=3600)
    enabled_sources: Optional[List[str]] = None


class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_clue: str
    clue_type: str
    status: str
    max_depth: int
    current_depth: int
    max_total_queries: int
    progress_percent: int
    stop_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime



class InvestigationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    event_type: str
    message: str
    details_json: Dict[str, Any]
    created_at: datetime


class QueryLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query_text: str
    source_name: str
    depth: int
    status: str
    results_count: int
    execution_duration_ms: float
    created_at: datetime


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # seed, text, domain, entity, url, phrase, source
    depth: int = 0
    status: str = "active"
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str = "discovered"
    confidence: Optional[float] = None
    relationship_kind: str = "direct"  # direct, inferred, unverified
    evidence_id: Optional[str] = None
    evidence_title: Optional[str] = None
    source_url: Optional[str] = None
    confidence_rationale: Optional[str] = None
    origin: str = "deterministic"  # source_derived, deterministic, ai_inferred


class LeadGraphResponse(BaseModel):
    investigation_id: str
    target_clue: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
    is_empty: bool = False
