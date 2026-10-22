"""
AI Intelligence Layer API Endpoints.
Provides health monitoring, evidence summarization & analysis,
grounded natural language Q&A, and AI report generation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.ai.analysis_service import AIAnalysisService
from recursive_osint.ai.ollama_client import OllamaClient, AIEngineError
from recursive_osint.api.dependencies import get_optional_user
from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger
from recursive_osint.db.models.user import User
from recursive_osint.db.session import get_db
from recursive_osint.schemas.ai import (
    AIHealthResponse,
    AIInvestigationAnalysis,
    AIQuestionRequest,
    AIQuestionResponse,
    AIReportRequest,
)
from recursive_osint.schemas.evidence import InvestigationReportResponse

logger = get_logger("api.ai")
router = APIRouter(tags=["AI Intelligence"])


@router.get("/ai/health", response_model=AIHealthResponse)
async def check_ai_health():
    """
    Checks the status and availability of the local Ollama LLM provider and target model.
    Does not crash if Ollama is unreachable.
    """
    client = OllamaClient()
    status_code, details = await client.check_health()
    return AIHealthResponse(
        status=status_code,
        provider="ollama",
        model=settings.OLLAMA_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        details=details,
    )


@router.post(
    "/investigations/{id}/ai/analyze",
    response_model=AIInvestigationAnalysis,
    status_code=status.HTTP_200_OK,
)
async def run_investigation_ai_analysis(
    id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers structured AI evidence analysis for an existing investigation.
    Extracts executive findings, contextual entities, relationship candidates, and citations.
    """
    service = AIAnalysisService(db)
    try:
        return await service.analyze_investigation(id)
    except AIEngineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        logger.error("Error executing AI analysis for investigation %s: %s", id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/investigations/{id}/ai/analysis",
    response_model=Optional[AIInvestigationAnalysis],
    status_code=status.HTTP_200_OK,
)
async def get_investigation_ai_analysis(
    id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the most recent saved AI analysis for the specified investigation.
    """
    service = AIAnalysisService(db)
    analysis = await service.get_latest_analysis(id)
    return analysis


@router.post(
    "/investigations/{id}/ai/ask",
    response_model=AIQuestionResponse,
    status_code=status.HTTP_200_OK,
)
async def ask_investigation_question(
    id: str,
    payload: AIQuestionRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Performs evidence-grounded natural language Q&A strictly against the investigation's evidence.
    Verifies citations and discloses when evidence is insufficient.
    """
    service = AIAnalysisService(db)
    try:
        return await service.answer_question(id, payload.question)
    except AIEngineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        logger.error("Error answering AI question for investigation %s: %s", id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post(
    "/investigations/{id}/ai/report",
    response_model=InvestigationReportResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_ai_report_endpoint(
    id: str,
    payload: Optional[AIReportRequest] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates an extended AI intelligence report synthesizing findings and evidence limitations.
    Falls back gracefully to deterministic report generation if AI is offline.
    """
    service = AIAnalysisService(db)
    try:
        res = await service.generate_ai_report(id)
        return InvestigationReportResponse(**res)
    except AIEngineError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        logger.error("Error generating AI report for investigation %s: %s", id, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
