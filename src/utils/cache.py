"""In-process cache for deterministic LLM calls."""
from __future__ import annotations

import hashlib
from functools import lru_cache

from ..config import settings
from ..llm import get_provider


def _key(system: str, user: str, temperature: float, max_tokens: int) -> str:
    h = hashlib.sha256()
    h.update(settings.active_model.encode())
    h.update(b"|")
    h.update(system.encode())
    h.update(b"|")
    h.update(user.encode())
    h.update(f"|{temperature}|{max_tokens}".encode())
    return h.hexdigest()


@lru_cache(maxsize=128)
def _cached_call(key: str, system: str, user: str, temperature: float, max_tokens: int) -> str:
    return get_provider().complete(
        system=system,
        user=user,
        temperature=temperature,
        max_tokens=max_tokens,
    ).text


def cached_complete(
    system: str,
    user: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Run an LLM call, dedup-cached by (model, system, user, params)."""
    t = settings.temperature if temperature is None else temperature
    m = settings.max_tokens if max_tokens is None else max_tokens
    return _cached_call(_key(system, user, t, m), system, user, t, m)
