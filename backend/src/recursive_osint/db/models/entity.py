"""
Extracted Entities and Entity Relationships models.
"""

from typing import Optional
from sqlalchemy import ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from recursive_osint.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExtractedEntity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "extracted_entities"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # person, organization, domain, email, location, date, identifier
    entity_value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    context_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="entities")


class EntityRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "entity_relationships"

    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), index=True, nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("extracted_entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(36), ForeignKey("extracted_entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)  # affiliated_with, referenced_in, co_occurs, alias_of
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    provenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
