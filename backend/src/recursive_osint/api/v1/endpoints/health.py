"""
Health check endpoints for liveness and readiness probes.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from recursive_osint.db.session import engine

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness():
    """Liveness probe indicating the API process is alive."""
    return {"status": "ok", "service": "osint-api"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness():
    """Readiness probe checking database and core service connectivity."""
    db_ok = True
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    if db_ok:
        return {"status": "ready", "database": "connected"}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unhealthy", "database": "disconnected"},
    )
