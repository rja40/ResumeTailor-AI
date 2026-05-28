"""Centralized settings loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

ProviderName = Literal["anthropic", "openai"]
ThemeName = Literal["terminal", "minimal", "workspace", "wizard"]

VALID_THEMES: tuple[ThemeName, ...] = ("terminal", "minimal", "workspace", "wizard")


@dataclass(frozen=True)
class Settings:
    provider: ProviderName
    anthropic_api_key: str
    anthropic_model: str
    openai_api_key: str
    openai_model: str
    openai_base_url: str          # empty = official OpenAI; set for OpenRouter/Together/etc.
    temperature: float
    max_tokens: int
    ui_theme: ThemeName

    @property
    def active_model(self) -> str:
        return self.anthropic_model if self.provider == "anthropic" else self.openai_model

    @property
    def active_api_key(self) -> str:
        return self.anthropic_api_key if self.provider == "anthropic" else self.openai_api_key


def load_settings() -> Settings:
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    if provider not in ("anthropic", "openai"):
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
    theme = os.getenv("UI_THEME", "terminal").lower()
    if theme not in VALID_THEMES:
        theme = "terminal"
    return Settings(
        provider=provider,  # type: ignore[arg-type]
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip(),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192")),
        ui_theme=theme,  # type: ignore[arg-type]
    )


settings = load_settings()
