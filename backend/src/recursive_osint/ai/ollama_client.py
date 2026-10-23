"""
Ollama LLM Provider Client.
Provides asynchronous, resilient communication with the Ollama instance (qwen3:4b).
Includes URL validation, credential redaction, health checks, connection timeouts,
model availability validation, bounded retries, and structured error categorization.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import httpx

from recursive_osint.config import settings, is_serverless_environment
from recursive_osint.core.logging import get_logger

logger = get_logger("ai.ollama_client")


def redact_url(url: str) -> str:
    """Redacts basic auth credentials from a URL for safe logging."""
    if not url:
        return "none"
    try:
        return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)
    except Exception:
        return url


def is_loopback_host(hostname: Optional[str]) -> bool:
    """Returns True if the hostname resolves to a loopback address."""
    if not hostname:
        return False
    return hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0")


class AIEngineError(Exception):
    """Structured exception for AI integration errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 503,
        details: Optional[str] = None,
        category: str = "ai_error",
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or message
        self.category = category


class OllamaClient:
    """Modular Ollama API Client with robust environment handling."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        ai_enabled: Optional[bool] = None,
    ):
        raw_url = base_url or settings.OLLAMA_BASE_URL
        self.base_url = (raw_url or "").rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS
        self.ai_enabled = settings.AI_ENABLED if ai_enabled is None else ai_enabled

    @property
    def redacted_base_url(self) -> str:
        """Returns the base URL with any credentials redacted for safe logging and diagnostics."""
        return redact_url(self.base_url)

    def validate_endpoint_configuration(self) -> Tuple[bool, Optional[str]]:
        """
        Validates the configured Ollama endpoint URL.
        Returns (is_valid, error_diagnostic).
        """
        if not self.base_url:
            return False, "Ollama base URL is empty. Please set OLLAMA_BASE_URL."

        try:
            parsed = urlparse(self.base_url)
        except Exception as exc:
            return False, f"Malformed OLLAMA_BASE_URL: {str(exc)}"

        if parsed.scheme not in ("http", "https"):
            return False, f"Invalid URL scheme '{parsed.scheme}'. OLLAMA_BASE_URL must use http:// or https://."

        if not parsed.hostname:
            return False, "OLLAMA_BASE_URL is missing a valid hostname."

        # Detect deployment mismatch: Cloud/Serverless function targeting developer localhost
        is_cloud = is_serverless_environment() or settings.ENVIRONMENT == "production"
        if is_cloud and is_loopback_host(parsed.hostname):
            return (
                False,
                (
                    f"AI provider configuration error: The backend is deployed in a cloud/serverless "
                    f"environment ({settings.ENVIRONMENT}) and cannot connect to '{self.redacted_base_url}'. "
                    f"Localhost refers to the ephemeral serverless container, not your local machine. "
                    f"Please configure OLLAMA_BASE_URL to a reachable external Ollama endpoint "
                    f"in your Vercel project environment variables (e.g. https://your-ollama-host:11434)."
                ),
            )

        return True, None

    async def check_health(self) -> Tuple[str, str]:
        """
        Validates Ollama server connectivity and model availability without running expensive inference.
        Returns:
            Tuple of (status, details)
            Status values: 'ready', 'disabled', 'configuration_error', 'unreachable', 'model_unavailable', 'error'
        """
        if not self.ai_enabled:
            return "disabled", "AI integration is currently disabled via configuration (AI_ENABLED=false)."

        is_valid, config_error = self.validate_endpoint_configuration()
        if not is_valid and config_error:
            return "configuration_error", config_error

        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return "error", f"Ollama returned HTTP status {res.status_code} on tags endpoint at {self.redacted_base_url}."

                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]

                # Match either exact name or model name prefix (e.g. qwen3:4b or qwen3:4b-latest)
                model_base = self.model.split(":")[0]
                matched = any(
                    m == self.model
                    or m.startswith(f"{self.model}:")
                    or m.startswith(f"{model_base}:")
                    for m in models
                )

                if matched:
                    return "ready", f"Ollama is reachable and model '{self.model}' is available at {self.redacted_base_url}."
                else:
                    return (
                        "model_unavailable",
                        (
                            f"Ollama is reachable at {self.redacted_base_url}, but model '{self.model}' is not installed. "
                            f"Available models: {', '.join(models) or 'None'}. Run 'ollama pull {self.model}' on the Ollama host."
                        ),
                    )
        except httpx.ConnectError:
            if is_loopback_host(urlparse(self.base_url).hostname):
                return (
                    "unreachable",
                    f"Cannot connect to Ollama at {self.redacted_base_url}. Ensure the Ollama service is running.",
                )
            return (
                "unreachable",
                f"Cannot connect to remote Ollama at {self.redacted_base_url}. Verify network connectivity and security groups.",
            )
        except httpx.TimeoutException:
            return "unreachable", f"Connection to Ollama at {self.redacted_base_url} timed out."
        except Exception as exc:
            return "error", f"Unexpected error checking Ollama health: {str(exc)}"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        format: Optional[str] = "json",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Executes a chat completion call to Ollama with bounded retries and structured error handling.
        """
        if not self.ai_enabled:
            raise AIEngineError(
                "AI features are disabled via configuration (AI_ENABLED=false).",
                status_code=503,
                category="ai_disabled",
            )

        is_valid, config_error = self.validate_endpoint_configuration()
        if not is_valid and config_error:
            raise AIEngineError(
                config_error,
                status_code=503,
                category="configuration_error",
            )

        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if format:
            payload["format"] = format

        # Bounded retries: max 1 retry for transient network drops (never retry indefinitely)
        max_attempts = 2
        last_exception: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 404:
                        raise AIEngineError(
                            f"Model '{self.model}' not found in Ollama at {self.redacted_base_url}. "
                            f"Please pull it via 'ollama pull {self.model}'.",
                            status_code=404,
                            category="model_unavailable",
                        )
                    if res.status_code != 200:
                        raise AIEngineError(
                            f"Ollama returned HTTP error {res.status_code}: {res.text[:200]}",
                            status_code=502,
                            category="invalid_model_response",
                        )

                    data = res.json()
                    message_content = data.get("message", {}).get("content", "")
                    prompt_tokens = data.get("prompt_eval_count", 0)
                    completion_tokens = data.get("eval_count", 0)

                    return {
                        "content": message_content,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    }

            except AIEngineError:
                raise
            except httpx.ConnectError as exc:
                last_exception = exc
                logger.warning(
                    "Ollama connection refused at %s (attempt %d/%d): %s",
                    self.redacted_base_url,
                    attempt,
                    max_attempts,
                    exc,
                )
                if attempt < max_attempts and not is_loopback_host(urlparse(self.base_url).hostname):
                    await asyncio.sleep(0.5)
                    continue
                break
            except httpx.TimeoutException as exc:
                last_exception = exc
                logger.warning(
                    "Ollama request timed out after %s seconds at %s (attempt %d/%d)",
                    self.timeout_seconds,
                    self.redacted_base_url,
                    attempt,
                    max_attempts,
                )
                if attempt < max_attempts:
                    await asyncio.sleep(0.5)
                    continue
                break
            except Exception as exc:
                logger.error("Unexpected error during Ollama invocation: %s", exc)
                raise AIEngineError(
                    f"AI invocation failed: {str(exc)}",
                    status_code=500,
                    category="ai_error",
                )

        if isinstance(last_exception, httpx.ConnectError):
            parsed_host = urlparse(self.base_url).hostname
            if is_loopback_host(parsed_host):
                msg = (
                    f"Ollama server is unreachable at {self.redacted_base_url}. "
                    "Ensure Ollama is running locally and the model is loaded."
                )
            else:
                msg = (
                    f"Ollama server is unreachable at {self.redacted_base_url}. "
                    "Verify the remote host is accessible and security rules permit inbound traffic."
                )
            raise AIEngineError(msg, status_code=503, category="provider_unreachable")

        if isinstance(last_exception, httpx.TimeoutException):
            raise AIEngineError(
                f"Ollama inference timed out after {self.timeout_seconds} seconds.",
                status_code=504,
                category="request_timeout",
            )

        raise AIEngineError(
            f"AI invocation failed: {str(last_exception)}",
            status_code=503,
            category="provider_unreachable",
        )

    @staticmethod
    def parse_json_safely(raw_text: str) -> Dict[str, Any]:
        """
        Safely extracts and parses JSON even if wrapped in markdown code blocks.
        """
        clean_text = raw_text.strip()
        # Strip markdown ```json ... ``` or ``` ... ```
        if "```" in clean_text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
            if match:
                clean_text = match.group(1).strip()

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode JSON from AI response: %s | Raw snippet: %s", exc, raw_text[:300])
            raise AIEngineError(
                f"Model returned invalid JSON: {str(exc)}",
                status_code=502,
                category="invalid_model_response",
            )
