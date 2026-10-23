"""
Base AI Provider Interface for NEXORA.
Defines the standard contract that Google Gemini and Groq providers implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseAIProvider(ABC):
    """Abstract base class for all AI model providers."""

    def __init__(self, name: str, model: str, timeout_seconds: float = 60.0):
        self.name = name
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has necessary credentials and configuration."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes a completion/chat request against the model.
        Returns:
            Dict containing:
                content: str
                prompt_tokens: int
                completion_tokens: int
                provider: str
                model: str
                latency_ms: float
        """
        pass

    @abstractmethod
    async def check_health(self) -> Tuple[str, str]:
        """
        Verifies connectivity and model availability without running a full/expensive prompt.
        Returns:
            Tuple of (status, details)
            Status: 'ready', 'auth_error', 'quota_exhausted', 'rate_limited', 'unavailable', 'disabled'
        """
        pass
