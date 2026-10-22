"""
Main FastAPI Application Entrypoint.
"""

import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from recursive_osint.api.errors import register_exception_handlers
from recursive_osint.api.v1.router import api_v1_router
from recursive_osint.config import settings
from recursive_osint.core.request_context import set_request_id
from recursive_osint.lifespan import lifespan

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Recursive OSINT Discovery Engine API. Autonomously discovers, searches, "
        "correlates, and synthesizes intelligence from authorized, public internet sources."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Assigns unique X-Request-ID to each incoming HTTP request for end-to-end tracing."""
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(req_id)
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


# Register Exception Handlers
register_exception_handlers(app)

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }

