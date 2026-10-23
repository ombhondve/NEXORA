"""
Centralized AI Provider Manager for NEXORA.
Coordinates bidirectional provider routing between Google Gemini (Primary) and Groq (Secondary / Fallback).
Implements automatic quota fallback, cooldown recovery, JSON repair, token accounting, and concurrency guards.
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from recursive_osint.ai.errors import AIEngineError
from recursive_osint.ai.providers.base import BaseAIProvider
from recursive_osint.ai.providers.gemini_provider import GeminiProvider
from recursive_osint.ai.providers.groq_provider import GroqProvider
from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger

logger = get_logger("ai.provider_manager")


@dataclass
class ProviderRuntimeState:
    """Tracks runtime operational state and quota health for a single AI provider."""
    name: str
    status: str = "ready"  # ready, rate_limited, quota_exhausted, auth_error, invalid_model, unavailable, disabled, unconfigured
    cooldown_until: float = 0.0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    last_error_category: Optional[str] = None
    last_error_message: Optional[str] = None
    retry_after: Optional[float] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    @property
    def is_in_cooldown(self) -> bool:
        """Returns True if the provider is currently cooling down from a rate limit or quota exhaustion."""
        return time.time() < self.cooldown_until

    def mark_success(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Records a successful request and restores ready status."""
        self.status = "ready"
        self.cooldown_until = 0.0
        self.last_success_time = time.time()
        self.successful_requests += 1
        self.total_requests += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

    def mark_failure(
        self,
        category: str,
        message: str,
        cooldown_seconds: float = 60.0,
        retry_after: Optional[float] = None,
    ) -> None:
        """Records a failure and sets appropriate cooldown state."""
        self.last_failure_time = time.time()
        self.last_error_category = category
        self.last_error_message = message
        self.failed_requests += 1
        self.total_requests += 1

        effective_cooldown = retry_after if retry_after and retry_after > 0 else cooldown_seconds
        self.cooldown_until = time.time() + effective_cooldown
        self.retry_after = retry_after

        if category == "quota_exhausted":
            self.status = "quota_exhausted"
        elif category == "rate_limited":
            self.status = "rate_limited"
        elif category == "auth_error":
            self.status = "auth_error"
            self.cooldown_until = time.time() + 3600.0
        elif category == "invalid_model":
            self.status = "invalid_model"
            self.cooldown_until = time.time() + 1800.0
        else:
            self.status = "unavailable"


