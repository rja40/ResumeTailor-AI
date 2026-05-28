"""Terminal theme — dark Vercel/Geist aesthetic, mono headings, violet accent."""
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
          @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');

          html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
          }
          .stApp { background: #000 !important; color: #ededed !important; }
          .main .block-container { max-width: 880px; padding-top: 1.4rem; padding-bottom: 6rem; }
          #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
          [data-testid="stToolbar"], [data-testid="stSidebar"],
          [data-testid="collapsedControl"] { display: none !important; }

          h1, h2, h3, h4 {
            font-family: 'JetBrains Mono', ui-monospace, 'SF Mono', monospace !important;
            color: #fff !important; letter-spacing: -0.02em; font-weight: 700 !important;
          }
          h1 { font-size: 1.05rem !important; letter-spacing: 0.04em; text-transform: uppercase; }

          .term-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 0 18px; border-bottom: 1px solid #1a1a1a;
          }
          .term-logo {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem; font-weight: 700;
            letter-spacing: 0.18em; color: #fff;
          }
          .term-logo::before { content: "■  "; color: #7c3aed; }

          .term-hero { padding: 38px 0 22px; }
          .term-hero-title {
            font-family: 'JetBrains Mono', monospace; font-size: 2.6rem;
            font-weight: 700; color: #fff; letter-spacing: -0.04em;
            line-height: 1.05; margin-bottom: 14px;
          }
          .term-hero-dot { color: #7c3aed; }
          .term-hero-tagline {
            font-family: 'Inter', sans-serif; font-size: 1.02rem;
            line-height: 1.6; color: #a3a3a3; max-width: 640px;
          }
          .term-hero-accent { color: #c4b5fd; font-weight: 500; }

          .pill {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 3px 9px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.68rem; font-weight: 500;
            border: 1px solid #1f1f1f; border-radius: 999px;
            color: #888; background: #0a0a0a; letter-spacing: 0.02em;
          }
          .pill.ok    { border-color: #1d4d2c; color: #4ade80; }
          .pill.warn  { border-color: #4d3a1d; color: #fbbf24; }
          .pill.bad   { border-color: #4d1d1d; color: #f87171; }
          .pill.accent{ border-color: #3a1d6e; color: #c4b5fd; }
          .pill .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

          .term-section {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem; font-weight: 700; color: #ededed;
            letter-spacing: 0.16em; text-transform: uppercase;
            margin: 28px 0 10px;
          }
          .term-section::before { content: ">  "; color: #7c3aed; }
          .term-hint {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem; color: #a3a3a3; margin: 0 0 12px;
          }
          .term-hint::before { content: "▸  "; color: #7c3aed; }

          input, textarea, .stTextInput input, .stTextArea textarea {
            background: #0a0a0a !important; border: 1px solid #1a1a1a !important;
            color: #ededed !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.82rem !important; border-radius: 6px !important;
          }
          .stTextInput input::placeholder,
          .stTextArea textarea::placeholder { color: #404040 !important; }
          .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #7c3aed !important;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
            outline: none !important;
          }
          .stTextInput label, .stTextArea label, .stFileUploader label {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.7rem !important; color: #888 !important;
            text-transform: uppercase; letter-spacing: 0.1em;
            font-weight: 500 !important;
          }

          [data-testid="stFileUploader"] section {
            background: #0a0a0a !important; border: 1px dashed #2a2a2a !important;
            border-radius: 8px; color: #888 !important;
          }
          [data-testid="stFileUploader"] button {
            background: #111 !important; border: 1px solid #2a2a2a !important;
            color: #ededed !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.75rem !important;
          }

          .stButton button, .stDownloadButton button {
            background: #0a0a0a; border: 1px solid #2a2a2a; color: #ededed;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem; font-weight: 500;
            border-radius: 6px; padding: 0.55rem 1rem;
            transition: all 0.12s ease; letter-spacing: 0.04em;
          }
          .stButton button:hover, .stDownloadButton button:hover {
            border-color: #7c3aed; background: rgba(124, 58, 237, 0.08); color: #fff;
          }
          .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
            background: #fff !important; color: #000 !important;
            border-color: #fff !important; font-weight: 600 !important;
          }
          .stButton button[kind="primary"]:hover,
          .stDownloadButton button[kind="primary"]:hover {
            background: #ededed !important; color: #000 !important;
          }

          .stTabs [data-baseweb="tab-list"] {
            background: transparent; border-bottom: 1px solid #1a1a1a;
            gap: 0; margin-top: 16px;
          }
          .stTabs [data-baseweb="tab"] {
            background: transparent !important; color: #525252 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.72rem !important; text-transform: uppercase;
            letter-spacing: 0.12em; padding: 12px 18px !important;
            border-radius: 0 !important; border-bottom: 2px solid transparent !important;
          }
          .stTabs [aria-selected="true"] {
            color: #fff !important; border-bottom-color: #7c3aed !important;
          }

          .stMarkdown p, .stMarkdown li { color: #ededed; font-size: 0.92rem; line-height: 1.6; }
          .stMarkdown h1 { font-size: 1.4rem !important; }
          .stMarkdown h2 { font-size: 1.05rem !important; margin-top: 1.4rem !important; }
          .stMarkdown h3 { font-size: 0.92rem !important; color: #c4b5fd !important; }
          .stMarkdown code {
            background: #0a0a0a !important; color: #c4b5fd !important;
            padding: 1px 6px; border-radius: 4px;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.85em !important;
          }

          [data-testid="stMetric"] {
            background: #0a0a0a; border: 1px solid #1a1a1a;
            border-radius: 8px; padding: 14px 16px;
          }
          [data-testid="stMetricLabel"],
          [data-testid="stMetricLabel"] > div,
          [data-testid="stMetricLabel"] p {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.64rem !important; color: #a3a3a3 !important;
            text-transform: uppercase; letter-spacing: 0.1em;
            white-space: normal !important; overflow: visible !important;
            text-overflow: clip !important;
          }
          [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 1.6rem !important; color: #fff !important; font-weight: 700 !important;
          }

          [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #7c3aed 0%, #a78bfa 100%) !important;
          }

          [data-testid="stAlert"] {
            background: #0a0a0a !important; border: 1px solid #1a1a1a !important;
            border-radius: 8px !important; color: #ededed !important;
          }

          hr { border-color: #1a1a1a !important; margin: 20px 0 !important; }

          /* widget-shared classes */
          .rationale-text {
            font-family: 'Inter', sans-serif; font-size: 0.82rem;
            line-height: 1.55; color: #a3a3a3; margin-top: 10px;
          }
          .native-banner {
            padding: 12px 14px; background: #0a0a0a; border: 1px solid #3a1d6e;
            border-radius: 8px; font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem; color: #c4b5fd; margin: 12px 0;
          }
          .download-hint {
            font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
            color: #525252; margin: 12px 0 8px;
          }
          .download-hint::before { content: "▸  "; }
          .cover-letter-body {
            white-space: pre-wrap; font-family: 'Inter', sans-serif;
            line-height: 1.7; padding: 18px 20px;
            background: #0a0a0a; border: 1px solid #1a1a1a;
            border-radius: 8px; color: #ededed; font-size: 0.92rem;
          }
          .match-summary {
            font-family: 'Inter', sans-serif; font-size: 0.94rem;
            line-height: 1.6; color: #d4d4d4;
            margin: 14px 0 22px; max-width: 720px;
          }

          .term-statusbar {
            position: fixed; left: 0; right: 0; bottom: 0;
            background: #050505; border-top: 1px solid #1a1a1a;
            padding: 8px 24px;
            font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
            color: #525252; z-index: 100; text-align: center;
            letter-spacing: 0.04em;
          }
          .term-statusbar .sep { color: #2a2a2a; margin: 0 8px; }
          .term-statusbar b { color: #ededed; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section(label: str, hint: str = "") -> None:
    st.markdown(f'<div class="term-section">{escape(label)}</div>', unsafe_allow_html=True)
    if hint:
        st.markdown(f'<div class="term-hint">{escape(hint)}</div>', unsafe_allow_html=True)


def render() -> None:
    st.set_page_config(
        page_title="ResumeTailor",
        page_icon="⬛",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    _inject_css()

    api_ready = bool(settings.active_api_key)
    status_html = (
        '<span class="pill ok"><span class="dot"></span>READY</span>'
        if api_ready
        else '<span class="pill bad"><span class="dot"></span>NO API KEY</span>'
    )

    st.markdown(
        f"""
        <div class="term-header">
          <div class="term-logo">RESUMETAILOR</div>
          <div style="display:flex; gap:8px; align-items:center;">
            <span class="pill">{escape(settings.active_model)}</span>
            {status_html}
          </div>
        </div>

        <div class="term-hero">
          <div class="term-hero-title">ResumeTailor<span class="term-hero-dot">.</span></div>
          <div class="term-hero-tagline">
            Tailor your resume to every job —
            <span class="term-hero-accent">truthfully, intelligently, instantly</span>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # — Inputs —
    _section("JOB", "paste a URL or the full job description")
    url_fetch_row(fetch_label="FETCH  ↓")

    jd_text_input = st.text_area(
        "JD",
        height=200,
        placeholder="or paste the full job description here…",
        key="jd_text_area",
        label_visibility="collapsed",
    )

    _section("RESUME", "upload your master resume or paste it below")
    resume_file = st.file_uploader(
        "RESUME FILE",
        type=["pdf", "docx", "txt", "md"],
        label_visibility="collapsed",
    )
    resume_text_input = st.text_area(
        "RESUME TEXT",
        height=180,
        placeholder="or paste resume text…",
        label_visibility="collapsed",
    )

    if resume_file is not None:
        st.markdown(
            f'<div class="term-hint">{escape(resume_file.name)} · '
            f'{len(resume_file.getvalue()):,} bytes · ✓ loaded</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin: 28px 0 12px;'></div>", unsafe_allow_html=True)
    run = st.button("RUN  →", type="primary", use_container_width=True)

    if run:
        jd_text = (jd_text_input or "").strip()
        resume_text, source_docx_bytes = resolve_resume_inputs(resume_file, resume_text_input)
        if not jd_text:
            st.error("Missing JD"); st.stop()
        if not resume_text:
            st.error("Missing resume"); st.stop()
        if not api_ready:
            st.error(f"No API key for `{settings.provider}`"); st.stop()

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
            st.error(f"Failed · {e}")
            with st.expander("trace"):
                st.code(traceback.format_exc())
            st.stop()

    # — Results —
    result: dict[str, Any] | None = st.session_state.get("result")
    if not result:
        st.markdown(
            '<div class="term-statusbar">paste a job description and resume · then press <b>RUN →</b></div>',
            unsafe_allow_html=True,
        )
        return

    match = result["match"]
    overall = int(match.get("overall_score", 0))
    role = result["jd_struct"].get("role_title", "—")
    company = result["jd_struct"].get("company", "—")

    _section("OUTPUT")
    m1, m2, m3 = st.columns([1, 1, 2])
    m1.metric("MATCH", f"{overall}")
    m2.metric("VERDICT", (match.get("verdict") or "—").lower())
    m3.markdown(
        f"<div style='padding-top: 8px;'>"
        f"<div class='term-hint' style='margin:0;'>ROLE</div>"
        f"<div style='color:#ededed; font-family:JetBrains Mono,monospace; font-size:0.92rem;'>"
        f"{escape(role)} <span style='color:#525252'>·</span> "
        f"<span style='color:#c4b5fd'>{escape(company)}</span></div></div>",
        unsafe_allow_html=True,
    )

    render_result_tabs(
        result,
        tab_labels=("RESUME", "COVER LETTER", "GAP", "MATCH"),
    )

    st.markdown(
        f'<div class="term-statusbar">'
        f'<b>MATCH</b> {overall}/100 '
        f'<span class="sep">·</span> '
        f'<b>{escape(role)}</b> · {escape(company)} '
        f'<span class="sep">·</span> '
        f'model <b>{escape(settings.active_model)}</b>'
        f'</div>',
        unsafe_allow_html=True,
    )
