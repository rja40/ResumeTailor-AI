"""OpenAI provider implementation."""
from __future__ import annotations

from openai import OpenAI

from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """Works against any OpenAI-compatible endpoint.

    Pass `base_url` to point at OpenRouter, Together, vLLM, etc.; leave empty
    to use the official OpenAI API.
    """

    def __init__(self, api_key: str, model: str, base_url: str = ""):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self._model = model

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = response.choices[0]
        usage = response.usage
        if choice.finish_reason == "length":
            raise RuntimeError(
                f"LLM output was truncated (hit max_tokens={max_tokens}). "
                f"Raise LLM_MAX_TOKENS in .env and retry. "
                f"Note: OpenRouter free tier caps available tokens by remaining credits."
            )
        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
