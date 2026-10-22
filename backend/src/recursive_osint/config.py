"""
Configuration module using Pydantic Settings with robust fallback.
Validates environment variables at application startup.
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic import Field, field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _BaseConfig = BaseSettings
except ImportError:
    from pydantic import BaseModel
    _BaseConfig = BaseModel


class Settings(_BaseConfig):
    # General App Config
    APP_NAME: str = os.getenv("APP_NAME", "Recursive OSINT Discovery Engine")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    # Security & JWT Auth
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./osint_dev.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL_SECONDS: int = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "3600"))

    # OpenSearch
    OPENSEARCH_URL: str = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    OPENSEARCH_USER: Optional[str] = os.getenv("OPENSEARCH_USER", None)
    OPENSEARCH_PASSWORD: Optional[str] = os.getenv("OPENSEARCH_PASSWORD", None)
    OPENSEARCH_VERIFY_CERTS: bool = os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() in ("true", "1")
    OPENSEARCH_INDEX_PREFIX: str = os.getenv("OPENSEARCH_INDEX_PREFIX", "osint")

    # Storage
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_LOCAL_ROOT: str = os.getenv("STORAGE_LOCAL_ROOT", "./storage/uploads")
    STORAGE_MAX_FILE_SIZE_MB: int = int(os.getenv("STORAGE_MAX_FILE_SIZE_MB", "25"))
    ALLOWED_UPLOAD_EXTENSIONS: str = os.getenv("ALLOWED_UPLOAD_EXTENSIONS", "pdf,txt,png,jpg,jpeg,webp")

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.strip().lower().lstrip(".") for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")}

    # Default Investigation Budget Limits
    DEFAULT_MAX_DEPTH: int = int(os.getenv("DEFAULT_MAX_DEPTH", "3"))
    DEFAULT_MAX_TOTAL_QUERIES: int = int(os.getenv("DEFAULT_MAX_TOTAL_QUERIES", "25"))
    DEFAULT_MAX_REQUESTS_PER_CONNECTOR: int = int(os.getenv("DEFAULT_MAX_REQUESTS_PER_CONNECTOR", "10"))
    DEFAULT_MAX_EXECUTION_TIME_SECONDS: int = int(os.getenv("DEFAULT_MAX_EXECUTION_TIME_SECONDS", "600"))
    DEFAULT_MAX_DOWNLOAD_BYTES: int = int(os.getenv("DEFAULT_MAX_DOWNLOAD_BYTES", "52428800"))
    DEFAULT_MAX_AI_TOKENS: int = int(os.getenv("DEFAULT_MAX_AI_TOKENS", "25000"))
    DIMINISHING_RETURNS_SIMILARITY_THRESHOLD: float = float(
        os.getenv("DIMINISHING_RETURNS_SIMILARITY_THRESHOLD", "0.88")
    )

    # SSRF & Crawler Protection
    ENABLE_SSRF_PROTECTION: bool = os.getenv("ENABLE_SSRF_PROTECTION", "true").lower() in ("true", "1")
    CRAWLER_USER_AGENT: str = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (compatible; RecursiveOSINTBot/1.0; +https://example.org/bot)",
    )
    CRAWLER_TIMEOUT_SECONDS: int = int(os.getenv("CRAWLER_TIMEOUT_SECONDS", "15"))
    CRAWLER_MAX_REDIRECTS: int = int(os.getenv("CRAWLER_MAX_REDIRECTS", "3"))
    CRAWLER_MAX_CONTENT_LENGTH: int = int(os.getenv("CRAWLER_MAX_CONTENT_LENGTH", "5242880"))
    RESPECT_ROBOTS_TXT: bool = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() in ("true", "1")

    # Connectors toggles
    ENABLE_WIKIPEDIA_CONNECTOR: bool = os.getenv("ENABLE_WIKIPEDIA_CONNECTOR", "true").lower() in ("true", "1")
    ENABLE_INTERNET_ARCHIVE_CONNECTOR: bool = os.getenv("ENABLE_INTERNET_ARCHIVE_CONNECTOR", "true").lower() in ("true", "1")
    ENABLE_CROSSREF_CONNECTOR: bool = os.getenv("ENABLE_CROSSREF_CONNECTOR", "true").lower() in ("true", "1")
    ENABLE_MOCK_DEMO_CONNECTOR: bool = os.getenv("ENABLE_MOCK_DEMO_CONNECTOR", "true").lower() in ("true", "1")


settings = Settings()
