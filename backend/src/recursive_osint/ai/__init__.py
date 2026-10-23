"""
NEXORA AI Intelligence Layer.
Provides multi-provider management (Gemini primary, Groq fallback),
evidence analysis, entity and relationship generation, and grounded Q&A.
"""

from recursive_osint.ai.errors import AIEngineError
from recursive_osint.ai.provider_manager import AIProviderManager, get_ai_provider_manager

__all__ = ["AIEngineError", "AIProviderManager", "get_ai_provider_manager"]
