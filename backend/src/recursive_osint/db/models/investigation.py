"""
Investigation, Runs, Events, and Reports models.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import DateTime, ForeignKey, Integer, Float, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from recursive_osint.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Investigation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "investigations"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_clue: Mapped[str] = mapped_column(Text, nullable=False)
    clue_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)  # text, name, domain, url, image, pdf
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)  # pending, running, paused, completed, cancelled, failed
    
    # Recursion limits and budgets
    max_depth: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_total_queries: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    max_execution_seconds: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    budget_limits_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Progress & Stopping status
    current_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stop_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="investigations")
    runs = relationship("InvestigationRun", back_populates="investigation", cascade="all, delete-orphan")
    queries = relationship("SearchQuery", back_populates="investigation", cascade="all, delete-orphan")
    leads = relationship("DiscoveryLead", back_populates="investigation", cascade="all, delete-orphan")
    documents = relationship("SourceDocument", back_populates="investigation", cascade="all, delete-orphan")
    evidence = relationship("EvidenceRecord", back_populates="investigation", cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="investigation", cascade="all, delete-orphan")
    events = relationship("InvestigationEvent", back_populates="investigation", cascade="all, delete-orphan")
    reports = relationship("ReportExport", back_populates="investigation", cascade="all, delete-orphan")


class InvestigationRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "investigation_runs"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)
    current_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queries_executed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads_evaluated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_downloaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="runs")


class InvestigationEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "investigation_events"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # lead_discovered, query_executed, doc_fetched, entity_extracted, error
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    investigation = relationship("Investigation", back_populates="events")


class ReportExport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "report_exports"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)  # markdown, json, pdf
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    content: Mapped[Text] = mapped_column(Text, nullable=False)

    investigation = relationship("Investigation", back_populates="reports")
