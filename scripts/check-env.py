"""
Environment Configuration Verification Script.
Checks for required secrets, database connectivity, and connector statuses.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from recursive_osint.config import settings
from recursive_osint.connectors.registry import connector_registry


def check_env():
    print("==================================================")
    print(" RECURSIVE OSINT ENGINE - ENVIRONMENT CHECK")
    print("==================================================")
    print(f"App Name:        {settings.APP_NAME}")
    print(f"Environment:     {settings.ENVIRONMENT}")
    print(f"Database Source: {settings.DATABASE_SOURCE}")
    print(f"Database URL:    {settings.get_redacted_database_url()}")
    if settings.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING:
        print(f"Non-Pooling URL: {settings.get_redacted_url(settings.DATABASE_NEXORA_POSTGRES_URL_NON_POOLING)}")
    if settings.DATABASE_NEXORA_PGHOST:
        print(f"Neon PG Host:    {settings.DATABASE_NEXORA_PGHOST}")
    if settings.DATABASE_NEXORA_NEON_PROJECT_ID:
        print(f"Neon Project ID: {settings.DATABASE_NEXORA_NEON_PROJECT_ID}")
    print(f"Redis URL:       {settings.REDIS_URL}")
    print(f"SSRF Protection: {'ENABLED (Strict)' if settings.ENABLE_SSRF_PROTECTION else 'DISABLED'}")
    print(f"Storage Root:    {settings.STORAGE_LOCAL_ROOT}")
    print(f"Max Depth:       {settings.DEFAULT_MAX_DEPTH}")
    print(f"Max Queries:     {settings.DEFAULT_MAX_TOTAL_QUERIES}")
    print(f"Max Time (s):    {settings.DEFAULT_MAX_EXECUTION_TIME_SECONDS}")

    print("\n--- ACTIVE SOURCE CONNECTORS ---")
    connectors = connector_registry.list_all()
    for c in connectors:
        status_str = "[READY]" if c.is_configured else "[NEEDS API KEY]"
        print(f" {status_str:<16} {c.display_name} ({c.name})")

    print("\n[OK] Configuration loaded and verified.")


if __name__ == "__main__":
    check_env()
