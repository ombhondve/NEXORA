"""
Unit tests for Vercel / Neon database configuration, precedence, and normalization.
"""

import os
import pytest
from recursive_osint.config import (
    Settings,
    normalize_database_url,
    resolve_active_database_url,
    resolve_active_redis_url,
)


class TestDatabaseConfiguration:
    def test_database_nexora_postgres_url_precedence(self, monkeypatch):
        """Confirm DATABASE_NEXORA_POSTGRES_URL takes precedence over all other variables."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DATABASE_NEXORA_POSTGRES_URL", "postgres://user1:pass1@ep-neon-1.aws.neon.tech/neondb?sslmode=require")
        monkeypatch.setenv("DATABASE_NEXORA_DATABASE_URL", "postgres://user2:pass2@ep-neon-2.aws.neon.tech/neondb")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user3:pass3@localhost:5432/fallback")

        raw_url, source = resolve_active_database_url()
        assert source == "DATABASE_NEXORA_POSTGRES_URL"
        assert "user1:pass1" in raw_url

    def test_database_nexora_database_url_secondary_precedence(self, monkeypatch):
        """Confirm DATABASE_NEXORA_DATABASE_URL is selected if DATABASE_NEXORA_POSTGRES_URL is unset."""
        monkeypatch.delenv("DATABASE_NEXORA_POSTGRES_URL", raising=False)
        monkeypatch.setenv("DATABASE_NEXORA_DATABASE_URL", "postgres://user2:pass2@ep-neon-2.aws.neon.tech/neondb")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user3:pass3@localhost:5432/fallback")

        raw_url, source = resolve_active_database_url()
        assert source == "DATABASE_NEXORA_DATABASE_URL"
        assert "user2:pass2" in raw_url

    def test_database_url_tertiary_fallback(self, monkeypatch):
        """Confirm DATABASE_URL is selected when neither DATABASE_NEXORA_* is set."""
        monkeypatch.delenv("DATABASE_NEXORA_POSTGRES_URL", raising=False)
        monkeypatch.delenv("DATABASE_NEXORA_DATABASE_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user3:pass3@localhost:5432/fallback")

        raw_url, source = resolve_active_database_url()
        assert source == "DATABASE_URL"
        assert "user3:pass3" in raw_url

    def test_default_sqlite_in_development(self, monkeypatch):
        """Confirm non-production environments default safely to SQLite if no variables are configured."""
        monkeypatch.delenv("DATABASE_NEXORA_POSTGRES_URL", raising=False)
        monkeypatch.delenv("DATABASE_NEXORA_DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")

        raw_url, source = resolve_active_database_url()
        assert source == "default_sqlite"
        assert "sqlite+aiosqlite" in raw_url

    def test_url_normalization_postgres_to_asyncpg(self):
        """Verify postgres:// and postgresql:// are normalized to postgresql+asyncpg:// with ssl=require."""
        raw = "postgres://neondb_owner:npg_secret@ep-xyz-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
        normalized = normalize_database_url(raw, is_async=True)
        assert normalized.startswith("postgresql+asyncpg://")
        assert "ssl=require" in normalized
        assert "sslmode" not in normalized

    def test_sync_migration_url_normalization(self):
        """Verify sync migration URL normalization maps to postgresql:// without asyncpg."""
        raw = "postgresql+asyncpg://neondb_owner:secret@ep-xyz.us-east-1.aws.neon.tech/neondb"
        sync_url = normalize_database_url(raw, is_async=False)
        assert sync_url.startswith("postgresql://")
        assert "asyncpg" not in sync_url

    def test_password_redaction(self):
        """Verify credentials are never exposed in redacted URLs."""
        raw = "postgresql+asyncpg://admin_user:super_secret_pw@ep-xyz.aws.neon.tech:5432/neondb?ssl=require"
        redacted = Settings.get_redacted_url(raw)
        assert "super_secret_pw" not in redacted
        assert "admin_user:***@" in redacted
        assert "ep-xyz.aws.neon.tech:5432/neondb" in redacted

    def test_non_pooling_migration_url_preferred(self, monkeypatch):
        """Verify get_migration_url() prefers DATABASE_NEXORA_POSTGRES_URL_NON_POOLING."""
        monkeypatch.setenv("DATABASE_NEXORA_POSTGRES_URL", "postgres://user:pass@ep-pooler.neon.tech/neondb")
        monkeypatch.setenv("DATABASE_NEXORA_POSTGRES_URL_NON_POOLING", "postgres://user:pass@ep-direct.neon.tech/neondb")

        s = Settings()
        assert s.DATABASE_MIGRATION_SOURCE == "DATABASE_NEXORA_POSTGRES_URL_NON_POOLING"
        mig_url = s.get_migration_url(is_async=True)
        assert "ep-direct.neon.tech" in mig_url

    def test_production_readiness_missing_url(self, monkeypatch):
        """Verify production mode rejects missing database URL with actionable message."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a" * 64)
        monkeypatch.delenv("DATABASE_NEXORA_POSTGRES_URL", raising=False)
        monkeypatch.delenv("DATABASE_NEXORA_DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with pytest.raises(ValueError, match="FATAL \\[Production Database\\]: No production database URL provided"):
            s = Settings()
            s.validate_production_readiness()

    def test_production_readiness_sqlite_forbidden(self, monkeypatch):
        """Verify production mode strictly forbids SQLite."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "b" * 64)
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./prod.db")

        with pytest.raises(ValueError, match="FATAL \\[Production Security\\]: SQLite is strictly prohibited"):
            s = Settings()
            s.validate_production_readiness()

    def test_production_readiness_unencrypted_forbidden(self, monkeypatch):
        """Verify production mode forbids DATABASE_NEXORA_POSTGRES_URL_NO_SSL and ssl=disable."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "c" * 64)
        monkeypatch.setenv("DATABASE_NEXORA_POSTGRES_URL", "postgresql://user:pass@ep.neon.tech/db?sslmode=disable")

        with pytest.raises(ValueError, match="FATAL \\[Production Security\\]: Unencrypted database connections"):
            s = Settings()
            s.validate_production_readiness()

    def test_environment_validation_invalid_value(self, monkeypatch):
        """Verify invalid ENVIRONMENT string is rejected."""
        monkeypatch.setenv("ENVIRONMENT", "prod-testing")
        with pytest.raises(ValueError, match="FATAL \\[Config\\]: Invalid ENVIRONMENT"):
            s = Settings()
            s.validate_production_readiness()

    def test_environment_validation_url_rejected(self, monkeypatch):
        """Verify ENVIRONMENT set to a URL is rejected."""
        monkeypatch.setenv("ENVIRONMENT", "postgres://user:pass@localhost/db")
        with pytest.raises(ValueError, match="FATAL \\[Config\\]: ENVIRONMENT appears to be set to a connection URL"):
            s = Settings()
            s.validate_production_readiness()


class TestRedisConfiguration:
    def test_redis_redis_url_precedence(self, monkeypatch):
        """Confirm Redis_REDIS_URL takes precedence over REDIS_URL."""
        monkeypatch.setenv("Redis_REDIS_URL", "redis://default:token_vercel@ep-upstash-1.upstash.io:6379")
        monkeypatch.setenv("REDIS_URL", "redis://fallback_user:fallback_pass@localhost:6379/1")

        raw_url, source = resolve_active_redis_url()
        assert source == "Redis_REDIS_URL"
        assert "ep-upstash-1.upstash.io:6379" in raw_url
        assert "token_vercel" in raw_url

        s = Settings()
        assert s.REDIS_SOURCE == "Redis_REDIS_URL"
        assert s.REDIS_URL == "redis://default:token_vercel@ep-upstash-1.upstash.io:6379"

    def test_redis_url_fallback(self, monkeypatch):
        """Confirm REDIS_URL is used when Redis_REDIS_URL is absent or empty."""
        monkeypatch.delenv("Redis_REDIS_URL", raising=False)
        monkeypatch.setenv("REDIS_URL", "redis://user:pass@localhost:6379/2")

        raw_url, source = resolve_active_redis_url()
        assert source == "REDIS_URL"
        assert "user:pass@localhost:6379/2" in raw_url

        s = Settings()
        assert s.REDIS_SOURCE == "REDIS_URL"
        assert s.REDIS_URL == "redis://user:pass@localhost:6379/2"

    def test_redis_default_when_unset(self, monkeypatch):
        """Confirm default Redis URL is used when neither variable is set."""
        monkeypatch.delenv("Redis_REDIS_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)

        raw_url, source = resolve_active_redis_url()
        assert source == "default_redis"
        assert raw_url == "redis://localhost:6379/0"

        s = Settings()
        assert s.REDIS_SOURCE == "default_redis"
        assert s.REDIS_URL == "redis://localhost:6379/0"

    def test_redis_password_redaction(self, monkeypatch):
        """Confirm passwords in Redis_REDIS_URL are masked in logs and diagnostic outputs."""
        monkeypatch.setenv("Redis_REDIS_URL", "redis://default:super_secret_redis_token@ep-upstash.io:6379")

        s = Settings()
        redacted = s.get_redacted_redis_url()
        assert "super_secret_redis_token" not in redacted
        assert "default:***@ep-upstash.io:6379" in redacted

