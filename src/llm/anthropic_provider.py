"""Anthropic provider implementation."""
from __future__ import annotations

from anthropic import Anthropic

from .base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self._model,
            "system": system,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user}],
        }
        # Newer Claude models (e.g. opus-4-7) deprecate `temperature`.
        if not self._model.startswith(("claude-opus-4-7", "claude-opus-4.7")):
            kwargs["temperature"] = temperature

        message = self._client.messages.create(**kwargs)
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        if message.stop_reason == "max_tokens":
            raise RuntimeError(
                f"LLM output was truncated (hit max_tokens={max_tokens}). "
                f"Increase LLM_MAX_TOKENS in .env and retry."
            )
        return LLMResponse(
            text=text,
            model=self._model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
