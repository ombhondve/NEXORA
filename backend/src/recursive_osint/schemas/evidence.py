"""
Evidence, Source Documents, and Entity schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvidenceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    document_id: Optional[str] = None
    title: str
    extracted_passage: str
    relevance_score: float
    uncertainty_score: float
    confidence_level: str
    why_included: str
    is_verified_source_statement: bool
    contradictions_noted: Optional[str] = None
    created_at: datetime


class SourceDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    connector_name: str
    title: str
    url: str
    canonical_url: str
    snippet: str
    mime_type: str
    publication_date: Optional[str] = None
    retrieved_at: datetime


class ExtractedEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    document_id: Optional[str] = None
    entity_type: str
    entity_value: str
    normalized_value: str
    confidence: float
    context_snippet: Optional[str] = None


class EntityRelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    confidence: float
    provenance_notes: Optional[str] = None


class SourceConnectorStatusResponse(BaseModel):
    name: str
    display_name: str
    connector_type: str
    is_enabled: bool
    rate_limit_per_minute: int
    coverage_info: str
    requires_api_key: bool
    is_configured: bool
    health_status: str = "online"
    is_simulated: bool = False


class InvestigationReportResponse(BaseModel):
    investigation_id: str
    title: str
    target_clue: str
    status: str
    summary_markdown: str
    total_sources_scanned: int
    total_evidence_collected: int
    total_entities_correlated: int
    generated_at: datetime
