import re
from typing import Optional

# Regex patterns matching potential API keys, secret prefixes, and credentials
_SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z\-_]{10,}", re.IGNORECASE),
    re.compile(r"gsk_[0-9A-Za-z\-_]{10,}", re.IGNORECASE),
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.]{15,}", re.IGNORECASE),
    re.compile(r"((?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?)[A-Za-z0-9\-_]{8,}(['\"]?)", re.IGNORECASE),
]


def sanitize_secret_text(text: Optional[str]) -> str:
    """
    Sanitizes string text by removing full and partial API keys, prefixes (e.g. AIza..., gsk_...),
    and secret tokens to prevent accidental leakage in errors, frontend responses, or logs.
    """
    if not text:
        return ""
    sanitized = str(text)
    sanitized = re.sub(r"AIza[0-9A-Za-z\-_]{5,}", "[REDACTED_GEMINI_KEY]", sanitized)
    sanitized = re.sub(r"gsk_[0-9A-Za-z\-_]{5,}", "[REDACTED_GROQ_KEY]", sanitized)
    sanitized = re.sub(r"(Bearer\s+)[A-Za-z0-9\-_\.]{10,}", r"\1[REDACTED_TOKEN]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(
        r"((?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?)[A-Za-z0-9\-_]{6,}(['\"]?)",
        r"\1[REDACTED]\2",
        sanitized,
        flags=re.IGNORECASE,
    )
    return sanitized


class AIEngineError(Exception):
    """
    Structured exception for AI integration errors.
    Carries machine-readable category, HTTP status code, and optional retry-after metadata.
    Automatically redacts secret credentials and keys from message and details.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 503,
        details: Optional[str] = None,
        category: str = "ai_error",
        provider: Optional[str] = None,
        retry_after: Optional[float] = None,
    ):
        clean_msg = sanitize_secret_text(message)
        clean_details = sanitize_secret_text(details or message)
        super().__init__(clean_msg)
        self.message = clean_msg
        self.status_code = status_code
        self.details = clean_details
        self.category = category
        self.provider = provider
        self.retry_after = retry_after

    def to_dict(self):
        return {
            "error": self.category.upper(),
            "message": self.message,
            "category": self.category,
            "provider": self.provider,
            "retry_after": self.retry_after,
        }

