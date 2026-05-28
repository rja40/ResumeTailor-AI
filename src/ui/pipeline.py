"""Shared pipeline + input helpers used by every theme.

`run_pipeline` invokes an optional `on_stage(label)` callback before each LLM
stage so the UI can show progress + elapsed time. No `@st.cache_data` —
the LLM-level lru_cache (`src/utils/cache.py`) already dedupes identical
sub-calls, and `st.session_state['result']` prevents reruns from re-executing
the pipeline.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from src.analysis import compute_match, extract_jd, extract_resume
from src.generators import (
    generate_cover_letter,
    generate_gap_analysis,
    generate_resume,
    generate_resume_from_template,
)
from src.parsers import clean_text, parse_uploaded_file


StageCallback = Callable[[str], None]


def resolve_resume_inputs(resume_file, paste_text: str) -> tuple[str, bytes | None]:
    """Return (text, optional source DOCX bytes for in-place template export)."""
    if resume_file is not None:
        raw = resume_file.getvalue()
        text = parse_uploaded_file(resume_file.name, raw)
        source = raw if resume_file.name.lower().endswith(".docx") else None
        return text, source
    return clean_text(paste_text or ""), None


def run_pipeline(
    jd_text: str,
    resume_text: str,
    source_docx_bytes: bytes | None,
    *,
    on_stage: Optional[StageCallback] = None,
) -> dict[str, Any]:
    """Run the full tailoring pipeline.

    When `on_stage` is provided, it's called with a human-readable label
    immediately before each LLM stage starts.
    """

    def _tick(label: str) -> None:
        if on_stage is not None:
            on_stage(label)

    _tick("Parsing job description")
    jd_struct = extract_jd(jd_text)

    _tick("Parsing master resume")
    resume_struct = extract_resume(resume_text)

    _tick("Computing match score")
    match = compute_match(jd_struct, resume_struct, resume_text)

    _tick("Rewriting resume bullets")
    tailored_resume_md = generate_resume(jd_struct, resume_struct, resume_text)

    _tick("Drafting cover letter")
    cover_letter = generate_cover_letter(jd_struct, resume_struct, resume_text)

    _tick("Analyzing gaps & interview prep")
    gap = generate_gap_analysis(jd_struct, resume_struct)

    native = None
    if source_docx_bytes:
        _tick("Preserving original DOCX formatting")
        native = generate_resume_from_template(source_docx_bytes, jd_struct)

    return {
        "jd_struct": jd_struct,
        "resume_struct": resume_struct,
        "match": match,
        "tailored_resume_md": tailored_resume_md,
        "cover_letter": cover_letter,
        "gap": gap,
        "native_docx_bytes": native,
    }
