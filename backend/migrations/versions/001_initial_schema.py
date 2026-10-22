"""Initial Schema for Recursive OSINT Engine

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-22 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), default='investigator', nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('api_key', sa.String(64), unique=True, index=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Role Permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('role', sa.String(50), index=True, nullable=False),
        sa.Column('permission', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Investigations table
    op.create_table(
        'investigations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_clue', sa.Text(), nullable=False),
        sa.Column('clue_type', sa.String(50), default='text', nullable=False),
        sa.Column('status', sa.String(50), default='pending', index=True, nullable=False),
        sa.Column('max_depth', sa.Integer(), default=3, nullable=False),
        sa.Column('max_total_queries', sa.Integer(), default=25, nullable=False),
        sa.Column('max_execution_seconds', sa.Integer(), default=600, nullable=False),
        sa.Column('budget_limits_json', sa.JSON(), nullable=False),
        sa.Column('current_depth', sa.Integer(), default=0, nullable=False),
        sa.Column('progress_percent', sa.Integer(), default=0, nullable=False),
        sa.Column('stop_reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Investigation Runs table
    op.create_table(
        'investigation_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('status', sa.String(50), default='running', nullable=False),
        sa.Column('current_depth', sa.Integer(), default=0, nullable=False),
        sa.Column('queries_executed', sa.Integer(), default=0, nullable=False),
        sa.Column('leads_evaluated', sa.Integer(), default=0, nullable=False),
        sa.Column('bytes_downloaded', sa.Integer(), default=0, nullable=False),
        sa.Column('tokens_used', sa.Integer(), default=0, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    # Investigation Events table
    op.create_table(
        'investigation_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('event_type', sa.String(50), index=True, nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Search Queries table
    op.create_table(
        'search_queries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('run_id', sa.String(36), nullable=True),
        sa.Column('query_text', sa.String(500), nullable=False),
        sa.Column('source_name', sa.String(50), nullable=False),
        sa.Column('depth', sa.Integer(), default=0, nullable=False),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('results_count', sa.Integer(), default=0, nullable=False),
        sa.Column('execution_duration_ms', sa.Float(), default=0.0, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Discovery Leads table
    op.create_table(
        'discovery_leads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('parent_lead_id', sa.String(36), sa.ForeignKey('discovery_leads.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lead_type', sa.String(50), nullable=False),
        sa.Column('lead_value', sa.String(500), nullable=False),
        sa.Column('depth', sa.Integer(), default=0, nullable=False),
        sa.Column('priority_score', sa.Float(), default=1.0, nullable=False),
        sa.Column('status', sa.String(50), default='queued', index=True, nullable=False),
        sa.Column('discovery_reason', sa.Text(), default='', nullable=False),
        sa.Column('similarity_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Source Documents table
    op.create_table(
        'source_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('connector_name', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), default='', nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('canonical_url', sa.Text(), index=True, nullable=False),
        sa.Column('content_hash', sa.String(64), index=True, nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('clean_text', sa.Text(), nullable=True),
        sa.Column('snippet', sa.Text(), default='', nullable=False),
        sa.Column('mime_type', sa.String(100), default='text/html', nullable=False),
        sa.Column('publication_date', sa.String(50), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('headers_json', sa.JSON(), nullable=False),
        sa.Column('is_retained', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Evidence Records table
    op.create_table(
        'evidence_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('extracted_passage', sa.Text(), nullable=False),
        sa.Column('relevance_score', sa.Float(), default=0.5, nullable=False),
        sa.Column('uncertainty_score', sa.Float(), default=0.2, nullable=False),
        sa.Column('confidence_level', sa.String(20), default='medium', nullable=False),
        sa.Column('why_included', sa.Text(), nullable=False),
        sa.Column('is_verified_source_statement', sa.Boolean(), default=True, nullable=False),
        sa.Column('contradictions_noted', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Extracted Entities table
    op.create_table(
        'extracted_entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('source_documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('entity_type', sa.String(50), index=True, nullable=False),
        sa.Column('entity_value', sa.String(500), nullable=False),
        sa.Column('normalized_value', sa.String(500), index=True, nullable=False),
        sa.Column('confidence', sa.Float(), default=0.7, nullable=False),
        sa.Column('context_snippet', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Report Exports table
    op.create_table(
        'report_exports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(36), sa.ForeignKey('investigations.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('format', sa.String(20), default='markdown', nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('summary_json', sa.JSON(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('report_exports')
    op.drop_table('extracted_entities')
    op.drop_table('evidence_records')
    op.drop_table('source_documents')
    op.drop_table('discovery_leads')
    op.drop_table('search_queries')
    op.drop_table('investigation_events')
    op.drop_table('investigation_runs')
    op.drop_table('investigations')
    op.drop_table('role_permissions')
    op.drop_table('users')
