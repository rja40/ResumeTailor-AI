"""Wizard theme — 3-step guided flow with a progress bar.

Step 1: Job. Step 2: Resume. Step 3: Results.
State held in `st.session_state["wizard_step"]`.
"""
from __future__ import annotations

import time
import traceback
from html import escape
from typing import Any

import streamlit as st

from src.config import settings
from src.ui.pipeline import run_pipeline
from src.ui.widgets import render_result_tabs, url_fetch_row


STEPS = ("Job", "Resume", "Tailor")


def _inject_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

          html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
          }
          .stApp { background: #f5f7fa !important; color: #1f2937 !important; }
          .main .block-container {
            max-width: 760px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
          }
          #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
          [data-testid="stToolbar"] { display: none !important; }

          h1, h2, h3 { color: #111827 !important; font-weight: 600 !important; }

          /* Brand */
          .wz-brand {
            text-align: center;
            font-size: 0.82rem; color: #6b7280;
            font-weight: 600; letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 14px;
          }
          .wz-brand-mark { color: #4f46e5; }

          /* Progress strip */
          .wz-progress {
            display: flex; align-items: center; justify-content: center;
            gap: 6px; margin: 8px 0 36px;
          }
          .wz-step {
            display: flex; flex-direction: column; align-items: center;
            min-width: 130px;
          }
          .wz-step-circle {
            width: 32px; height: 32px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-weight: 600; font-size: 0.86rem;
            background: #e5e7eb; color: #6b7280;
            border: 2px solid transparent;
            margin-bottom: 8px;
          }
          .wz-step.active .wz-step-circle {
            background: #4f46e5; color: #fff;
            box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15);
          }
          .wz-step.done .wz-step-circle {
            background: #10b981; color: #fff;
          }
          .wz-step-label {
            font-size: 0.84rem; color: #6b7280; font-weight: 500;
          }
          .wz-step.active .wz-step-label { color: #111827; font-weight: 600; }
          .wz-connector {
            flex: 0 0 60px; height: 2px;
            background: #e5e7eb; align-self: flex-start;
            margin-top: 24px;
          }
          .wz-connector.done { background: #10b981; }

          /* Step card */
          .wz-step-title {
            font-size: 1.7rem; font-weight: 600;
            color: #111827; margin-bottom: 6px;
            letter-spacing: -0.02em;
          }
          .wz-step-desc {
            color: #6b7280; font-size: 1rem;
            margin-bottom: 28px;
            line-height: 1.55;
          }

          /* Inputs */
          input, textarea, .stTextInput input, .stTextArea textarea {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            color: #111827 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.96rem !important;
            border-radius: 10px !important;
            line-height: 1.5;
          }
          .stTextInput input::placeholder,
          .stTextArea textarea::placeholder { color: #9ca3af !important; }
          .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #4f46e5 !important;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.13) !important;
            outline: none !important;
          }
          .stTextInput label, .stTextArea label, .stFileUploader label {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.86rem !important;
            color: #4b5563 !important; font-weight: 500 !important;
          }

          [data-testid="stFileUploader"] section {
            background: #fafafa !important;
            border: 2px dashed #d1d5db !important;
            border-radius: 12px;
            color: #6b7280 !important;
            padding: 32px 20px !important;
          }
          [data-testid="stFileUploader"] button {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            color: #111827 !important;
            font-size: 0.9rem !important; border-radius: 8px !important;
          }

          /* Buttons */
          .stButton button, .stDownloadButton button {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            color: #374151;
            font-family: 'Inter', sans-serif;
            font-size: 0.92rem; font-weight: 500;
            border-radius: 10px;
            padding: 0.65rem 1.4rem;
          }
          .stButton button:hover, .stDownloadButton button:hover {
            border-color: #c7d2fe; background: #f5f3ff; color: #4338ca;
          }
          .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
            background: #4f46e5 !important; color: #fff !important;
            border-color: #4f46e5 !important; font-weight: 600 !important;
            padding: 0.75rem 1.7rem !important;
          }
          .stButton button[kind="primary"]:hover,
          .stDownloadButton button[kind="primary"]:hover {
            background: #4338ca !important;
          }

          /* Tabs */
          .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            border-bottom: 1px solid #e5e7eb;
            gap: 4px; margin-top: 12px;
          }
          .stTabs [data-baseweb="tab"] {
            background: transparent !important; color: #6b7280 !important;
            font-size: 0.94rem !important; font-weight: 500 !important;
            padding: 10px 18px !important;
            border-radius: 8px 8px 0 0 !important;
            border-bottom: 2px solid transparent !important;
          }
          .stTabs [aria-selected="true"] {
            color: #111827 !important; border-bottom-color: #4f46e5 !important;
          }

          .stMarkdown p, .stMarkdown li { color: #1f2937; font-size: 1rem; line-height: 1.65; }
          .stMarkdown h1 { font-size: 1.5rem !important; }
          .stMarkdown h2 { font-size: 1.18rem !important; margin-top: 1.4rem !important; }
          .stMarkdown h3 { font-size: 1rem !important; color: #374151 !important; }

          [data-testid="stMetric"] {
            background: #ffffff; border: 1px solid #e5e7eb;
            border-radius: 12px; padding: 18px 20px;
          }
          [data-testid="stMetricLabel"],
          [data-testid="stMetricLabel"] > div,
          [data-testid="stMetricLabel"] p {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.78rem !important; color: #6b7280 !important;
            font-weight: 500 !important;
            white-space: normal !important; overflow: visible !important;
            text-overflow: clip !important;
          }
          [data-testid="stMetricValue"] {
            font-size: 1.9rem !important; color: #111827 !important;
            font-weight: 600 !important;
          }

          [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #4f46e5 0%, #818cf8 100%) !important;
          }

          hr { border-color: #e5e7eb !important; margin: 18px 0 !important; }

          /* shared classes */
          .pill {
            display: inline-block; padding: 3px 10px;
            font-size: 0.78rem; font-weight: 500;
            border-radius: 999px; margin-right: 4px; margin-bottom: 4px;
            background: #f3f4f6; color: #4b5563;
          }
          .pill.ok    { background: #ecfdf5; color: #047857; }
          .pill.warn  { background: #fffbeb; color: #b45309; }
          .pill.bad   { background: #fef2f2; color: #b91c1c; }

          .rationale-text {
            font-size: 0.88rem; line-height: 1.55;
            color: #6b7280; margin-top: 10px;
          }
          .native-banner {
            padding: 14px 18px; background: #f5f3ff;
            border: 1px solid #ddd6fe; border-radius: 10px;
            color: #4338ca; margin: 12px 0; font-size: 0.94rem;
          }
          .download-hint {
            font-size: 0.86rem; color: #6b7280; margin: 14px 0 8px;
          }
          .cover-letter-body {
            white-space: pre-wrap; font-family: Georgia, serif;
            line-height: 1.75; padding: 24px 28px;
            background: #ffffff; border: 1px solid #e5e7eb;
            border-radius: 12px; color: #1f2937; font-size: 1rem;
          }
          .match-summary {
            font-size: 1rem; line-height: 1.6;
            color: #374151; margin: 14px 0 22px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_progress(current: int) -> None:
    parts: list[str] = []
    for i, label in enumerate(STEPS):
        cls = ""
        if i < current:
            cls = " done"
        elif i == current:
            cls = " active"
        icon = "✓" if i < current else str(i + 1)
        parts.append(
            f'<div class="wz-step{cls}">'
            f'<div class="wz-step-circle">{icon}</div>'
            f'<div class="wz-step-label">{label}</div>'
            f'</div>'
        )
        if i < len(STEPS) - 1:
            conn_cls = " done" if i < current else ""
            parts.append(f'<div class="wz-connector{conn_cls}"></div>')
    st.markdown(
        '<div class="wz-progress">' + "".join(parts) + "</div>",
        unsafe_allow_html=True,
    )


def _step_header(title: str, desc: str) -> None:
    st.markdown(
        f'<div class="wz-step-title">{escape(title)}</div>'
        f'<div class="wz-step-desc">{escape(desc)}</div>',
        unsafe_allow_html=True,
    )


def render() -> None:
    st.set_page_config(
        page_title="ResumeTailor",
        page_icon="✨",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 0

    step = st.session_state["wizard_step"]

    st.markdown(
        '<div class="wz-brand"><span class="wz-brand-mark">✦</span>  ResumeTailor</div>',
        unsafe_allow_html=True,
    )
    _render_progress(step)

    api_ready = bool(settings.active_api_key)

    # ── Step 1: Job ───────────────────────────────────────────────────────────
    if step == 0:
        _step_header(
            "Where are you applying?",
            "Paste a job posting URL — or the JD text directly. "
            "We'll tailor your resume to match this exact role.",
        )
        url_fetch_row(fetch_label="Fetch")
        st.text_area(
            "JD",
            height=240,
            placeholder="Or paste the full job description here…",
            key="jd_text_area",
            label_visibility="collapsed",
        )
        st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1])
        # No back button on step 1 — but reserve the column for layout
        col_a.write("")
        if col_b.button("Continue  →", type="primary", use_container_width=True):
            if not st.session_state.get("jd_text_area", "").strip():
                st.error("Please paste a URL or JD text before continuing.")
            else:
                st.session_state["wizard_step"] = 1
                st.rerun()

    # ── Step 2: Resume ────────────────────────────────────────────────────────
    elif step == 1:
        _step_header(
            "Your master resume",
            "Upload your resume — we'll only use facts that are actually in this document. "
            "PDF, DOCX, or plain text.",
        )
        resume_file = st.file_uploader(
            "Resume",
            type=["pdf", "docx", "txt", "md"],
            label_visibility="collapsed",
        )
        st.text_area(
            "Or paste resume text",
            height=180,
            placeholder="…or paste your master resume here.",
            key="resume_text_area",
        )
        if resume_file is not None:
            st.success(f"✓ Loaded {resume_file.name} ({len(resume_file.getvalue()):,} bytes)")
            # Stash bytes in session_state so they survive the step transition.
            st.session_state["resume_file_bytes"] = resume_file.getvalue()
            st.session_state["resume_file_name"] = resume_file.name

        st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1])
        if col_a.button("←  Back", use_container_width=True):
            st.session_state["wizard_step"] = 0
            st.rerun()
        if col_b.button("Continue  →", type="primary", use_container_width=True):
            has_file = "resume_file_bytes" in st.session_state
            has_text = bool(st.session_state.get("resume_text_area", "").strip())
            if not (has_file or has_text):
                st.error("Please upload or paste a resume before continuing.")
            elif not api_ready:
                st.error(f"No API key for `{settings.provider}`. Set it in `.env` and restart.")
            else:
                st.session_state["wizard_step"] = 2
                st.session_state.pop("result", None)
                st.rerun()

    # ── Step 3: Tailor + results ──────────────────────────────────────────────
    else:
        result: dict[str, Any] | None = st.session_state.get("result")

        if not result:
            _step_header("Tailoring your application…",
                         "Drafting your resume, cover letter, gap analysis, and match score.")
            jd_text = st.session_state.get("jd_text_area", "").strip()

            # Reconstruct a file-like object if we stored bytes
            from src.parsers import parse_uploaded_file, clean_text
            from src.generators import generate_resume_from_template  # noqa: F401  (cached path used)

            resume_text = ""
            source_docx_bytes = None
            if "resume_file_bytes" in st.session_state:
                fname = st.session_state["resume_file_name"]
                raw = st.session_state["resume_file_bytes"]
                resume_text = parse_uploaded_file(fname, raw)
                if fname.lower().endswith(".docx"):
                    source_docx_bytes = raw
            else:
                resume_text = clean_text(st.session_state.get("resume_text_area", ""))

            start = time.monotonic()
            try:
                with st.status("Tailoring… (0s)", expanded=True) as status:
                    def on_stage(label: str) -> None:
                        elapsed = int(time.monotonic() - start)
                        status.update(label=f"{label}… ({elapsed}s elapsed)")
                        st.write(f"▸ {label}")

                    try:
                        result = run_pipeline(
                            jd_text, resume_text, source_docx_bytes,
                            on_stage=on_stage,
                        )
                    except Exception as e:
                        total = int(time.monotonic() - start)
                        status.update(label=f"Failed after {total}s — {e}", state="error", expanded=True)
                        raise

                    total = int(time.monotonic() - start)
                    status.update(label=f"✓ Tailored in {total}s", state="complete", expanded=False)
                st.session_state["result"] = result
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Tailoring failed: {e}")
                with st.expander("Details"):
                    st.code(traceback.format_exc())
                if st.button("←  Back"):
                    st.session_state["wizard_step"] = 1
                    st.rerun()
                return

        # Result is ready
        match = result["match"]
        overall = int(match.get("overall_score", 0))
        role = result["jd_struct"].get("role_title", "—")
        company = result["jd_struct"].get("company", "—")

        _step_header(
            "Your tailored application",
            f"Match score {overall}/100 for {role} at {company}. "
            "Review each tab and download whichever format you prefer.",
        )

        m1, m2 = st.columns([1, 2])
        m1.metric("Match", f"{overall}/100")
        m2.markdown(
            f"<div style='padding-top: 10px;'>"
            f"<div style='font-size:0.8rem; color:#6b7280; margin-bottom:4px;'>Verdict</div>"
            f"<div style='color:#111827; font-size:1.1rem; font-weight:500;'>"
            f"{escape((match.get('verdict') or '—').title())}</div></div>",
            unsafe_allow_html=True,
        )

        render_result_tabs(result)

        st.markdown("<div style='margin: 28px 0 10px;'></div>", unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1])
        if col_a.button("←  Edit resume", use_container_width=True):
            st.session_state["wizard_step"] = 1
            st.session_state.pop("result", None)
            st.rerun()
        if col_b.button("New job  ↻", use_container_width=True):
            st.session_state["wizard_step"] = 0
            st.session_state.pop("result", None)
            st.rerun()
