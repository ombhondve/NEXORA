"""
Upload Security and Validation Tests.
Verifies file signature checks, magic byte verification, path traversal prevention, and size bounds.
"""

import pytest
from recursive_osint.core.exceptions import ValidationError, SecurityException
from recursive_osint.media.upload_validation import validate_file_content, sanitize_filename


def test_sanitize_filename_prevents_traversal():
    assert sanitize_filename("../../etc/shadow") == "shadow"
    assert sanitize_filename("..\\..\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("normal_file.pdf") == "normal_file.pdf"


def test_upload_accepts_valid_png_magic():
    valid_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    ext, safe_name = validate_file_content(valid_png_bytes, "evidence.png")
    assert ext == "png"
    assert safe_name.endswith(".png")


def test_upload_rejects_fake_extension_magic_mismatch():
    # File named .png but contains plain text script
    malicious_bytes = b"#!/bin/bash\necho PWNED"
    with pytest.raises(SecurityException):
        validate_file_content(malicious_bytes, "malicious.png")


def test_upload_rejects_disallowed_extension():
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    with pytest.raises(SecurityException):
        validate_file_content(exe_bytes, "payload.exe")


def test_upload_enforces_size_threshold():
    # 26 MB of data (exceeds default 25MB threshold)
    huge_bytes = b"A" * (26 * 1024 * 1024)
    with pytest.raises(ValidationError):
        validate_file_content(huge_bytes, "huge.txt")
