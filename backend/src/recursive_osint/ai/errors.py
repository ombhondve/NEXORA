"""
Structured AI Exceptions and Error Categories for NEXORA AI Layer.
"""

from typing import Optional


class AIEngineError(Exception):
    """
    Structured exception for AI integration errors.
    Carries machine-readable category, HTTP status code, and optional retry-after metadata.
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
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or message
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
