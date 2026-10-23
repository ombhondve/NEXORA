"""
Google Gemini AI Provider for NEXORA.
Implements primary AI model generation using the official google-genai SDK.
Supports dynamic model verification against Google's API, structured JSON output,
timeout handling, granular error mapping (quota vs auth vs invalid model), and credential security.
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

# Known active Gemini models supporting generateContent in order of preference
PREFERENCE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-pro",
]


class GeminiProvider(BaseAIProvider):
    """Primary AI provider leveraging Google Gemini API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        name = "gemini"
        active_model = (model or settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
        active_timeout = timeout_seconds or settings.GEMINI_TIMEOUT_SECONDS or 60.0
        super().__init__(name=name, model=active_model, timeout_seconds=active_timeout)

        self.api_key = (api_key or settings.GEMINI_API_KEY or "").strip()
        self._client: Optional[Client] = None
        self._resolved_model: Optional[str] = None
        self._model_verified: bool = False

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

    async def resolve_working_model(self) -> str:
        """
        Verifies the configured Gemini model against Google's currently available models for this API key.
        If the configured model is found and supports generateContent, returns it.
        Otherwise, automatically resolves to a verified compatible Flash model that supports generateContent.
        """
        if self._resolved_model and self._model_verified:
            return self._resolved_model

        if not self.is_configured:
            return self.model

        client = self._get_client()
        configured_target = self.model.removeprefix("models/").strip()

        try:
            available_models: List[str] = []
            pager = await client.aio.models.list()
            async for m in pager:
                name = getattr(m, "name", "") or ""
                canonical = name.removeprefix("models/").strip()
                actions = getattr(m, "supported_actions", []) or []
                supports_generate = (
                    not actions
                    or "generateContent" in actions
                    or "generate_content" in actions
                    or any("generate" in str(a).lower() for a in actions)
                )
                if supports_generate and canonical:
                    available_models.append(canonical)

            logger.info(
                "Gemini API model discovery: found %d models supporting generateContent for this key",
                len(available_models),
            )

            # If the user's configured model is in available_models, use it
            if configured_target in available_models:
                self._resolved_model = configured_target
                self._model_verified = True
                return self._resolved_model

            # If user's model is not available or deprecated on v1beta, select compatible Flash model
            for candidate in PREFERENCE_MODELS:
                if candidate in available_models:
                    logger.warning(
                        "Configured Gemini model '%s' not supported or not found for this key. "
                        "Automatically resolved to verified model '%s'.",
                        self.model,
                        candidate,
                    )
                    self._resolved_model = candidate
                    self._model_verified = True
                    return self._resolved_model

            # Fallback to first available flash/gemini model
            flash_models = [m for m in available_models if "flash" in m.lower()]
            if flash_models:
                self._resolved_model = flash_models[0]
                self._model_verified = True
                return self._resolved_model

            if available_models:
                self._resolved_model = available_models[0]
                self._model_verified = True
                return self._resolved_model

        except Exception as exc:
            # Model listing may fail due to permissions, network, or mock clients
            logger.warning(
                "Could not dynamically query Gemini models list (%s). Using configured model '%s'.",
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
        Executes an asynchronous content generation request against Google Gemini.
        """
        client = self._get_client()
        model_to_use = await self.resolve_working_model()

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
            logger.info("Calling Gemini API with model: %s (json_mode=%s)...", model_to_use, json_mode)
            call_coro = client.aio.models.generate_content(
                model=model_to_use,
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
                "model": model_to_use,
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
                    "Google Gemini API authentication failed. Verify GEMINI_API_KEY in backend environment.",
                    status_code=401,
                    category="auth_error",
                    provider=self.name,
                )
            elif (
                code == 404
                or "is not found for API version" in msg
                or "not supported for generateContent" in msg
            ):
                logger.warning("Gemini model not found or not supported: %s", msg)
                raise AIEngineError(
                    f"Gemini model '{model_to_use}' is not supported or not found for API version v1beta: {msg}",
                    status_code=404,
                    category="invalid_model",
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
            Status values: 'ready', 'auth_error', 'quota_exhausted', 'rate_limited', 'invalid_model', 'unavailable', 'disabled'
        """
        if not self.is_configured:
            return (
                "configuration_error",
                "Google Gemini is not configured. Set GEMINI_API_KEY in backend environment.",
            )

        client = self._get_client()
        try:
            model_to_check = await self.resolve_working_model()
            # Lightweight model metadata retrieval to verify key and model validity without full inference
            model_info = await asyncio.wait_for(
                client.aio.models.get(model=model_to_check),
                timeout=8.0,
            )
            display_name = getattr(model_info, "display_name", model_to_check)
            return "ready", f"Google Gemini is ready with model '{display_name}' ({model_to_check})."
        except asyncio.TimeoutError:
            return "unavailable", "Gemini health probe timed out after 8.0s."
        except APIError as exc:
            code = getattr(exc, "code", 500)
            msg = str(exc.message or exc)
            if code == 429 or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                return "quota_exhausted", f"Gemini quota exhausted: {msg}"
            elif code in (401, 403) or "API_KEY_INVALID" in msg:
                return "auth_error", "Invalid GEMINI_API_KEY. Verify credentials."
            elif code == 404 or "is not found for API version" in msg or "not supported for generateContent" in msg:
                return "invalid_model", f"Gemini model '{self.model}' is not supported or not found: {msg}"
            return "unavailable", f"Gemini health check error (code {code}): {msg}"
        except Exception as exc:
            return "unavailable", f"Gemini health check failed: {str(exc)}"
