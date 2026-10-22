"""
Search Queries, Discovery Leads, and Source Connector Config models.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import Boolean, ForeignKey, Integer, Float, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from recursive_osint.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SourceConnectorConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_connectors"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)  # archive, search_api, web_crawler, open_data, mock
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    coverage_info: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class SearchQuery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "search_queries"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    query_text: Mapped[str] = mapped_column(String(500), nullable=False)
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, executing, completed, failed
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="queries")


class DiscoveryLead(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "discovery_leads"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    parent_lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("discovery_leads.id", ondelete="SET NULL"), nullable=True)
    lead_type: Mapped[str] = mapped_column(String(50), nullable=False)  # entity, domain, phrase, document, handle
    lead_value: Mapped[str] = mapped_column(String(500), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # Higher is prioritized
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True, nullable=False)  # queued, evaluating, expanded, exhausted, discarded
    discovery_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    similarity_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    investigation = relationship("Investigation", back_populates="leads")
    parent_lead = relationship("DiscoveryLead", remote_side="DiscoveryLead.id", backref="child_leads")
