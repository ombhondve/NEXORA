"""
Global exception handlers for FastAPI.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from recursive_osint.core.exceptions import (
    OSINTException,
    SecurityException,
    AccessDeniedError,
    SSRFViolationError,
    RateLimitExceededError,
    BudgetExhaustedError,
    EntityNotFoundError,
    ValidationError,
)
from recursive_osint.core.logging import get_logger

logger = get_logger("api.errors")


def register_exception_handlers(app):
    @app.exception_handler(SSRFViolationError)
    async def ssrf_exception_handler(request: Request, exc: SSRFViolationError):
        logger.warning("SSRF Violation blocked on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "SSRF_VIOLATION", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "RATE_LIMIT_EXCEEDED", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(EntityNotFoundError)
    async def not_found_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "NOT_FOUND", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "VALIDATION_ERROR", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(AccessDeniedError)
    async def access_denied_handler(request: Request, exc: AccessDeniedError):
        logger.warning("Access Denied on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "ACCESS_DENIED", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(SecurityException)
    async def security_handler(request: Request, exc: SecurityException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "SECURITY_ERROR", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(OSINTException)
    async def general_osint_handler(request: Request, exc: OSINTException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "APPLICATION_ERROR", "message": exc.message, "details": exc.details},
        )
