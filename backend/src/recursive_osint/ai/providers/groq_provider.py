"""
Groq AI Provider for NEXORA.
Implements secondary / fallback AI model generation using the official groq SDK.
Supports structured JSON output, timeout handling, error mapping, and credential security.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from groq import AsyncGroq, RateLimitError, AuthenticationError, APITimeoutError, APIConnectionError, APIStatusError

from recursive_osint.ai.errors import AIEngineError
from recursive_osint.ai.providers.base import BaseAIProvider
from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger

logger = get_logger("ai.provider.groq")


class GroqProvider(BaseAIProvider):
    """Secondary / Fallback AI provider leveraging Groq LPU inference."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        name = "groq"
        active_model = model or settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        active_timeout = timeout_seconds or settings.GROQ_TIMEOUT_SECONDS or 60.0
        super().__init__(name=name, model=active_model, timeout_seconds=active_timeout)

        self.api_key = (api_key or settings.GROQ_API_KEY or "").strip()
        self._client: Optional[AsyncGroq] = None
        if self.api_key:
            self._client = AsyncGroq(api_key=self.api_key, timeout=self.timeout_seconds)

    @property
    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is configured."""
        return bool(self.api_key and len(self.api_key) > 5)

    def _get_client(self) -> AsyncGroq:
        if not self._client:
            if not self.is_configured:
                raise AIEngineError(
                    "Groq API key is missing. Set GROQ_API_KEY in your environment.",
                    status_code=503,
                    category="configuration_error",
                    provider=self.name,
                )
            self._client = AsyncGroq(api_key=self.api_key, timeout=self.timeout_seconds)
        return self._client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes an asynchronous chat completion request against Groq.
        """
        client = self._get_client()

        payload_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload_kwargs["response_format"] = {"type": "json_object"}

        start_time = time.perf_counter()
        try:
            call_coro = client.chat.completions.create(**payload_kwargs)
            response = await asyncio.wait_for(call_coro, timeout=self.timeout_seconds)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content_text = ""
            if response.choices and response.choices[0].message:
                content_text = response.choices[0].message.content or ""

            prompt_tokens = 0
            completion_tokens = 0
            if response.usage:
                prompt_tokens = response.usage.prompt_tokens or 0
                completion_tokens = response.usage.completion_tokens or 0

            return {
                "content": content_text,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "provider": self.name,
                "model": self.model,
                "latency_ms": latency_ms,
            }

        except (asyncio.TimeoutError, APITimeoutError):
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning("Groq request timed out after %.1fms (timeout=%.1fs)", latency_ms, self.timeout_seconds)
            raise AIEngineError(
                f"Groq request timed out after {self.timeout_seconds}s.",
                status_code=504,
                category="timeout",
                provider=self.name,
            )
        except RateLimitError as exc:
            msg = str(exc)
            logger.warning("Groq rate limit / quota exceeded: %s", msg)
            # Try to extract retry-after from response headers if available
            retry_after = None
            if hasattr(exc, "response") and exc.response and hasattr(exc.response, "headers"):
                try:
                    retry_after = float(exc.response.headers.get("retry-after", "60"))
                except (ValueError, TypeError):
                    pass
            raise AIEngineError(
                "Groq API quota exceeded or rate limit reached.",
                status_code=429,
                category="quota_exhausted",
                provider=self.name,
                retry_after=retry_after,
            )
        except AuthenticationError as exc:
            logger.error("Groq authentication failure: %s", exc)
            raise AIEngineError(
                "Groq API authentication failed. Verify GROQ_API_KEY.",
                status_code=401,
                category="auth_error",
                provider=self.name,
            )
        except APIConnectionError as exc:
            logger.warning("Groq connection failure: %s", exc)
            raise AIEngineError(
                "Cannot connect to Groq API. Check network or internet connectivity.",
                status_code=503,
                category="service_unavailable",
                provider=self.name,
            )
        except APIStatusError as exc:
            code = exc.status_code
            msg = str(exc)
            if code in (500, 502, 503, 504):
                raise AIEngineError(
                    f"Groq service temporarily unavailable (status {code}).",
                    status_code=503,
                    category="service_unavailable",
                    provider=self.name,
                )
            raise AIEngineError(
                f"Groq API status error: {msg}",
                status_code=code,
                category="invalid_request" if code == 400 else "api_error",
                provider=self.name,
            )
        except AIEngineError:
            raise
        except Exception as exc:
            logger.error("Unexpected error calling Groq: %s", exc)
            raise AIEngineError(
                f"Unexpected error communicating with Groq: {str(exc)}",
                status_code=500,
                category="api_error",
                provider=self.name,
            )

    async def check_health(self) -> Tuple[str, str]:
        """
        Validates Groq provider availability.
        Returns:
            Tuple of (status, details)
            Status values: 'ready', 'auth_error', 'quota_exhausted', 'rate_limited', 'unavailable', 'disabled'
        """
        if not self.is_configured:
            return (
                "configuration_error",
                "Groq is not configured. Set GROQ_API_KEY in backend environment.",
            )

        client = self._get_client()
        try:
            # Retrieve model information to verify key and model validity
            model_info = await asyncio.wait_for(
                client.models.retrieve(self.model),
                timeout=8.0,
            )
            return "ready", f"Groq is ready with model '{model_info.id}'."
        except (asyncio.TimeoutError, APITimeoutError):
            return "unavailable", "Groq health probe timed out after 8.0s."
        except RateLimitError as exc:
            return "quota_exhausted", f"Groq quota exhausted: {str(exc)}"
        except AuthenticationError:
            return "auth_error", "Invalid GROQ_API_KEY. Verify credentials."
        except Exception as exc:
            return "unavailable", f"Groq health check failed: {str(exc)}"
