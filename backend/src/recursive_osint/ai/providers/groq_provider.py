"""
Groq AI Provider for NEXORA.
Implements secondary / fallback AI model generation using the official groq SDK.
Supports dynamic model verification against Groq's catalog, structured JSON output,
timeout handling, granular error mapping (quota vs auth vs invalid model), and credential security.
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

# Known active Groq models in order of capability / preference
GROQ_PREFERENCE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "meta-models/muse-spark-open",
]


class GroqProvider(BaseAIProvider):
    """Secondary / Fallback AI provider leveraging Groq LPU inference."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        name = "groq"
        active_model = (model or settings.GROQ_MODEL or "openai/gpt-oss-120b").strip()
        active_timeout = timeout_seconds or settings.GROQ_TIMEOUT_SECONDS or 60.0
        super().__init__(name=name, model=active_model, timeout_seconds=active_timeout)

        self.api_key = (api_key or settings.GROQ_API_KEY or "").strip()
        self._client: Optional[AsyncGroq] = None
        self._resolved_model: Optional[str] = None
        self._model_verified: bool = False

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

    async def resolve_working_model(self) -> str:
        """
        Verifies the configured Groq model against the account's active model catalog.
        If the configured model is available, returns it.
        Otherwise, automatically resolves to a verified candidate (e.g. openai/gpt-oss-120b).
        """
        if self._resolved_model and self._model_verified:
            return self._resolved_model

        if not self.is_configured:
            return self.model

        client = self._get_client()
        configured_target = self.model.strip()

        try:
            model_list_resp = await client.models.list()
            available_ids = [getattr(m, "id", "") for m in getattr(model_list_resp, "data", []) if getattr(m, "id", "")]
            logger.info("Groq model discovery: retrieved %d available models for this account", len(available_ids))

            # If user's configured model is in available_ids, use it
            if configured_target in available_ids:
                self._resolved_model = configured_target
                self._model_verified = True
                return self._resolved_model

            # Check if any preference models are available in the catalog
            for cand in GROQ_PREFERENCE_MODELS:
                if cand in available_ids:
                    logger.warning(
                        "Configured Groq model '%s' is not accessible for this account. "
                        "Automatically resolved to verified model '%s'.",
                        self.model,
                        cand,
                    )
                    self._resolved_model = cand
                    self._model_verified = True
                    return self._resolved_model

            if available_ids:
                # Use first active model
                self._resolved_model = available_ids[0]
                self._model_verified = True
                return self._resolved_model

        except Exception as exc:
            logger.warning(
                "Could not dynamically query Groq models catalog (%s). Using configured model '%s'.",
                str(exc),
                self.model,
            )

        self._resolved_model = configured_target
        return self._resolved_model

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
        model_to_use = await self.resolve_working_model()

        payload_kwargs: Dict[str, Any] = {
            "model": model_to_use,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload_kwargs["response_format"] = {"type": "json_object"}

        start_time = time.perf_counter()
        try:
            logger.info("Calling Groq API with model: %s (json_mode=%s)...", model_to_use, json_mode)
            call_coro = client.chat.completions.create(**payload_kwargs)
            response = await asyncio.wait_for(call_coro, timeout=self.timeout_seconds)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content_text = ""
            if response.choices and response.choices[0].message:
                content_text = response.choices[0].message.content or ""

            prompt_tokens = 0
            completion_tokens = 0
            if response.usage:
                prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0

            return {
                "content": content_text,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "provider": self.name,
                "model": model_to_use,
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
            # Differentiate invalid/retired model error from quota exhaustion
            if (
                code == 404
                or "does not exist" in msg.lower()
                or "do not have access to it" in msg.lower()
                or "model_not_found" in msg.lower()
            ):
                logger.warning("Groq model not found or inaccessible: %s", msg)
                raise AIEngineError(
                    f"Groq model '{model_to_use}' does not exist or account lacks access: {msg}",
                    status_code=404,
                    category="invalid_model",
                    provider=self.name,
                )
            elif code in (500, 502, 503, 504):
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
            Status values: 'ready', 'auth_error', 'quota_exhausted', 'rate_limited', 'invalid_model', 'unavailable', 'disabled'
        """
        if not self.is_configured:
            return (
                "configuration_error",
                "Groq is not configured. Set GROQ_API_KEY in backend environment.",
            )

        client = self._get_client()
        try:
            model_to_check = await self.resolve_working_model()
            # Retrieve model information to verify key and model validity
            model_info = await asyncio.wait_for(
                client.models.retrieve(model_to_check),
                timeout=8.0,
            )
            return "ready", f"Groq is ready with model '{model_info.id}'."
        except (asyncio.TimeoutError, APITimeoutError):
            return "unavailable", "Groq health probe timed out after 8.0s."
        except RateLimitError as exc:
            return "quota_exhausted", f"Groq quota exhausted: {str(exc)}"
        except AuthenticationError:
            return "auth_error", "Invalid GROQ_API_KEY. Verify credentials."
        except APIStatusError as exc:
            code = exc.status_code
            msg = str(exc)
            if code == 404 or "does not exist" in msg.lower() or "do not have access to it" in msg.lower():
                return "invalid_model", f"Groq model '{self.model}' does not exist or account lacks access: {msg}"
            return "unavailable", f"Groq health check error (status {code}): {msg}"
        except Exception as exc:
            return "unavailable", f"Groq health check failed: {str(exc)}"
