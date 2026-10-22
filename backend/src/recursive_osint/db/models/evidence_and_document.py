"""
Source Documents, Evidence Records, and Document Relationships models.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import DateTime, ForeignKey, Integer, Float, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from recursive_osint.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SourceDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_documents"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    connector_name: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SHA-256
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clean_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="text/html", nullable=False)
    publication_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    headers_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_retained: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    investigation = relationship("Investigation", back_populates="documents")
    evidence = relationship("EvidenceRecord", back_populates="document", cascade="all, delete-orphan")


class EvidenceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence_records"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_passage: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 to 1.0
    uncertainty_score: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)  # 0.0 to 1.0
    confidence_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # high, medium, low, unverified
    why_included: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified_source_statement: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contradictions_noted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="evidence")
    document = relationship("SourceDocument", back_populates="evidence")


class DocumentRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_relationships"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    source_doc_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False)
    target_doc_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shared_domain, shared_entities, cites, references
    shared_entities_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
