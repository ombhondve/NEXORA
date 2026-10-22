"""
Configuration module using Pydantic Settings with robust production validation.
Validates environment variables at application startup and synchronizes with
Vercel / Neon PostgreSQL environment variable conventions.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Set
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Deterministic dotenv loading for backend local development:
# Locates backend/.env relative to this config file:
# backend/src/recursive_osint/config.py -> parent(recursive_osint) -> parent(src) -> parent(backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_ENV_PATH = BACKEND_DIR / ".env"
ROOT_ENV_PATH = BACKEND_DIR.parent / ".env"

if BACKEND_ENV_PATH.is_file():
    # Load backend/.env without overriding existing environment variables
    # (so Vercel/system/Docker/test env vars take precedence)
    load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
elif ROOT_ENV_PATH.is_file():
    # Backward compatibility fallback during migration
    load_dotenv(dotenv_path=ROOT_ENV_PATH, override=False)

VALID_ENVIRONMENTS: Set[str] = {"development", "test", "staging", "production"}


def normalize_database_url(url: str, is_async: bool = True) -> str:
    """
    Normalizes a database URL for SQLAlchemy compatibility:
    - Automatically maps postgres:// and postgresql:// to postgresql+asyncpg:// (for async runtime)
    - Maps to postgresql:// for synchronous drivers (e.g. offline Alembic migrations)
    - Maps sslmode=require / verify-ca / verify-full to ssl=require for asyncpg
    - Leaves SQLite URLs untouched
    """
    if not url:
        return ""
    cleaned = url.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    if "sqlite" in cleaned:
        return cleaned

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://"):]

    try:
        from sqlalchemy.engine.url import make_url

        parsed = make_url(cleaned)
        if is_async:
            if parsed.drivername in ("postgres", "postgresql", "postgresql+psycopg2"):
                parsed = parsed.set(drivername="postgresql+asyncpg")
        else:
            if parsed.drivername in ("postgresql+asyncpg", "postgres"):
                parsed = parsed.set(drivername="postgresql")

        if "asyncpg" in parsed.drivername:
            query = dict(parsed.query)
            sslmode = query.pop("sslmode", None)
            if sslmode and "ssl" not in query:
                if sslmode in ("require", "prefer", "verify-ca", "verify-full"):
                    query["ssl"] = "require"
                elif sslmode == "disable":
                    query["ssl"] = "disable"
            parsed = parsed._replace(query=query)

        return parsed.render_as_string(hide_password=False)
    except Exception:
        if is_async and cleaned.startswith("postgresql://") and "+asyncpg" not in cleaned:
            cleaned = "postgresql+asyncpg://" + cleaned[len("postgresql://"):]
        return cleaned


def resolve_active_database_url() -> tuple[str, str]:
    """
    Resolves the active database connection string based on strict precedence:
    1. DATABASE_NEXORA_POSTGRES_URL (Preferred Neon connection URL configured in Vercel)
    2. DATABASE_NEXORA_DATABASE_URL (Secondary Vercel integration alias)
    3. DATABASE_URL (Standard local dev / docker / fallback)
    Returns: (raw_url, source_variable_name)
    """
    env_name = os.getenv("ENVIRONMENT", "development").strip().lower()

    # 1. Preferred Neon PostgreSQL connection URL
    val = os.getenv("DATABASE_NEXORA_POSTGRES_URL")
    if val and val.strip():
        return val.strip(), "DATABASE_NEXORA_POSTGRES_URL"

    # 2. Secondary Vercel alias
    val = os.getenv("DATABASE_NEXORA_DATABASE_URL")
    if val and val.strip():
        return val.strip(), "DATABASE_NEXORA_DATABASE_URL"

    # 3. Standard fallback
    val = os.getenv("DATABASE_URL")
    if val and val.strip():
        return val.strip(), "DATABASE_URL"

    # 4. Default SQLite for non-production environments only
    if env_name != "production":
        return "sqlite+aiosqlite:///./osint_dev.db", "default_sqlite"

    return "", "none"


def resolve_active_redis_url() -> tuple[str, str]:
    """
    Resolves the active Redis connection string based on strict precedence:
    1. Redis_REDIS_URL (Preferred Vercel integration variable name)
    2. REDIS_URL (Standard fallback / local development)
    Returns: (raw_url, source_variable_name)
    """
    val = os.getenv("Redis_REDIS_URL")
    if val and val.strip():
        return val.strip(), "Redis_REDIS_URL"

    val = os.getenv("REDIS_URL")
    if val and val.strip():
        return val.strip(), "REDIS_URL"

    return "redis://localhost:6379/0", "default_redis"


class Settings(BaseModel):
    # General App Config
    APP_NAME: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Recursive OSINT Discovery Engine"))
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development").strip().lower())
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    API_V1_PREFIX: str = Field(default_factory=lambda: os.getenv("API_V1_PREFIX", "/api/v1"))
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # Security & JWT Auth
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        )
    )
    ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")))
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))
    ALLOW_ANONYMOUS_DEV_AUTH: bool = Field(default_factory=lambda: os.getenv("ALLOW_ANONYMOUS_DEV_AUTH", "false").lower() in ("true", "1"))
    ENABLE_DEV_SEEDS: bool = Field(default_factory=lambda: os.getenv("ENABLE_DEV_SEEDS", "false").lower() in ("true", "1"))

    # CORS
    CORS_ORIGINS: str = Field(default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"))

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Database Source Tracking & Resolved URLs
    DATABASE_SOURCE: str = Field(default_factory=lambda: resolve_active_database_url()[1])
    RAW_DATABASE_URL: str = Field(default_factory=lambda: resolve_active_database_url()[0])

    @property
    def DATABASE_URL(self) -> str:
        """Returns the normalized async database URL (postgresql+asyncpg:// or sqlite+aiosqlite:///)."""
        return normalize_database_url(self.RAW_DATABASE_URL, is_async=True)

    # Optional Vercel / Neon Environment Variables
    DATABASE_NEXORA_POSTGRES_URL_NON_POOLING: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_NEXORA_POSTGRES_URL_NON_POOLING", None)
    )
    DATABASE_NEXORA_POSTGRES_USER: Optional[str] = Field(default_factory=lambda: os.getenv("DATABASE_NEXORA_POSTGRES_USER", None))
    DATABASE_NEXORA_PGHOST: Optional[str] = Field(default_factory=lambda: os.getenv("DATABASE_NEXORA_PGHOST", None))
    DATABASE_NEXORA_POSTGRES_PRISMA_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_NEXORA_POSTGRES_PRISMA_URL", None)
    )
    DATABASE_NEXORA_POSTGRES_URL_NO_SSL: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_NEXORA_POSTGRES_URL_NO_SSL", None)
    )
    DATABASE_NEXORA_NEON_AUTH_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_NEXORA_NEON_AUTH_BASE_URL", None)
    )
    DATABASE_NEXORA_VITE_NEON_AUTH_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_NEXORA_VITE_NEON_AUTH_URL", None)
    )
    DATABASE_NEXORA_NEON_PROJECT_ID: Optional[str] = Field(default_factory=lambda: os.getenv("DATABASE_NEXORA_NEON_PROJECT_ID", None))

    # Connection Pool Settings
    DATABASE_POOL_SIZE: int = Field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "5")))
    DATABASE_MAX_OVERFLOW: int = Field(default_factory=lambda: int(os.getenv("DATABASE_MAX_OVERFLOW", "10")))
    DATABASE_POOL_TIMEOUT: int = Field(default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30")))
    DATABASE_USE_NULLPOOL: bool = Field(default_factory=lambda: os.getenv("DATABASE_USE_NULLPOOL", "false").lower() in ("true", "1"))

    @property
    def DATABASE_MIGRATION_SOURCE(self) -> str:
        """Identifies which variable is supplying the migration connection."""
        if self.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING and self.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING.strip():
            return "DATABASE_NEXORA_POSTGRES_URL_NON_POOLING"
        return self.DATABASE_SOURCE

    def get_migration_url(self, is_async: bool = False) -> str:
        """
        Returns the database URL for migrations.
        Prefers DATABASE_NEXORA_POSTGRES_URL_NON_POOLING (direct connection)
        to prevent PgBouncer transaction-mode connection pooler issues during DDL operations.
        """
        raw = (
            self.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING.strip()
            if self.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING and self.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING.strip()
            else self.RAW_DATABASE_URL
        )
        return normalize_database_url(raw, is_async=is_async)

    def get_redacted_database_url(self) -> str:
        """Returns the active database URL with password redacted for safe logging."""
        return self.get_redacted_url(self.DATABASE_URL)

    @staticmethod
    def get_redacted_url(url: str) -> str:
        """Helper to redact passwords from any connection string."""
        if not url:
            return "none"
        try:
            from sqlalchemy.engine.url import make_url

            parsed = make_url(url)
            return parsed.render_as_string(hide_password=True)
        except Exception:
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)

    # Redis (Task Queue & Cache)
    REDIS_SOURCE: str = Field(default_factory=lambda: resolve_active_redis_url()[1])
    REDIS_URL: str = Field(default_factory=lambda: resolve_active_redis_url()[0])
    REDIS_CACHE_TTL_SECONDS: int = Field(default_factory=lambda: int(os.getenv("REDIS_CACHE_TTL_SECONDS", "3600")))

    def get_redacted_redis_url(self) -> str:
        """Returns the Redis URL with password redacted for safe logging."""
        return self.get_redacted_url(self.REDIS_URL)

    # OpenSearch
    OPENSEARCH_URL: str = Field(default_factory=lambda: os.getenv("OPENSEARCH_URL", "http://localhost:9200"))
    OPENSEARCH_USER: Optional[str] = Field(default_factory=lambda: os.getenv("OPENSEARCH_USER", None))
    OPENSEARCH_PASSWORD: Optional[str] = Field(default_factory=lambda: os.getenv("OPENSEARCH_PASSWORD", None))
    OPENSEARCH_VERIFY_CERTS: bool = Field(default_factory=lambda: os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() in ("true", "1"))
    OPENSEARCH_INDEX_PREFIX: str = Field(default_factory=lambda: os.getenv("OPENSEARCH_INDEX_PREFIX", "osint"))

    # Storage (Private uploads)
    STORAGE_BACKEND: str = Field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))
    STORAGE_LOCAL_ROOT: str = Field(default_factory=lambda: os.getenv("STORAGE_LOCAL_ROOT", "./storage/uploads"))
    STORAGE_MAX_FILE_SIZE_MB: int = Field(default_factory=lambda: int(os.getenv("STORAGE_MAX_FILE_SIZE_MB", "25")))
    ALLOWED_UPLOAD_EXTENSIONS: str = Field(default_factory=lambda: os.getenv("ALLOWED_UPLOAD_EXTENSIONS", "pdf,txt,png,jpg,jpeg,webp"))

    @property
    def allowed_extensions_set(self) -> Set[str]:
        return {ext.strip().lower().lstrip(".") for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")}

    # Default Investigation Budget Limits
    DEFAULT_MAX_DEPTH: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_DEPTH", "3")))
    DEFAULT_MAX_TOTAL_QUERIES: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_TOTAL_QUERIES", "25")))
    DEFAULT_MAX_REQUESTS_PER_CONNECTOR: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_REQUESTS_PER_CONNECTOR", "10")))
    DEFAULT_MAX_EXECUTION_TIME_SECONDS: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_EXECUTION_TIME_SECONDS", "600")))
    DEFAULT_MAX_DOWNLOAD_BYTES: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_DOWNLOAD_BYTES", "52428800")))
    DEFAULT_MAX_AI_TOKENS: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_AI_TOKENS", "25000")))
    DIMINISHING_RETURNS_SIMILARITY_THRESHOLD: float = Field(default_factory=lambda: float(
        os.getenv("DIMINISHING_RETURNS_SIMILARITY_THRESHOLD", "0.88")
    ))

    # SSRF & Crawler Protection
    ENABLE_SSRF_PROTECTION: bool = Field(default_factory=lambda: os.getenv("ENABLE_SSRF_PROTECTION", "true").lower() in ("true", "1"))
    CRAWLER_USER_AGENT: str = Field(default_factory=lambda: os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (compatible; RecursiveOSINTBot/1.0; +https://example.org/bot)",
    ))
    CRAWLER_TIMEOUT_SECONDS: int = Field(default_factory=lambda: int(os.getenv("CRAWLER_TIMEOUT_SECONDS", "15")))
    CRAWLER_MAX_REDIRECTS: int = Field(default_factory=lambda: int(os.getenv("CRAWLER_MAX_REDIRECTS", "3")))
    CRAWLER_MAX_CONTENT_LENGTH: int = Field(default_factory=lambda: int(os.getenv("CRAWLER_MAX_CONTENT_LENGTH", "5242880")))
    RESPECT_ROBOTS_TXT: bool = Field(default_factory=lambda: os.getenv("RESPECT_ROBOTS_TXT", "true").lower() in ("true", "1"))

    # Connectors toggles
    ENABLE_WIKIPEDIA_CONNECTOR: bool = Field(default_factory=lambda: os.getenv("ENABLE_WIKIPEDIA_CONNECTOR", "true").lower() in ("true", "1"))
    ENABLE_INTERNET_ARCHIVE_CONNECTOR: bool = Field(default_factory=lambda: os.getenv("ENABLE_INTERNET_ARCHIVE_CONNECTOR", "true").lower() in ("true", "1"))
    ENABLE_CROSSREF_CONNECTOR: bool = Field(default_factory=lambda: os.getenv("ENABLE_CROSSREF_CONNECTOR", "true").lower() in ("true", "1"))
    ENABLE_MOCK_DEMO_CONNECTOR: bool = Field(default_factory=lambda: os.getenv("ENABLE_MOCK_DEMO_CONNECTOR", "true").lower() in ("true", "1"))

    # Optional Commercial Keys
    TAVILY_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY", None))
    SERPER_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("SERPER_API_KEY", None))
    BRAVE_SEARCH_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("BRAVE_SEARCH_API_KEY", None))

    def validate_production_readiness(self) -> None:
        """
        Enforces strict production safety assertions:
        - Validates ENVIRONMENT name against allowed set.
        - Ensures ENVIRONMENT is not accidentally set to a URL.
        - Rejects default or weak SECRET_KEY in production.
        - Ensures a valid PostgreSQL database URL is configured (preferring DATABASE_NEXORA_POSTGRES_URL).
        - Forbids silent fallback to SQLite in production.
        - Forbids unencrypted database connections (DATABASE_NEXORA_POSTGRES_URL_NO_SSL / ssl=disable).
        - Forbids anonymous dev authentication bypass.
        - Forbids DEBUG mode in production.
        """
        if "://" in self.ENVIRONMENT or "postgres" in self.ENVIRONMENT:
            raise ValueError(
                "FATAL [Config]: ENVIRONMENT appears to be set to a connection URL or invalid string. "
                "Set ENVIRONMENT to 'production', 'staging', or 'development'."
            )

        if self.ENVIRONMENT not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"FATAL [Config]: Invalid ENVIRONMENT '{self.ENVIRONMENT}'. "
                f"Supported values are: {', '.join(sorted(VALID_ENVIRONMENTS))}."
            )

        if self.ENVIRONMENT == "production":
            DEFAULT_INSECURE_SECRET = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
            if not self.SECRET_KEY or self.SECRET_KEY == DEFAULT_INSECURE_SECRET or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "FATAL [Production Security]: SECRET_KEY must be a cryptographically secure random string "
                    "(minimum 32 characters) and cannot use development default."
                )

            # Ensure valid PostgreSQL URL
            if not self.RAW_DATABASE_URL or self.DATABASE_SOURCE in ("none", "default_sqlite"):
                raise ValueError(
                    "FATAL [Production Database]: No production database URL provided. "
                    "Configure DATABASE_NEXORA_POSTGRES_URL (preferred Neon connection string) "
                    "in your Vercel project environment variables."
                )

            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError(
                    "FATAL [Production Security]: SQLite is strictly prohibited in production. "
                    "Configure a production PostgreSQL connection string using DATABASE_NEXORA_POSTGRES_URL."
                )

            if not ("postgres" in self.DATABASE_URL.lower()):
                raise ValueError(
                    f"FATAL [Production Database]: Unsupported database scheme in '{self.DATABASE_SOURCE}'. "
                    "A valid PostgreSQL / Neon connection URL is required."
                )

            # SSL validation
            if (
                self.DATABASE_SOURCE == "DATABASE_NEXORA_POSTGRES_URL_NO_SSL"
                or "ssl=disable" in self.DATABASE_URL
                or "sslmode=disable" in self.RAW_DATABASE_URL
            ):
                raise ValueError(
                    "FATAL [Production Security]: Unencrypted database connections "
                    "(DATABASE_NEXORA_POSTGRES_URL_NO_SSL / ssl=disable) are strictly prohibited in production. "
                    "Neon requires SSL encryption (sslmode=require)."
                )

            if self.ALLOW_ANONYMOUS_DEV_AUTH:
                raise ValueError("FATAL [Production Security]: ALLOW_ANONYMOUS_DEV_AUTH must be disabled in production.")

            if self.DEBUG:
                raise ValueError("FATAL [Production Security]: DEBUG mode must be False in production.")


settings = Settings()
# Execute check on startup
settings.validate_production_readiness()
