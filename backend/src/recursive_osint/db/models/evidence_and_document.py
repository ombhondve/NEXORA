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

    @property
    def source_url(self) -> Optional[str]:
        return self.document.url if self.document else None

    @property
    def source_title(self) -> Optional[str]:
        return self.document.title if self.document else self.title

    @property
    def connector_name(self) -> Optional[str]:
        return self.document.connector_name if self.document else None

    @property
    def retrieved_at(self) -> Optional[datetime]:
        return self.document.retrieved_at if self.document else self.created_at

    @property
    def publication_date(self) -> Optional[str]:
        return self.document.publication_date if self.document else None

    @property
    def is_simulated(self) -> bool:
        if self.document and self.document.connector_name in ("mock_demo", "mock"):
            return True
        if self.is_verified_source_statement is False:
            return True
        return "simulated" in (self.why_included or "").lower()

    @property
    def source_verification_status(self) -> str:
        if self.is_simulated:
            return "simulated"
        if not self.is_verified_source_statement:
            return "unverified"
        if self.document and self.document.connector_name in ("openalex", "crossref", "wikidata", "wikipedia"):
            return "primary"
        return "secondary"


class DocumentRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_relationships"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    source_doc_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False)
    target_doc_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shared_domain, shared_entities, cites, references
    shared_entities_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
