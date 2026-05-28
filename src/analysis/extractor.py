"""Structured extraction from JD and resume text."""
from __future__ import annotations

import json
from typing import Any

from ..prompts.extraction import (
    JD_EXTRACTION_SYSTEM,
    JD_EXTRACTION_USER,
    RESUME_EXTRACTION_SYSTEM,
    RESUME_EXTRACTION_USER,
)
from ..utils.cache import cached_complete
from ..utils.json_utils import extract_json


def extract_resume(resume_text: str) -> dict[str, Any]:
    user = RESUME_EXTRACTION_USER.format(resume_text=resume_text)
    raw = cached_complete(RESUME_EXTRACTION_SYSTEM, user)
    return extract_json(raw)


def extract_jd(jd_text: str) -> dict[str, Any]:
    user = JD_EXTRACTION_USER.format(jd_text=jd_text)
    raw = cached_complete(JD_EXTRACTION_SYSTEM, user)
    return extract_json(raw)


def to_pretty_json(data: dict[str, Any] | list[Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
