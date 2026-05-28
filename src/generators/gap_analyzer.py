"""Generate gap analysis + interview prep plan."""
from __future__ import annotations

from typing import Any

from ..analysis.extractor import to_pretty_json
from ..prompts.gap import GAP_ANALYSIS_SYSTEM, GAP_ANALYSIS_USER
from ..utils.cache import cached_complete
from ..utils.json_utils import extract_json


def generate_gap_analysis(
    jd_struct: dict[str, Any],
    resume_struct: dict[str, Any],
) -> dict[str, Any]:
    user = GAP_ANALYSIS_USER.format(
        jd_json=to_pretty_json(jd_struct),
        resume_json=to_pretty_json(resume_struct),
    )
    raw = cached_complete(GAP_ANALYSIS_SYSTEM, user)
    return extract_json(raw)
