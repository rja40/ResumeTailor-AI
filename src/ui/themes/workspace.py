"""Workspace theme — Cursor/IDE-inspired two-column layout.

Left column: inputs (job + resume + run button).
Right column: live preview (placeholder until the pipeline runs, then results).
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
          @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

          html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
          }
          .stApp { background: #0b0d10 !important; color: #e6e8eb !important; }
          .main .block-container {
            max-width: 1500px;
            padding: 1.2rem 2rem 4rem;
          }
          #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
          [data-testid="stToolbar"] { display: none !important; }

          /* Top bar */
          .ws-topbar {
            display: flex; align-items: center; justify-content: space-between;
            padding: 6px 0 18px;
            border-bottom: 1px solid #1f2228;
            margin-bottom: 22px;
          }
          .ws-brand {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.96rem; font-weight: 700; color: #e6e8eb;
            letter-spacing: -0.01em;
          }
          .ws-brand-mark { color: #38bdf8; margin-right: 8px; }
          .ws-brand-sub {
            font-family: 'Inter', sans-serif;
            color: #6b7280; margin-left: 12px; font-weight: 400;
            font-size: 0.86rem;
          }

          h1, h2, h3 {
            font-family: 'Inter', sans-serif !important;
            color: #f1f5f9 !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em;
          }

          /* Pane labels */
          .ws-pane-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem; font-weight: 600;
            color: #6b7280; letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 12px;
            display: flex; align-items: center; gap: 8px;
          }
          .ws-pane-label .ws-dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: #38bdf8; display: inline-block;
          }

          /* Card */
          .ws-card {
            background: #11141a;
            border: 1px solid #1f2228;
            border-radius: 12px;
            padding: 18px 18px 14px;
            margin-bottom: 14px;
          }
          .ws-card-title {
            font-size: 0.88rem; font-weight: 600; color: #e6e8eb;
            margin-bottom: 10px;
          }

          /* Inputs */
          input, textarea, .stTextInput input, .stTextArea textarea {
            background: #0b0d10 !important;
            border: 1px solid #1f2228 !important;
            color: #e6e8eb !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.9rem !important;
            border-radius: 8px !important;
          }
          .stTextInput input::placeholder,
          .stTextArea textarea::placeholder { color: #4b5563 !important; }
          .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15) !important;
            outline: none !important;
          }
          .stTextInput label, .stTextArea label, .stFileUploader label {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.78rem !important;
            color: #9ca3af !important; font-weight: 500 !important;
          }

          [data-testid="stFileUploader"] section {
            background: #0b0d10 !important;
            border: 1px dashed #2d323b !important;
            border-radius: 8px; color: #9ca3af !important;
          }
          [data-testid="stFileUploader"] button {
            background: #1a1d23 !important; border: 1px solid #2d323b !important;
            color: #e6e8eb !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.84rem !important; border-radius: 6px !important;
          }

          /* Buttons */
          .stButton button, .stDownloadButton button {
            background: #1a1d23; border: 1px solid #2d323b; color: #e6e8eb;
            font-family: 'Inter', sans-serif;
            font-size: 0.86rem; font-weight: 500;
            border-radius: 8px; padding: 0.55rem 1.1rem;
            transition: all 0.12s ease;
          }
          .stButton button:hover, .stDownloadButton button:hover {
            border-color: #38bdf8; color: #38bdf8;
          }
          .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
            background: #38bdf8 !important; color: #0b0d10 !important;
            border-color: #38bdf8 !important; font-weight: 600 !important;
          }
          .stButton button[kind="primary"]:hover,
          .stDownloadButton button[kind="primary"]:hover {
            background: #0ea5e9 !important; color: #0b0d10 !important;
          }

          /* Tabs */
          .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            border-bottom: 1px solid #1f2228;
            gap: 0; margin-top: 8px;
          }
          .stTabs [data-baseweb="tab"] {
            background: transparent !important; color: #6b7280 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.86rem !important; font-weight: 500 !important;
            padding: 9px 16px !important;
            border-radius: 0 !important;
            border-bottom: 2px solid transparent !important;
          }
          .stTabs [aria-selected="true"] {
            color: #e6e8eb !important; border-bottom-color: #38bdf8 !important;
          }

          /* Markdown */
          .stMarkdown p, .stMarkdown li { color: #d1d5db; font-size: 0.92rem; line-height: 1.55; }
          .stMarkdown h1 { font-size: 1.3rem !important; }
          .stMarkdown h2 { font-size: 1.02rem !important; margin-top: 1.2rem !important; }
          .stMarkdown h3 { font-size: 0.9rem !important; color: #7dd3fc !important; }
          .stMarkdown code {
            background: #0b0d10 !important; color: #7dd3fc !important;
            padding: 1px 6px; border-radius: 4px;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.86em !important;
          }

          [data-testid="stMetric"] {
            background: #11141a; border: 1px solid #1f2228;
            border-radius: 10px; padding: 14px 16px;
          }
          [data-testid="stMetricLabel"],
          [data-testid="stMetricLabel"] > div,
          [data-testid="stMetricLabel"] p {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.72rem !important; color: #9ca3af !important;
            font-weight: 500 !important; text-transform: uppercase;
            letter-spacing: 0.08em;
            white-space: normal !important; overflow: visible !important;
            text-overflow: clip !important;
          }
          [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 1.7rem !important; color: #f1f5f9 !important;
            font-weight: 600 !important;
          }

          [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #0ea5e9 0%, #38bdf8 100%) !important;
          }

          [data-testid="stAlert"] {
            background: #11141a !important; border: 1px solid #1f2228 !important;
            border-radius: 8px !important; color: #e6e8eb !important;
          }

          hr { border-color: #1f2228 !important; margin: 16px 0 !important; }

          /* Right pane placeholder */
          .ws-placeholder {
            border: 1px dashed #2d323b;
            border-radius: 12px;
            padding: 60px 28px;
            text-align: center;
            color: #4b5563;
            background: #0b0d10;
            min-height: 460px;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
          }
          .ws-placeholder-glyph {
            font-size: 2.4rem; margin-bottom: 14px;
            color: #38bdf8; opacity: 0.4;
          }
          .ws-placeholder-msg {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.86rem; color: #6b7280;
            max-width: 360px; line-height: 1.55;
          }

          /* shared widget classes */
          .pill {
            display: inline-block; padding: 3px 10px;
            font-family: 'Inter', sans-serif;
            font-size: 0.78rem; font-weight: 500;
            border-radius: 999px; margin-right: 4px; margin-bottom: 4px;
            background: #1a1d23; color: #9ca3af;
          }
          .pill.ok    { background: rgba(34, 197, 94, 0.14); color: #4ade80; }
          .pill.warn  { background: rgba(245, 158, 11, 0.14); color: #fbbf24; }
          .pill.bad   { background: rgba(239, 68, 68, 0.14); color: #f87171; }
          .pill.accent{ background: rgba(56, 189, 248, 0.14); color: #7dd3fc; }

          .rationale-text {
            font-family: 'Inter', sans-serif;
            font-size: 0.84rem; line-height: 1.55;
            color: #9ca3af; margin-top: 10px;
          }
          .native-banner {
            padding: 12px 14px; background: #0b1620;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 8px; color: #7dd3fc;
            margin: 12px 0; font-size: 0.88rem;
          }
          .download-hint {
            font-size: 0.82rem; color: #6b7280; margin: 12px 0 6px;
          }
          .cover-letter-body {
            white-space: pre-wrap; font-family: Georgia, serif;
            line-height: 1.7; padding: 18px 22px;
            background: #11141a; border: 1px solid #1f2228;
            border-radius: 10px; color: #d1d5db; font-size: 0.96rem;
          }
          .match-summary {
            font-size: 0.94rem; line-height: 1.6;
            color: #d1d5db; margin: 14px 0 22px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _pane_label(text: str) -> None:
    st.markdown(
        f'<div class="ws-pane-label"><span class="ws-dot"></span>{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def render() -> None:
    st.set_page_config(
        page_title="ResumeTailor",
        page_icon="◐",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    api_ready = bool(settings.active_api_key)

    # Top bar
    st.markdown(
        f"""
        <div class="ws-topbar">
          <div>
            <span class="ws-brand"><span class="ws-brand-mark">◐</span>ResumeTailor</span>
            <span class="ws-brand-sub">Tailor your resume to every job — truthfully, intelligently, instantly.</span>
          </div>
          <div style="font-family: 'JetBrains Mono', monospace; font-size:0.78rem; color:#6b7280;">
            {'<span style="color:#4ade80;">● ready</span>' if api_ready else '<span style="color:#f87171;">● no api key</span>'}
            · {escape(settings.active_model)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1.15], gap="large")

    # ── LEFT: inputs ──────────────────────────────────────────────────────────
    with left:
        _pane_label("Inputs")

        st.markdown('<div class="ws-card"><div class="ws-card-title">Job description</div>',
                    unsafe_allow_html=True)
        url_fetch_row(fetch_label="Fetch")
        st.text_area(
            "JD",
            height=170,
            placeholder="Or paste the JD text…",
            key="jd_text_area",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="ws-card"><div class="ws-card-title">Master resume</div>',
                    unsafe_allow_html=True)
        resume_file = st.file_uploader(
            "Resume",
            type=["pdf", "docx", "txt", "md"],
            label_visibility="collapsed",
        )
        resume_text_input = st.text_area(
            "Resume text",
            height=140,
            placeholder="Or paste resume text…",
            label_visibility="collapsed",
        )
        if resume_file is not None:
            st.caption(f"✓ {resume_file.name} · {len(resume_file.getvalue()):,} bytes")
        st.markdown("</div>", unsafe_allow_html=True)

        run = st.button("✨  Tailor my resume", type="primary", use_container_width=True)

    # ── RIGHT: preview ────────────────────────────────────────────────────────
    with right:
        _pane_label("Preview")

        if run:
            jd_text = st.session_state.get("jd_text_area", "").strip()
            resume_text, source_docx_bytes = resolve_resume_inputs(resume_file, resume_text_input)
            if not jd_text:
                st.error("Missing job description")
            elif not resume_text:
                st.error("Missing resume")
            elif not api_ready:
                st.error(f"No API key for `{settings.provider}`")
            else:
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

        result: dict[str, Any] | None = st.session_state.get("result")
        if not result:
            st.markdown(
                '<div class="ws-placeholder">'
                '<div class="ws-placeholder-glyph">◐</div>'
                '<div class="ws-placeholder-msg">'
                'Add a job description and your master resume on the left, then press '
                '<b style="color:#7dd3fc;">Tailor my resume</b>. Results appear here.'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            return

        match = result["match"]
        overall = int(match.get("overall_score", 0))
        role = result["jd_struct"].get("role_title", "—")
        company = result["jd_struct"].get("company", "—")

        m1, m2 = st.columns([1, 2])
        m1.metric("Match", f"{overall}/100")
        m2.markdown(
            f"<div style='padding-top: 12px;'>"
            f"<div style='font-size:0.74rem; color:#6b7280; text-transform:uppercase; "
            f"letter-spacing:0.1em; margin-bottom:4px;'>Role</div>"
            f"<div style='color:#e6e8eb; font-size:0.96rem;'>{escape(role)} · "
            f"<span style='color:#7dd3fc;'>{escape(company)}</span></div></div>",
            unsafe_allow_html=True,
        )

        render_result_tabs(result)
