"""
Investigation AI Analysis model.
Stores structured AI-derived intelligence summaries, findings, extracted entities,
relationship candidates, and limitations.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from recursive_osint.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InvestigationAIAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "investigation_ai_analyses"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings_json: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    evidence_summaries_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    entities_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    relationships_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    conflicts_and_limitations_json: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    missing_information_json: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    unverified_claims_json: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    analyzed_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)

    investigation = relationship("Investigation", back_populates="ai_analyses")
