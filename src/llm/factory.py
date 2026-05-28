"""Provider factory. Add new providers here."""
from __future__ import annotations

from functools import lru_cache

from ..config import settings
from .base import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider


@lru_cache(maxsize=1)
def get_provider() -> LLMProvider:
    if settings.provider == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    if settings.provider == "openai":
        return OpenAIProvider(
            settings.openai_api_key,
            settings.openai_model,
            base_url=settings.openai_base_url,
        )
    raise ValueError(f"Unknown provider: {settings.provider}")
