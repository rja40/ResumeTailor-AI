"""Minimal theme — Linear/Notion aesthetic.

White background, soft serif headings, generous whitespace, single column,
card-based input sections with subtle borders.
"""
from __future__ import annotations

import time
import traceback
from html import escape
from typing import Any

import streamlit as st

from src.config import settings
from src.ui.pipeline import resolve_resume_inputs, run_pipeline
from src.ui.widgets import render_result_tabs, url_fetch_row


def _inject_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

          html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
          }
          .stApp {
            background: #fafaf9 !important;
            color: #1f2937 !important;
          }
          .main .block-container {
            max-width: 760px;
            padding-top: 3rem;
            padding-bottom: 4rem;
          }
          #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
          [data-testid="stToolbar"] { display: none !important; }

          h1, h2, h3 {
            font-family: 'Fraunces', Georgia, serif !important;
            color: #111827 !important;
            font-weight: 500 !important;
            letter-spacing: -0.015em;
          }

          /* Hero */
          .mn-hero {
            margin-bottom: 56px;
            padding-bottom: 28px;
            border-bottom: 1px solid #e5e7eb;
          }
          .mn-hero-eyebrow {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem; font-weight: 600;
            color: #6366f1; text-transform: uppercase;
            letter-spacing: 0.18em;
            margin-bottom: 12px;
          }
          .mn-hero-title {
            font-family: 'Fraunces', Georgia, serif;
            font-size: 3rem; font-weight: 500;
            color: #0f172a;
            letter-spacing: -0.03em;
            line-height: 1.05;
            margin-bottom: 14px;
          }
          .mn-hero-tagline {
            font-size: 1.08rem;
            line-height: 1.6;
            color: #4b5563;
            max-width: 580px;
          }

          /* Card sections */
          .mn-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 28px 28px 22px;
            margin-bottom: 22px;
            box-shadow: 0 1px 0 rgba(0,0,0,0.02);
          }
          .mn-card-num {
            display: inline-flex;
            align-items: center; justify-content: center;
            width: 26px; height: 26px;
            border-radius: 999px;
            background: #f1f5f9;
            color: #4f46e5;
            font-family: 'Inter', sans-serif;
            font-size: 0.78rem; font-weight: 700;
            margin-right: 10px;
          }
          .mn-card-title {
            font-family: 'Fraunces', Georgia, serif;
            font-size: 1.25rem;
            font-weight: 500;
            color: #111827;
            display: inline-block;
            vertical-align: middle;
          }
          .mn-card-hint {
            color: #6b7280; font-size: 0.88rem;
            margin: 6px 0 16px 36px;
          }

          /* Inputs */
          input, textarea, .stTextInput input, .stTextArea textarea {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            color: #111827 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.94rem !important;
            border-radius: 10px !important;
            line-height: 1.5;
          }
          .stTextInput input::placeholder,
          .stTextArea textarea::placeholder { color: #9ca3af !important; }
          .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
            outline: none !important;
          }
          .stTextInput label, .stTextArea label, .stFileUploader label {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.82rem !important;
            color: #6b7280 !important;
            font-weight: 500 !important;
          }

          [data-testid="stFileUploader"] section {
            background: #fafaf9 !important;
            border: 1px dashed #d1d5db !important;
            border-radius: 12px;
            color: #6b7280 !important;
          }
          [data-testid="stFileUploader"] button {
            background: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            color: #111827 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.86rem !important;
            border-radius: 8px !important;
          }

          /* Buttons */
          .stButton button, .stDownloadButton button {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            color: #374151;
            font-family: 'Inter', sans-serif;
            font-size: 0.88rem; font-weight: 500;
            border-radius: 10px;
            padding: 0.55rem 1.1rem;
            transition: all 0.12s ease;
          }
          .stButton button:hover, .stDownloadButton button:hover {
            border-color: #c7d2fe;
            background: #f5f3ff;
            color: #4338ca;
          }
          .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
            background: #4f46e5 !important;
            color: #ffffff !important;
            border-color: #4f46e5 !important;
            font-weight: 600 !important;
            padding: 0.7rem 1.4rem !important;
          }
          .stButton button[kind="primary"]:hover,
          .stDownloadButton button[kind="primary"]:hover {
            background: #4338ca !important;
            color: #ffffff !important;
          }

          /* Tabs */
          .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            border-bottom: 1px solid #e5e7eb;
            gap: 4px; margin-top: 12px;
          }
          .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            color: #6b7280 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.94rem !important;
            font-weight: 500 !important;
            padding: 10px 18px !important;
            border-radius: 8px 8px 0 0 !important;
            border-bottom: 2px solid transparent !important;
          }
          .stTabs [aria-selected="true"] {
            color: #111827 !important;
            border-bottom-color: #6366f1 !important;
          }

          /* Markdown body */
          .stMarkdown p, .stMarkdown li { color: #1f2937; font-size: 1rem; line-height: 1.65; }
          .stMarkdown h1 { font-size: 1.6rem !important; }
          .stMarkdown h2 { font-size: 1.2rem !important; margin-top: 1.6rem !important; }
          .stMarkdown h3 { font-size: 1.02rem !important; color: #374151 !important; }
          .stMarkdown code {
            background: #f3f4f6 !important; color: #4f46e5 !important;
            padding: 2px 6px; border-radius: 4px;
            font-family: ui-monospace, 'SF Mono', monospace !important;
            font-size: 0.88em !important;
          }

          /* Metric cards */
          [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 1px 0 rgba(0,0,0,0.02);
          }
          [data-testid="stMetricLabel"],
          [data-testid="stMetricLabel"] > div,
          [data-testid="stMetricLabel"] p {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.78rem !important; color: #6b7280 !important;
            font-weight: 500 !important; text-transform: none !important;
            letter-spacing: 0 !important;
            white-space: normal !important; overflow: visible !important;
            text-overflow: clip !important;
          }
          [data-testid="stMetricValue"] {
            font-family: 'Fraunces', Georgia, serif !important;
            font-size: 2rem !important; color: #111827 !important;
            font-weight: 500 !important;
          }

          [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%) !important;
          }

          [data-testid="stAlert"] {
            background: #f9fafb !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 10px !important; color: #374151 !important;
          }

          hr { border-color: #e5e7eb !important; margin: 20px 0 !important; }

          /* widget-shared classes */
          .pill {
            display: inline-block; padding: 3px 10px;
            font-size: 0.78rem; font-weight: 500;
            border-radius: 999px; margin-right: 4px; margin-bottom: 4px;
            background: #f3f4f6; color: #4b5563;
          }
          .pill.ok    { background: #ecfdf5; color: #047857; }
          .pill.warn  { background: #fffbeb; color: #b45309; }
          .pill.bad   { background: #fef2f2; color: #b91c1c; }
          .pill.accent{ background: #eef2ff; color: #4338ca; }

          .rationale-text {
            font-family: 'Inter', sans-serif;
            font-size: 0.86rem; line-height: 1.55;
            color: #6b7280; margin-top: 10px;
          }
          .native-banner {
            padding: 14px 18px; background: #f5f3ff;
            border: 1px solid #ddd6fe; border-radius: 10px;
            color: #4338ca; margin: 12px 0; font-size: 0.94rem;
          }
          .download-hint {
            font-size: 0.84rem; color: #9ca3af;
            margin: 14px 0 8px;
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


def _card_open(num: int, title: str, hint: str = "") -> None:
    st.markdown(
        f'<div class="mn-card">'
        f'<div><span class="mn-card-num">{num}</span>'
        f'<span class="mn-card-title">{escape(title)}</span></div>'
        + (f'<div class="mn-card-hint">{escape(hint)}</div>' if hint else ""),
        unsafe_allow_html=True,
    )


def _card_close() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render() -> None:
    st.set_page_config(
        page_title="ResumeTailor",
        page_icon="✒️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    # Hero
    st.markdown(
        """
        <div class="mn-hero">
          <div class="mn-hero-eyebrow">ResumeTailor</div>
          <div class="mn-hero-title">Tailor your resume<br/>to every job.</div>
          <div class="mn-hero-tagline">
            Truthfully, intelligently, instantly.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    api_ready = bool(settings.active_api_key)
    if not api_ready:
        st.error(f"Missing API key for `{settings.provider}`. Set it in `.env` and restart.")

    # — Card 1: Job —
    _card_open(1, "Job description", "Paste a URL — or the JD text directly.")
    url_fetch_row(fetch_label="Fetch")
    st.text_area(
        "JD",
        height=200,
        placeholder="Or paste the full job description here…",
        key="jd_text_area",
        label_visibility="collapsed",
    )
    _card_close()

    # — Card 2: Resume —
    _card_open(2, "Master resume", "Upload your resume — PDF, DOCX, or text.")
    resume_file = st.file_uploader(
        "Resume file",
        type=["pdf", "docx", "txt", "md"],
        label_visibility="collapsed",
    )
    resume_text_input = st.text_area(
        "Resume text",
        height=160,
        placeholder="Or paste your resume text…",
        label_visibility="collapsed",
    )
    if resume_file is not None:
        st.caption(f"✓ Loaded {resume_file.name} ({len(resume_file.getvalue()):,} bytes)")
    _card_close()

    st.markdown("<div style='margin: 8px 0 24px;'></div>", unsafe_allow_html=True)
    run = st.button("✨  Tailor my resume", type="primary", use_container_width=True)

    if run:
        jd_text = st.session_state.get("jd_text_area", "").strip()
        resume_text, source_docx_bytes = resolve_resume_inputs(resume_file, resume_text_input)
        if not jd_text:
            st.error("Missing job description"); st.stop()
        if not resume_text:
            st.error("Missing resume"); st.stop()
        if not api_ready:
            st.stop()

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
        except Exception as e:  # noqa: BLE001
            st.error(f"Tailoring failed: {e}")
            with st.expander("Details"):
                st.code(traceback.format_exc())
            st.stop()

    result: dict[str, Any] | None = st.session_state.get("result")
    if not result:
        return

    match = result["match"]
    overall = int(match.get("overall_score", 0))
    role = result["jd_struct"].get("role_title", "—")
    company = result["jd_struct"].get("company", "—")

    st.markdown("<hr style='margin: 36px 0;'/>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns([1, 1, 2])
    m1.metric("Match", f"{overall}")
    m2.metric("Verdict", (match.get("verdict") or "—").title())
    m3.markdown(
        f"<div style='padding-top: 10px;'>"
        f"<div style='font-size:0.78rem; color:#6b7280; margin-bottom:4px;'>Role</div>"
        f"<div style='color:#111827; font-size:1rem;'>"
        f"{escape(role)} · <span style='color:#6366f1;'>{escape(company)}</span></div></div>",
        unsafe_allow_html=True,
    )

    render_result_tabs(result)
