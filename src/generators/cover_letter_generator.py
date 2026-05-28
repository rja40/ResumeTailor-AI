"""Generate tailored cover letter."""
from __future__ import annotations

from typing import Any

from ..analysis.extractor import to_pretty_json
from ..prompts.cover_letter import COVER_LETTER_SYSTEM, COVER_LETTER_USER
from ..utils.cache import cached_complete


def generate_cover_letter(
    jd_struct: dict[str, Any],
    resume_struct: dict[str, Any],
    resume_text: str,
) -> str:
    user = COVER_LETTER_USER.format(
        jd_json=to_pretty_json(jd_struct),
        resume_json=to_pretty_json(resume_struct),
        resume_text=resume_text,
    )
    return cached_complete(COVER_LETTER_SYSTEM, user).strip()
