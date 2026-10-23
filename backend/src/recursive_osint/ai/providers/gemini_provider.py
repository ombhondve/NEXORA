"""
Google Gemini AI Provider for NEXORA.
Implements primary AI model generation using the official google-genai SDK.
Supports structured JSON output, timeout handling, error mapping, and credential security.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from google.genai import Client, types
from google.genai.errors import APIError

from recursive_osint.ai.errors import AIEngineError
from recursive_osint.ai.providers.base import BaseAIProvider
from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger

logger = get_logger("ai.provider.gemini")


class GeminiProvider(BaseAIProvider):
    """Primary AI provider leveraging Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        name = "gemini"
        active_model = model or settings.GEMINI_MODEL or "gemini-1.5-flash"
        active_timeout = timeout_seconds or settings.GEMINI_TIMEOUT_SECONDS or 60.0
        super().__init__(name=name, model=active_model, timeout_seconds=active_timeout)

        self.api_key = (api_key or settings.GEMINI_API_KEY or "").strip()
        self._client: Optional[Client] = None
        if self.api_key:
            self._client = Client(api_key=self.api_key)

    @property
    def is_configured(self) -> bool:
        """Returns True if a non-empty API key is configured."""
        return bool(self.api_key and len(self.api_key) > 5)

    def _get_client(self) -> Client:
        if not self._client:
            if not self.is_configured:
                raise AIEngineError(
                    "Google Gemini API key is missing. Set GEMINI_API_KEY in your environment.",
                    status_code=503,
                    category="configuration_error",
                    provider=self.name,
                )
            self._client = Client(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes an asynchronous content generation request against Google Gemini.
        """
        client = self._get_client()

        # Separate system instruction from conversation contents
        system_instruction: Optional[str] = None
        contents: List[str] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                if system_instruction:
                    system_instruction += "\n\n" + content
                else:
                    system_instruction = content
            else:
                contents.append(content)

        if not contents:
            contents = ["Please analyze the provided evidence."]

        full_content = "\n\n".join(contents)

        # Build config
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json" if json_mode else "text/plain",
        )

        start_time = time.perf_counter()
        try:
            call_coro = client.aio.models.generate_content(
                model=self.model,
                contents=full_content,
                config=config,
            )
            response = await asyncio.wait_for(call_coro, timeout=self.timeout_seconds)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            content_text = ""
            if response.text:
                content_text = response.text
            elif response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts or []
                content_text = "".join(getattr(p, "text", "") for p in parts)

            prompt_tokens = 0
            completion_tokens = 0
            if response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

            return {
                "content": content_text,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "provider": self.name,
                "model": self.model,
                "latency_ms": latency_ms,
            }

        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning("Gemini request timed out after %.1fms (timeout=%.1fs)", latency_ms, self.timeout_seconds)
            raise AIEngineError(
                f"Gemini request timed out after {self.timeout_seconds}s.",
                status_code=504,
                category="timeout",
                provider=self.name,
            )
        except APIError as exc:
            code = getattr(exc, "code", 500)
            msg = str(exc.message or exc)
            # Map specific Gemini HTTP error codes
            if code == 429 or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                logger.warning("Gemini quota exhausted / rate limit reached: %s", msg)
                raise AIEngineError(
                    "Google Gemini API quota exceeded or rate limit reached.",
                    status_code=429,
                    category="quota_exhausted",
                    provider=self.name,
                )
            elif code in (401, 403) or "API_KEY_INVALID" in msg or "permission" in msg.lower():
                logger.error("Gemini authentication failure: %s", msg)
                raise AIEngineError(
                    "Google Gemini API authentication failed. Verify GEMINI_API_KEY.",
                    status_code=401,
                    category="auth_error",
                    provider=self.name,
                )
            elif code in (500, 502, 503, 504) or "UNAVAILABLE" in msg:
                logger.warning("Gemini service unavailable: %s", msg)
                raise AIEngineError(
                    f"Gemini service temporarily unavailable (status {code}).",
                    status_code=503,
                    category="service_unavailable",
                    provider=self.name,
                )
            else:
                logger.warning("Gemini API error (code %s): %s", code, msg)
                raise AIEngineError(
                    f"Gemini API error: {msg}",
                    status_code=code if isinstance(code, int) and 400 <= code <= 599 else 500,
                    category="invalid_request" if code == 400 else "api_error",
                    provider=self.name,
                )
        except AIEngineError:
            raise
        except Exception as exc:
            logger.error("Unexpected error calling Gemini: %s", exc)
            raise AIEngineError(
                f"Unexpected error communicating with Gemini: {str(exc)}",
                status_code=500,
                category="api_error",
                provider=self.name,
            )

    async def check_health(self) -> Tuple[str, str]:
        """
        Validates Gemini provider availability.
        Returns:
            Tuple of (status, details)
            Status values: 'ready', 'auth_error', 'quota_exhausted', 'rate_limited', 'unavailable', 'disabled'
        """
        if not self.is_configured:
            return (
                "configuration_error",
                "Google Gemini is not configured. Set GEMINI_API_KEY in backend environment.",
            )

        client = self._get_client()
        try:
            # Lightweight model metadata retrieval to verify key and model validity without full inference
            model_info = await asyncio.wait_for(
                client.aio.models.get(model=self.model),
                timeout=8.0,
            )
            display_name = getattr(model_info, "display_name", self.model)
            return "ready", f"Google Gemini is ready with model '{display_name}' ({self.model})."
        except asyncio.TimeoutError:
            return "unavailable", "Gemini health probe timed out after 8.0s."
        except APIError as exc:
            code = getattr(exc, "code", 500)
            msg = str(exc.message or exc)
            if code == 429 or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                return "quota_exhausted", f"Gemini quota exhausted: {msg}"
            elif code in (401, 403) or "API_KEY_INVALID" in msg:
                return "auth_error", "Invalid GEMINI_API_KEY. Verify credentials."
            return "unavailable", f"Gemini health check error (code {code}): {msg}"
        except Exception as exc:
            return "unavailable", f"Gemini health check failed: {str(exc)}"
