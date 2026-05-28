"""Helpers for coercing LLM output into JSON."""
from __future__ import annotations

import json
import re
from typing import Any


class JSONParseError(ValueError):
    pass


def extract_json(text: str) -> Any:
    """Pull a JSON object/array out of LLM text, tolerating markdown fences."""
    if not text or not text.strip():
        raise JSONParseError("Empty LLM response")

    # Strip code fences if present.
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else text

    # Try direct parse.
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Greedy: first { ... last } or first [ ... last ].
    for opener, closer in (("{", "}"), ("[", "]")):
        start = candidate.find(opener)
        end = candidate.rfind(closer)
        if start != -1 and end != -1 and end > start:
            chunk = candidate[start : end + 1]
            try:
                return json.loads(chunk)
            except json.JSONDecodeError:
                continue

    raise JSONParseError(f"Could not parse JSON from LLM output:\n{text[:500]}")