class AIProviderManager:
    """
    Centralized AI Provider Manager.
    Directs all model inferences through Google Gemini as primary, automatically failing over to Groq
    upon rate limits, quota exhaustion, or model/temporary outages, and seamlessly restoring Gemini when its cooldown expires.
    """

    def __init__(
        self,
        gemini_provider: Optional[BaseAIProvider] = None,
        groq_provider: Optional[BaseAIProvider] = None,
        ai_enabled: Optional[bool] = None,
    ):
        self.ai_enabled = settings.AI_ENABLED if ai_enabled is None else ai_enabled
        self.gemini = gemini_provider or GeminiProvider()
        self.groq = groq_provider or GroqProvider()

        self.state: Dict[str, ProviderRuntimeState] = {
            "gemini": ProviderRuntimeState(name="gemini"),
            "groq": ProviderRuntimeState(name="groq"),
        }

        self._lock = asyncio.Lock()

    @property
    def active_model(self) -> str:
        """Returns the currently expected primary model name."""
        return self.gemini.model

    @property
    def model(self) -> str:
        """Polymorphic alias for callers expecting .model attribute."""
        return self.active_model

    @property
    def active_provider_name(self) -> str:
        """Returns the name of the provider that would be chosen for the next request."""
        if (
            not self.state["gemini"].is_in_cooldown
            and self.gemini.is_configured
            and self.state["gemini"].status not in ("auth_error", "invalid_model")
        ):
            return "gemini"
        elif (
            self.groq.is_configured
            and not self.state["groq"].is_in_cooldown
            and self.state["groq"].status not in ("auth_error", "invalid_model")
        ):
            return "groq"
        return "gemini"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        format: Optional[str] = "json",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Unified inference entry point matching application callers.
        Executes bidirectional automatic failover and recovery.
        """
        if not self.ai_enabled:
            raise AIEngineError(
                "AI features are disabled via configuration (AI_ENABLED=false).",
                status_code=503,
                category="ai_disabled",
            )

        json_mode = (format == "json")

        # Determine eligible providers
        async with self._lock:
            gemini_configured = self.gemini.is_configured
            groq_configured = self.groq.is_configured

            if not gemini_configured and not groq_configured:
                raise AIEngineError(
                    "No AI provider credentials configured. Please set GEMINI_API_KEY (primary) "
                    "or GROQ_API_KEY (secondary/fallback) in your environment variables.",
                    status_code=503,
                    category="configuration_error",
                )

            # Check if Gemini cooldown has expired
            if self.state["gemini"].is_in_cooldown:
                gemini_available = False
            else:
                gemini_available = (
                    gemini_configured
                    and self.state["gemini"].status not in ("auth_error", "invalid_model")
                )

            if self.state["groq"].is_in_cooldown:
                groq_available = False
            else:
                groq_available = (
                    groq_configured
                    and self.state["groq"].status not in ("auth_error", "invalid_model")
                )

        # Routing decision:
        # Priority 1: Gemini (if available)
        # Priority 2: Groq (if Gemini is in cooldown/unconfigured/model_error and Groq is available)
        # Priority 3: Fallback check
        providers_to_try: List[Tuple[str, BaseAIProvider]] = []

        if gemini_available:
            providers_to_try.append(("gemini", self.gemini))
            if groq_configured and self.state["groq"].status not in ("auth_error", "invalid_model"):
                providers_to_try.append(("groq", self.groq))
        elif groq_available:
            providers_to_try.append(("groq", self.groq))
            if gemini_configured and self.state["gemini"].status not in ("auth_error", "invalid_model"):
                providers_to_try.append(("gemini", self.gemini))
        else:
            # Both providers are currently in cooldown or error state
            if gemini_configured and self.state["gemini"].status not in ("auth_error", "invalid_model"):
                providers_to_try.append(("gemini", self.gemini))
            if groq_configured and self.state["groq"].status not in ("auth_error", "invalid_model"):
                providers_to_try.append(("groq", self.groq))

        if not providers_to_try:
            # Check if one or both had invalid_model or auth_error
            gem_err = self.state["gemini"].last_error_message or self.state["gemini"].status
            groq_err = self.state["groq"].last_error_message or self.state["groq"].status
            raise AIEngineError(
                f"All configured AI providers are unavailable. Gemini: {gem_err}; Groq: {groq_err}.",
                status_code=503,
                category="configuration_error",
            )

        for provider_name, provider in providers_to_try:
            # Bounded execution: exactly 1 attempt per provider (no infinite loops)
            try:
                logger.info("Dispatching AI request to provider: %s (model: %s)...", provider_name, provider.model)
                res = await provider.generate(messages, temperature=temperature, json_mode=json_mode)

                # Record success in state
                async with self._lock:
                    self.state[provider_name].mark_success(
                        prompt_tokens=res.get("prompt_tokens", 0),
                        completion_tokens=res.get("completion_tokens", 0),
                    )
                    logger.info(
                        "AI request succeeded with %s (model: %s, latency: %.1fms, tokens: %d+%d)",
                        provider_name,
                        res.get("model", provider.model),
                        res.get("latency_ms", 0.0),
                        res.get("prompt_tokens", 0),
                        res.get("completion_tokens", 0),
                    )

                return res

            except AIEngineError as exc:
                category = exc.category
                logger.warning(
                    "AI Provider '%s' encountered %s: %s",
                    provider_name,
                    category,
                    exc.message,
                )

                # Compute cooldown
                cooldown_sec = (
                    getattr(settings, f"{provider_name.upper()}_QUOTA_COOLDOWN_SECONDS", 300.0)
                    if category == "quota_exhausted"
                    else getattr(settings, f"{provider_name.upper()}_RATE_LIMIT_COOLDOWN_SECONDS", 60.0)
                )

                async with self._lock:
                    self.state[provider_name].mark_failure(
                        category=category,
                        message=exc.message,
                        cooldown_seconds=cooldown_sec,
                        retry_after=exc.retry_after,
                    )

                # Fallback determination:
                if category in ("quota_exhausted", "rate_limited"):
                    logger.info("Failing over from %s to alternative provider due to quota/rate limit.", provider_name)
                    continue
                elif category in ("service_unavailable", "timeout"):
                    logger.info("Failing over from %s to alternative provider due to temporary outage.", provider_name)
                    continue
                elif category in ("invalid_model", "auth_error"):
                    logger.warning("Failing over from %s to alternative provider due to %s.", provider_name, category)
                    continue
                else:
                    # Invalid request or bad prompt: do not retry against alternative provider blindly
                    raise exc

        # If loop finishes without returning, all tried providers failed
        logger.error("All available AI providers failed to process the request.")
        gem_st = self.state["gemini"].status
        groq_st = self.state["groq"].status
        gem_msg = self.state["gemini"].last_error_message or "unavailable"
        groq_msg = self.state["groq"].last_error_message or "unavailable"

        raise AIEngineError(
            (
                "All AI providers are temporarily unavailable or unable to process the request. "
                f"Gemini: [{gem_st}] {gem_msg}; "
                f"Groq: [{groq_st}] {groq_msg}. "
                "Please verify provider configuration or retry after cooldown."
            ),
            status_code=503,
            category=(
                "quota_exhausted"
                if any(s.status == "quota_exhausted" for s in self.state.values())
                else "configuration_error"
                if any(s.status in ("auth_error", "invalid_model") for s in self.state.values())
                else "all_providers_unavailable"
            ),
        )

    async def check_health(self) -> Tuple[str, str]:
        """
        Synthesizes active provider health and fallback availability.
        Returns:
            Tuple of (status_code, details_string)
            status_code: 'ready', 'fallback_active', 'rate_limited', 'quota_exhausted', 'configuration_error', 'disabled'
        """
        if not self.ai_enabled:
            return "disabled", "AI features are disabled via configuration (AI_ENABLED=false)."

        gemini_configured = self.gemini.is_configured
        groq_configured = self.groq.is_configured

        if not gemini_configured and not groq_configured:
            return (
                "configuration_error",
                "No AI providers configured. Configure GEMINI_API_KEY (primary) or GROQ_API_KEY (fallback) in Vercel/backend environment.",
            )

        # Check Gemini status
        gemini_status, gemini_details = ("unconfigured", "GEMINI_API_KEY not set")
        if gemini_configured:
            if self.state["gemini"].is_in_cooldown:
                gemini_status = self.state["gemini"].status
                gemini_details = f"Gemini in cooldown ({self.state['gemini'].status}): {self.state['gemini'].last_error_message}"
            else:
                gemini_status, gemini_details = await self.gemini.check_health()
                if gemini_status != "ready":
                    self.state["gemini"].status = gemini_status
                    self.state["gemini"].last_error_message = gemini_details

        # Check Groq status
        groq_status, groq_details = ("unconfigured", "GROQ_API_KEY not set")
        if groq_configured:
            if self.state["groq"].is_in_cooldown:
                groq_status = self.state["groq"].status
                groq_details = f"Groq in cooldown ({self.state['groq'].status}): {self.state['groq'].last_error_message}"
            else:
                groq_status, groq_details = await self.groq.check_health()
                if groq_status != "ready":
                    self.state["groq"].status = groq_status
                    self.state["groq"].last_error_message = groq_details

        # Aggregate overall status
        if gemini_status == "ready":
            fallback_note = f" (Groq fallback: {groq_status})" if groq_configured else " (Groq fallback not configured)"
            return "ready", f"Primary provider Gemini is active with model '{self.gemini.model}'{fallback_note}."
        elif groq_status == "ready":
            return (
                "fallback_active",
                f"Groq fallback is active with model '{self.groq.model}'. Primary Gemini is {gemini_status} ({gemini_details}).",
            )
        elif gemini_status == "quota_exhausted" and groq_status == "quota_exhausted":
            return "quota_exhausted", "Both Gemini and Groq usage quotas are temporarily exhausted."
        elif gemini_status == "rate_limited" or groq_status == "rate_limited":
            return "rate_limited", f"AI providers are temporarily rate-limited. Gemini: {gemini_status}, Groq: {groq_status}."
        elif gemini_status in ("invalid_model", "auth_error") and not groq_configured:
            return "configuration_error", f"Gemini configuration error: {gemini_details}. Groq fallback is not configured."
        else:
            return "unavailable", f"AI providers unavailable. Gemini: [{gemini_status}] {gemini_details}; Groq: [{groq_status}] {groq_details}."

    @staticmethod
    def parse_json_safely(raw_content: str) -> Dict[str, Any]:
        """
        Robust JSON response extractor and repair parser.
        Strips markdown code blocks, removes trailing commas, and recovers from minor LLM syntax flaws.
        """
        if not raw_content or not raw_content.strip():
            raise AIEngineError("Model returned an empty response.", status_code=502, category="invalid_model_response")

        cleaned = raw_content.strip()

        # Strip markdown ```json ... ``` blocks
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Extract first outermost JSON object {...}
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
        else:
            candidate = cleaned

        # Attempt 1: Direct JSON parse
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Attempt 2: Strip trailing commas before closing braces/brackets
        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as exc:
            logger.warning("JSON decode failed on AI response: %s", exc)
            raise AIEngineError(
                f"Failed to parse valid structured JSON from model response: {str(exc)}",
                status_code=502,
                category="invalid_model_response",
            )


# Global singleton provider manager instance
_ai_manager_instance: Optional[AIProviderManager] = None


def get_ai_provider_manager() -> AIProviderManager:
    """Returns the global AIProviderManager singleton instance."""
    global _ai_manager_instance
    if _ai_manager_instance is None:
        _ai_manager_instance = AIProviderManager()
    return _ai_manager_instance
