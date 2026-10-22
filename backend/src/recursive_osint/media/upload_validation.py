"""
Secure File Upload & Media Validation Service.
Enforces magic-byte signature verification, size limits, randomized storage IDs,
and path-traversal prevention.
"""

import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from recursive_osint.config import settings
from recursive_osint.core.exceptions import ValidationError, SecurityException

# Known magic signatures for permitted file formats
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "webp": [b"RIFF"],  # WebP begins with RIFF header
}


def sanitize_filename(filename: str) -> str:
    """Strips directory traversal sequences and unsafe characters."""
    clean = os.path.basename(filename.strip().replace("\\", "/"))
    # Disallow empty or hidden files
    if not clean or clean.startswith("."):
        return "upload.dat"
    return clean


def validate_file_content(content: bytes, filename: str) -> Tuple[str, str]:
    """
    Validates file content by verifying magic bytes and size constraints.
    Returns: (detected_extension, randomized_storage_filename)
    """
    max_bytes = settings.STORAGE_MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise ValidationError(
            f"File size exceeds maximum permitted threshold of {settings.STORAGE_MAX_FILE_SIZE_MB} MB."
        )

    clean_name = sanitize_filename(filename)
    parts = clean_name.rsplit(".", 1)
    declared_ext = parts[1].lower() if len(parts) > 1 else ""

    if declared_ext not in settings.allowed_extensions_set:
        raise SecurityException(
            f"Prohibited file extension '{declared_ext}'. Permitted extensions: {settings.ALLOWED_UPLOAD_EXTENSIONS}"
        )

    # Magic byte verification
    matched_ext: Optional[str] = None
    if declared_ext in MAGIC_SIGNATURES:
        for magic in MAGIC_SIGNATURES[declared_ext]:
            if content.startswith(magic):
                matched_ext = declared_ext
                break
        if not matched_ext:
            raise SecurityException(
                f"File content does not match declared file signature for type '{declared_ext}'."
            )
    elif declared_ext == "txt":
        # Text file validation: ensure content decodes as UTF-8 without control characters
        try:
            content.decode("utf-8")
            matched_ext = "txt"
        except UnicodeDecodeError:
            raise SecurityException("Text document contains invalid non-UTF-8 binary sequences.")

    random_id = str(uuid.uuid4())
    safe_storage_name = f"{random_id}.{declared_ext}"
    return declared_ext, safe_storage_name


def save_upload_securely(content: bytes, filename: str) -> str:
    """Validates and persists file into the private storage directory."""
    ext, safe_name = validate_file_content(content, filename)
    target_dir = Path(settings.STORAGE_LOCAL_ROOT)
    target_dir.mkdir(parents=True, exist_ok=True)

    dest_path = target_dir / safe_name
    with open(dest_path, "wb") as f:
        f.write(content)

    return str(dest_path.resolve())
