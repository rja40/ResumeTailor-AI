"""Compute JD-to-resume match score."""
from __future__ import annotations

from typing import Any

from ..prompts.matching import MATCH_SCORE_SYSTEM, MATCH_SCORE_USER
from ..utils.cache import cached_complete
from ..utils.json_utils import extract_json
from .extractor import to_pretty_json


def compute_match(
    jd_struct: dict[str, Any],
    resume_struct: dict[str, Any],
    resume_text: str,
) -> dict[str, Any]:
    user = MATCH_SCORE_USER.format(
        jd_json=to_pretty_json(jd_struct),
        resume_json=to_pretty_json(resume_struct),
        resume_text=resume_text,
    )
    raw = cached_complete(MATCH_SCORE_SYSTEM, user)
    return extract_json(raw)
