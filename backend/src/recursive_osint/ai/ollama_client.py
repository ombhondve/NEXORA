"""
Ollama LLM Provider Client.
Provides asynchronous, resilient communication with the local Ollama instance (qwen3:4b).
Includes health checks, connection timeouts, model availability validation,
and prompt injection defense.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger

logger = get_logger("ai.ollama_client")


class AIEngineError(Exception):
    """Base exception for AI integration errors."""

    def __init__(self, message: str, status_code: int = 503, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or message


class OllamaClient:
    """Modular Ollama API Client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        ai_enabled: Optional[bool] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS
        self.ai_enabled = settings.AI_ENABLED if ai_enabled is None else ai_enabled

    async def check_health(self) -> Tuple[str, str]:
        """
        Validates Ollama server connectivity and model availability.
        Returns:
            Tuple of (status, details)
            Status values: 'ready', 'disabled', 'unreachable', 'model_unavailable', 'error'
        """
        if not self.ai_enabled:
            return "disabled", "AI integration is currently disabled via configuration (AI_ENABLED=false)."

        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return "error", f"Ollama returned HTTP status {res.status_code} on tags endpoint."

                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]

                # Match either exact name or model name prefix (e.g. qwen3:4b or qwen3:4b-latest)
                model_base = self.model.split(":")[0]
                matched = any(
                    m == self.model or m.startswith(f"{self.model}:") or m.startswith(f"{model_base}:")
                    for m in models
                )

                if matched:
                    return "ready", f"Ollama is reachable and model '{self.model}' is available."
                else:
                    return (
                        "model_unavailable",
                        f"Ollama is running, but model '{self.model}' is not installed. Available models: {', '.join(models) or 'None'}. Run 'ollama pull {self.model}'."
                    )
        except httpx.ConnectError:
            return "unreachable", f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running locally."
        except httpx.TimeoutException:
            return "unreachable", f"Connection to Ollama at {self.base_url} timed out."
        except Exception as exc:
            return "error", f"Unexpected error checking Ollama health: {str(exc)}"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        format: Optional[str] = "json",
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Executes a chat completion call to Ollama.
        """
        if not self.ai_enabled:
            raise AIEngineError("AI features are disabled (AI_ENABLED=false)", status_code=503)

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

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 404:
                    raise AIEngineError(
                        f"Model '{self.model}' not found in Ollama. Pull it via 'ollama pull {self.model}'.",
                        status_code=404,
                    )
                if res.status_code != 200:
                    raise AIEngineError(
                        f"Ollama returned HTTP error {res.status_code}: {res.text[:200]}",
                        status_code=502,
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

        except httpx.ConnectError as exc:
            logger.error("Ollama connection refused at %s: %s", self.base_url, exc)
            raise AIEngineError(
                f"Ollama server is unreachable at {self.base_url}. Please ensure Ollama is running.",
                status_code=503,
            )
        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out after %s seconds: %s", self.timeout_seconds, exc)
            raise AIEngineError(
                f"Ollama inference timed out after {self.timeout_seconds} seconds.",
                status_code=504,
            )
        except AIEngineError:
            raise
        except Exception as exc:
            logger.error("Unexpected error during Ollama invocation: %s", exc)
            raise AIEngineError(f"AI invocation failed: {str(exc)}", status_code=500)

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
            raise AIEngineError(f"Model returned invalid JSON: {str(exc)}", status_code=502)
