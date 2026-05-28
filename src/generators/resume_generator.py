"""Generate tailored resume Markdown."""
from __future__ import annotations

from typing import Any

from ..analysis.extractor import to_pretty_json
from ..prompts.resume import RESUME_REWRITE_SYSTEM, RESUME_REWRITE_USER
from ..utils.cache import cached_complete


def generate_resume(
    jd_struct: dict[str, Any],
    resume_struct: dict[str, Any],
    resume_text: str,
) -> str:
    user = RESUME_REWRITE_USER.format(
        jd_json=to_pretty_json(jd_struct),
        resume_json=to_pretty_json(resume_struct),
        resume_text=resume_text,
    )
    return cached_complete(RESUME_REWRITE_SYSTEM, user).strip()
