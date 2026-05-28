"""Shared widgets used across themes — URL fetch row and result-tab renderers.

Each theme injects its own CSS; the Python structure of inputs and result
tabs is identical so styling cascades naturally.
"""
from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from src.exporters import (
    markdown_to_docx_bytes,
    markdown_to_pdf_bytes,
    text_to_docx_bytes,
    text_to_pdf_bytes,
)
from src.parsers import (
    BotCheckError,
    EmptyJDError,
    JDFetchError,
    LoginWallError,
    MalformedURLError,
    NetworkError,
    fetch_jd_from_url,
)


# ──────────────────────────────────────────────────────────────────────────────
#  URL fetch row — populates session_state["jd_text_area"]
# ──────────────────────────────────────────────────────────────────────────────


def url_fetch_row(
    *,
    placeholder: str = "https://wrapbook.com/careers?ashby_jid=...",
    fetch_label: str = "Fetch",
    url_label: str = "URL",
    show_url_label: bool = False,
) -> None:
    """Render the URL input + Fetch button. On click, populates the JD textarea."""
    url_col, btn_col = st.columns([3, 1])
    jd_url = url_col.text_input(
        url_label,
        key="jd_url_input",
        placeholder=placeholder,
        label_visibility="visible" if show_url_label else "collapsed",
    )
    btn_col.write("")
    if btn_col.button(fetch_label, use_container_width=True, key="fetch_jd_btn"):
        if not jd_url.strip():
            st.warning("Enter a URL first.")
        else:
            with st.spinner("Fetching job description…"):
                try:
                    fetched = fetch_jd_from_url(jd_url.strip())
                    st.session_state["jd_text_area"] = fetched
                    st.success(f"Fetched · {len(fetched):,} characters")
                except MalformedURLError:
                    st.error("Invalid URL — needs http:// or https://")
                except BotCheckError:
                    st.error(
                        "Blocked by bot-check (common on Indeed/Glassdoor). "
                        "Paste the JD manually below."
                    )
                except LoginWallError:
                    st.error("Page requires login. Paste the JD manually below.")
                except NetworkError as e:
                    st.error(f"Couldn't reach that URL: {e}")
                except EmptyJDError:
                    st.error("Couldn't find a job description on that page.")
                except JDFetchError as e:
                    st.error(f"Fetch failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
#  Result tabs renderer — works in any theme
# ──────────────────────────────────────────────────────────────────────────────


def _severity_class(sev: str) -> str:
    sev = (sev or "").lower()
    return {"high": "bad", "medium": "warn", "low": "ok"}.get(sev, "")


def render_result_tabs(
    result: dict[str, Any],
    *,
    tab_labels: tuple[str, str, str, str] = (
        "📄 Resume",
        "✉️ Cover Letter",
        "🧭 Gap Analysis",
        "🎯 Match",
    ),
    pill_class: str = "pill",
    rationale_class: str = "rationale-text",
) -> None:
    """Render the 4-tab result block. Themes supply their own CSS for pills,
    rationale text, etc. — we just emit consistent HTML class names."""
    match = result["match"]
    overall = int(match.get("overall_score", 0))
    verdict = (match.get("verdict") or "—").lower()

    t_resume, t_cover, t_gap, t_match = st.tabs(list(tab_labels))

    # — Resume —
    with t_resume:
        md = result["tailored_resume_md"]
        native = result.get("native_docx_bytes")

        if native:
            st.markdown(
                '<div class="native-banner">'
                '<b>✨ Original format preserved.</b> Your DOCX has been rewritten in '
                'place — fonts, colors, and layout match your source design exactly.'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(md)
        st.markdown("<hr/>", unsafe_allow_html=True)

        if native:
            st.download_button(
                "⬇ Download DOCX (original format)",
                data=native,
                file_name="tailored_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
            )
            st.markdown('<div class="download-hint">Other formats:</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.download_button(
            "⬇ DOCX",
            data=markdown_to_docx_bytes(md),
            file_name="tailored_resume_generic.docx" if native else "tailored_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        c2.download_button(
            "⬇ PDF",
            data=markdown_to_pdf_bytes(md),
            file_name="tailored_resume.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        c3.download_button(
            "⬇ Markdown",
            data=md.encode("utf-8"),
            file_name="tailored_resume.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # — Cover —
    with t_cover:
        letter = result["cover_letter"]
        st.markdown(
            f'<div class="cover-letter-body">{escape(letter)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<hr/>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.download_button(
            "⬇ DOCX", text_to_docx_bytes(letter),
            file_name="cover_letter.docx", use_container_width=True,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        c2.download_button(
            "⬇ PDF", text_to_pdf_bytes(letter),
            file_name="cover_letter.pdf", use_container_width=True,
            mime="application/pdf",
        )
        c3.download_button(
            "⬇ TXT", letter.encode("utf-8"),
            file_name="cover_letter.txt", use_container_width=True,
            mime="text/plain",
        )

    # — Gap —
    with t_gap:
        gap = result["gap"]

        st.markdown("#### Strengths")
        for s in gap.get("strengths", []):
            st.markdown(f"- **{s.get('area', '')}** — {s.get('evidence', '')}")

        st.markdown("#### Gaps")
        for g in gap.get("gaps", []):
            sev_cls = _severity_class(g.get("severity", ""))
            st.markdown(
                f'<span class="{pill_class} {sev_cls}">{escape((g.get("severity") or "").upper())}</span>  '
                f'**{escape(g.get("area", ""))}** — {escape(g.get("why_it_matters", ""))}  \n'
                f'<span class="{rationale_class}">▸ {escape(g.get("how_to_close", ""))}</span>',
                unsafe_allow_html=True,
            )

        st.markdown("#### Learning Plan")
        for item in gap.get("learning_plan", []):
            st.markdown(
                f"**{item.get('priority', '?')}.** {item.get('topic', '')}  "
                f'<span class="{pill_class}">{escape(item.get("time_estimate", "—"))}</span>',
                unsafe_allow_html=True,
            )
            for r in item.get("resources", []):
                st.markdown(f"  - {r}")

        st.markdown("#### Interview Prep")
        prep = gap.get("interview_prep", {}) or {}
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Technical**")
            for q in prep.get("likely_technical_questions", []):
                st.markdown(f"- {q}")
        with col_b:
            st.markdown("**Behavioral**")
            for q in prep.get("likely_behavioral_questions", []):
                st.markdown(f"- {q}")

    # — Match —
    with t_match:
        st.progress(min(max(overall, 0), 100) / 100, text=f"{overall}/100 · {verdict}")
        st.markdown(
            f'<div class="match-summary">{escape(match.get("summary", ""))}</div>',
            unsafe_allow_html=True,
        )

        breakdown = match.get("breakdown", {}) or {}
        cols = st.columns(len(breakdown) or 1)

        def _short_label(k: str) -> str:
            return k.replace("_match", "").replace("_", " ").strip().upper()

        for col, (key, val) in zip(cols, breakdown.items()):
            with col:
                st.metric(_short_label(key), f"{int(val.get('score', 0))}")
                st.markdown(
                    f'<div class="{rationale_class}">{escape(val.get("rationale", ""))}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("#### Matched")
        matched = list(dict.fromkeys((match.get("matched_skills") or []) + (match.get("matched_keywords") or [])))
        if matched:
            pills = "".join(f'<span class="{pill_class} ok">{escape(s)}</span> ' for s in matched)
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.markdown('<div class="rationale-text">No matches detected.</div>', unsafe_allow_html=True)

        st.markdown("#### Missing must-haves")
        missing = match.get("missing_must_have_skills", []) or []
        if missing:
            pills = "".join(f'<span class="{pill_class} bad">{escape(s)}</span> ' for s in missing)
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.success("✓ No must-have gaps")

        with st.expander("Debug · structured JD + resume"):
            st.json(result["jd_struct"])
            st.json(result["resume_struct"])
