"""
Custom application exception hierarchy.
"""

from typing import Any, Dict, Optional


class OSINTException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SecurityException(OSINTException):
    """Raised on security violation (e.g. invalid tokens, auth failures)."""
    pass


class AccessDeniedError(SecurityException):
    """Raised when an authenticated user attempts to access another user's private resource."""
    pass


class SSRFViolationError(SecurityException):
    """Raised when an outbound URL resolves to a prohibited network or private IP."""
    pass


class RateLimitExceededError(OSINTException):
    """Raised when request rate limit threshold is exceeded."""
    pass


class BudgetExhaustedError(OSINTException):
    """Raised when an investigation exceeds its allotted search/time/token budget."""
    pass


class ConnectorError(OSINTException):
    """Raised when an external source connector encounters an error."""
    pass


class EntityNotFoundError(OSINTException):
    """Raised when an entity or resource is not found."""
    pass


class ValidationError(OSINTException):
    """Raised on input or domain validation failures."""
    pass
