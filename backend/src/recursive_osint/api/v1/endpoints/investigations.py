"""
Investigation endpoints.
Full lifecycle management of recursive investigations.
"""

import asyncio
from typing import List
from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.api.dependencies import get_current_user
from recursive_osint.db.session import get_db, AsyncSessionLocal
from recursive_osint.db.models.user import User
from recursive_osint.db.repositories.evidence_repo import EvidenceRepository
from recursive_osint.schemas.investigation import (
    InvestigationCreate,
    InvestigationResponse,
    InvestigationEventResponse,
)
from recursive_osint.schemas.evidence import (
    EvidenceRecordResponse,
    SourceDocumentResponse,
    ExtractedEntityResponse,
    InvestigationReportResponse,
)
from recursive_osint.services.investigation_service import InvestigationService
from recursive_osint.services.report_service import ReportService

router = APIRouter(prefix="/investigations", tags=["Investigations"])


async def run_discovery_background(investigation_id: str, user_id: str):
    """Executes discovery loop asynchronously."""
    async with AsyncSessionLocal() as session:
        service = InvestigationService(session)
        await service.start_discovery(investigation_id, user_id)


@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    data: InvestigationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new recursive investigation."""
    service = InvestigationService(db)
    inv = await service.create_investigation(current_user.id, data)
    return InvestigationResponse.model_validate(inv)


@router.get("", response_model=List[InvestigationResponse])
async def list_investigations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists investigations belonging to the authenticated user."""
    service = InvestigationService(db)
    items = await service.list_user_investigations(current_user.id, skip=skip, limit=limit)
    return [InvestigationResponse.model_validate(i) for i in items]


@router.get("/{id}", response_model=InvestigationResponse)
async def get_investigation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves an investigation by ID."""
    service = InvestigationService(db)
    inv = await service.get_investigation(id, current_user.id)
    return InvestigationResponse.model_validate(inv)


@router.post("/{id}/start", response_model=InvestigationResponse)
async def start_investigation(
    id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Triggers recursive discovery in the background."""
    service = InvestigationService(db)
    inv = await service.get_investigation(id, current_user.id)
    inv.status = "running"
    await db.commit()
    background_tasks.add_task(run_discovery_background, id, current_user.id)
    return InvestigationResponse.model_validate(inv)


@router.post("/{id}/cancel", response_model=InvestigationResponse)
async def cancel_investigation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancels an active investigation."""
    service = InvestigationService(db)
    inv = await service.cancel_discovery(id, current_user.id)
    return InvestigationResponse.model_validate(inv)


@router.get("/{id}/events", response_model=List[InvestigationEventResponse])
async def get_investigation_events(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves chronological activity events for an investigation."""
    service = InvestigationService(db)
    events = await service.get_events(id, current_user.id)
    return [InvestigationEventResponse.model_validate(e) for e in events]


@router.get("/{id}/evidence", response_model=List[EvidenceRecordResponse])
async def get_investigation_evidence(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves correlated evidence records."""
    service = InvestigationService(db)
    await service.get_investigation(id, current_user.id)
    repo = EvidenceRepository(db)
    records = await repo.list_by_investigation(id)
    return [EvidenceRecordResponse.model_validate(r) for r in records]


@router.get("/{id}/documents", response_model=List[SourceDocumentResponse])
async def get_investigation_documents(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves discovered source documents."""
    service = InvestigationService(db)
    await service.get_investigation(id, current_user.id)
    repo = EvidenceRepository(db)
    docs = await repo.list_documents(id)
    return [SourceDocumentResponse.model_validate(d) for d in docs]


@router.get("/{id}/entities", response_model=List[ExtractedEntityResponse])
async def get_investigation_entities(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves extracted entities."""
    service = InvestigationService(db)
    await service.get_investigation(id, current_user.id)
    repo = EvidenceRepository(db)
    entities = await repo.list_entities(id)
    return [ExtractedEntityResponse.model_validate(e) for e in entities]


@router.get("/{id}/report", response_model=InvestigationReportResponse)
async def get_investigation_report(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates and returns consolidated investigation report."""
    service = InvestigationService(db)
    inv = await service.get_investigation(id, current_user.id)
    rep_service = ReportService(db)
    return await rep_service.generate_report(inv)
