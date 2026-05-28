"""Tailor a DOCX resume by rewriting paragraphs in place — preserves original design."""
from __future__ import annotations

import json
from typing import Any

from ..analysis.extractor import to_pretty_json
from ..exporters.template_exporter import (
    apply_rewrites,
    collect_rewritable_paragraphs,
)
from ..prompts.resume_template import (
    RESUME_TEMPLATE_REWRITE_SYSTEM,
    RESUME_TEMPLATE_REWRITE_USER,
)
from ..utils.cache import cached_complete
from ..utils.json_utils import extract_json


def generate_resume_from_template(
    source_docx_bytes: bytes,
    jd_struct: dict[str, Any],
) -> bytes:
    """Return new DOCX bytes with content paragraphs tailored to the JD.

    Falls back to the original bytes if no rewritable paragraphs were detected.
    """
    paragraphs = collect_rewritable_paragraphs(source_docx_bytes)
    if not paragraphs:
        return source_docx_bytes

    user = RESUME_TEMPLATE_REWRITE_USER.format(
        jd_json=to_pretty_json(jd_struct),
        paragraphs_json=json.dumps(paragraphs, indent=2, ensure_ascii=False),
    )
    raw = cached_complete(RESUME_TEMPLATE_REWRITE_SYSTEM, user)
    parsed = extract_json(raw)
    rewrites = parsed.get("rewrites", {}) or {}

    # Coerce to {int: str}, drop anything malformed.
    coerced: dict[int, str] = {}
    for k, v in rewrites.items():
        try:
            idx = int(k)
        except (TypeError, ValueError):
            continue
        if isinstance(v, str) and v.strip():
            # Collapse any accidental newlines — one paragraph per value.
            coerced[idx] = " ".join(v.split())

    return apply_rewrites(source_docx_bytes, coerced)
