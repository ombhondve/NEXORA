"""
Pydantic Schemas for Phase 2 AI Intelligence Layer.
Includes structured output models for Evidence Summarization, Entity Extraction,
Relationship Discovery, Investigation Q&A, and AI Reports.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AIHealthResponse(BaseModel):
    status: str = Field(..., description="Operational status: ready, fallback_active, rate_limited, quota_exhausted, configuration_error, disabled, unavailable")
    provider: str = Field(default="gemini", description="Active AI provider: gemini or groq")
    model: str = Field(..., description="Active model name")
    primary_provider: str = "gemini"
    fallback_provider: str = "groq"
    details: str
    gemini_status: Optional[str] = None
    groq_status: Optional[str] = None


class AIEvidenceSummaryItem(BaseModel):
    evidence_id: str
    source_title: str
    main_subject: str
    key_facts: List[str] = Field(default_factory=list)
    relevance_to_investigation: str
    limitations: Optional[str] = None


class AIEntityCandidate(BaseModel):
    entity_type: str  # organization, person, domain, product, location, identifier
    entity_value: str
    normalized_value: str
    evidence_ids: List[str] = Field(default_factory=list)
    context_snippet: str = ""
    confidence: float = 0.70


class AIRelationshipCandidate(BaseModel):
    source_entity: str
    target_entity: str
    relationship_type: str
    relationship_kind: str = "inferred"  # direct, inferred, unverified
    evidence_ids: List[str] = Field(default_factory=list)
    explanation: str
    confidence: float = 0.65


class AIInvestigationAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investigation_id: str
    model_name: str
    objective: str
    executive_summary: str
    key_findings: List[str] = Field(default_factory=list)
    evidence_summaries: List[AIEvidenceSummaryItem] = Field(default_factory=list)
    entities: List[AIEntityCandidate] = Field(default_factory=list)
    relationships: List[AIRelationshipCandidate] = Field(default_factory=list)
    conflicts_and_limitations: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    unverified_claims: List[str] = Field(default_factory=list)
    analyzed_evidence_count: int = 0
    created_at: Optional[datetime] = None


class AIQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Natural-language question regarding investigation evidence")


class AIQuestionResponse(BaseModel):
    investigation_id: str
    question: str
    answer: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    supporting_source_urls: List[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    confidence_assessment: str = "medium"


class AIReportRequest(BaseModel):
    format: str = "markdown"
