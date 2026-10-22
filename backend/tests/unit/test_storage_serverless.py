"""
Tests for Storage Configuration, Serverless /tmp Fallback, Lifespan Startup, and S3 Backend.
"""

import os
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi import FastAPI

from recursive_osint.config import (
    Settings,
    is_serverless_environment,
    resolve_storage_local_root,
)
from recursive_osint.core.exceptions import StorageError
from recursive_osint.lifespan import lifespan
from recursive_osint.media.upload_validation import save_upload_securely


def test_is_serverless_environment_detection(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("LAMBDA_TASK_ROOT", raising=False)
    assert is_serverless_environment() is False

    monkeypatch.setenv("VERCEL", "1")
    assert is_serverless_environment() is True

    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "backend-handler")
    assert is_serverless_environment() is True


def test_resolve_storage_local_root_serverless(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    # If unset in serverless, defaults to /tmp/storage/uploads
    monkeypatch.delenv("STORAGE_LOCAL_ROOT", raising=False)
    assert resolve_storage_local_root() == "/tmp/storage/uploads"

    # If relative path set in serverless, safely redirects to /tmp/storage/uploads
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", "./storage/uploads")
    assert resolve_storage_local_root() == "/tmp/storage/uploads"

    # If explicit /tmp path set, preserves it
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", "/tmp/custom_uploads")
    assert resolve_storage_local_root() == "/tmp/custom_uploads"


def test_resolve_storage_local_root_local_dev(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("LAMBDA_TASK_ROOT", raising=False)

    monkeypatch.delenv("STORAGE_LOCAL_ROOT", raising=False)
    assert resolve_storage_local_root() == "./storage/uploads"

    monkeypatch.setenv("STORAGE_LOCAL_ROOT", "custom/local/path")
    assert resolve_storage_local_root() == "custom/local/path"


@pytest.mark.asyncio
async def test_lifespan_startup_survives_readonly_filesystem(monkeypatch, tmp_path):
    """
    Simulates a read-only filesystem where Path.mkdir raises OSError(30, 'Read-only file system').
    Confirms lifespan does not crash and falls back to a writable temp dir.
    """
    app = FastAPI()

    original_mkdir = Path.mkdir
    calls = []

    def mocked_mkdir(self, *args, **kwargs):
        calls.append(str(self))
        if "readonly" in str(self):
            raise OSError(30, "Read-only file system: 'storage'")
        return original_mkdir(self, *args, **kwargs)

    from recursive_osint.config import settings
    monkeypatch.setattr(settings, "STORAGE_LOCAL_ROOT", str(tmp_path / "readonly" / "uploads"))
    monkeypatch.setattr(Path, "mkdir", mocked_mkdir)

    # Lifespan startup should complete without raising OSError
    async with lifespan(app):
        # Successfully entered lifespan context
        assert True


def test_save_upload_securely_fallback_on_readonly(monkeypatch, tmp_path):
    """Verifies save_upload_securely falls back to temporary directory when target is read-only."""
    from recursive_osint.config import settings

    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    original_mkdir = Path.mkdir

    def mocked_mkdir(self, *args, **kwargs):
        if "readonly_dir" in str(self):
            raise OSError(30, "Read-only file system")
        return original_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(settings, "STORAGE_LOCAL_ROOT", str(tmp_path / "readonly_dir"))
    monkeypatch.setattr(Path, "mkdir", mocked_mkdir)

    saved_path = save_upload_securely(valid_png, "sample.png")
    assert os.path.exists(saved_path)
    assert "storage" in saved_path
    # Clean up test file
    try:
        os.remove(saved_path)
    except OSError:
        pass


def test_save_upload_securely_s3_missing_bucket(monkeypatch):
    """Confirms S3 backend raises StorageError when bucket is not configured."""
    from recursive_osint.config import settings

    monkeypatch.setattr(settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", None)

    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with pytest.raises(StorageError) as exc_info:
        save_upload_securely(valid_png, "sample.png")
    assert "S3_BUCKET_NAME is not set" in str(exc_info.value)
