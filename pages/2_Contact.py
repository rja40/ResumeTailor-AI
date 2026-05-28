"""Contact page — sends messages via Resend."""
from __future__ import annotations

import re
from html import escape

import streamlit as st

from src.config import settings


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _inject_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap');
          html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
          .stApp { background: #000 !important; color: #ededed !important; }
          .main .block-container { max-width: 720px; padding-top: 2rem; }
          #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }

          h1, h2, h3 {
            font-family: 'JetBrains Mono', monospace !important;
            color: #fff !important; letter-spacing: -0.02em;
          }
          .contact-hero-title {
            font-family: 'JetBrains Mono', monospace; font-size: 2.4rem;
            color: #fff; letter-spacing: -0.04em; margin-bottom: 8px;
          }
          .contact-hero-title .dot { color: #7c3aed; }
          .contact-hero-tagline {
            color: #a3a3a3; font-size: 1rem; line-height: 1.6;
            margin-bottom: 28px; max-width: 540px;
          }

          input, textarea, .stTextInput input, .stTextArea textarea {
            background: #0a0a0a !important; border: 1px solid #1a1a1a !important;
            color: #ededed !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.85rem !important; border-radius: 6px !important;
          }
          .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #7c3aed !important;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
            outline: none !important;
          }
          .stTextInput label, .stTextArea label {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.7rem !important; color: #888 !important;
            text-transform: uppercase; letter-spacing: 0.1em;
          }

          .stButton button {
            background: #fff !important; color: #000 !important;
            border: 1px solid #fff !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600 !important; border-radius: 6px !important;
            padding: 0.6rem 1.2rem !important; letter-spacing: 0.05em;
          }
          .stButton button:hover {
            background: #ededed !important; border-color: #ededed !important;
          }

          [data-testid="stAlert"] {
            background: #0a0a0a !important; border: 1px solid #1a1a1a !important;
            border-radius: 8px !important; color: #ededed !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _send_email(name: str, sender_email: str, subject: str, message: str) -> tuple[bool, str]:
    """Returns (success, message_or_error)."""
    if not settings.resend_api_key:
        return False, "Contact form is not configured (missing RESEND_API_KEY)."
    if not settings.contact_to_email:
        return False, "Contact form is not configured (missing CONTACT_TO_EMAIL)."

    try:
        import resend
    except ImportError:
        return False, "Resend SDK not installed. Run: pip install resend"

    resend.api_key = settings.resend_api_key

    html_body = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px;">
      <h2 style="color: #111;">New ResumeTailor contact message</h2>
      <p><strong>From:</strong> {escape(name)} &lt;{escape(sender_email)}&gt;</p>
      <p><strong>Subject:</strong> {escape(subject)}</p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
      <div style="white-space: pre-wrap; line-height: 1.6; color: #333;">
        {escape(message)}
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": settings.contact_from_email,
            "to": settings.contact_to_email,
            "reply_to": sender_email,
            "subject": f"[ResumeTailor] {subject}",
            "html": html_body,
        })
        return True, "Message sent. I'll get back to you soon."
    except Exception as e:  # noqa: BLE001
        return False, f"Failed to send: {e}"


st.set_page_config(
    page_title="Contact · ResumeTailor",
    page_icon="✉",
    layout="centered",
    initial_sidebar_state="collapsed",
)
_inject_css()

st.markdown(
    """
    <div class="contact-hero-title">Contact<span class="dot">.</span></div>
    <div class="contact-hero-tagline">
      Questions, feedback, or want to collaborate? Send a message — it goes straight to my inbox.
    </div>
    """,
    unsafe_allow_html=True,
)

if not settings.resend_api_key or not settings.contact_to_email:
    st.warning(
        "Contact form is not fully configured. Set `RESEND_API_KEY` and `CONTACT_TO_EMAIL` "
        "in your environment to enable sending."
    )

with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("Name", placeholder="Your name")
    sender_email = st.text_input("Email", placeholder="you@example.com")
    subject = st.text_input("Subject", placeholder="What's this about?")
    message = st.text_area("Message", placeholder="Your message…", height=180)
    submitted = st.form_submit_button("Send Message")

if submitted:
    if not name.strip():
        st.error("Please enter your name.")
    elif not EMAIL_RE.match(sender_email.strip()):
        st.error("Please enter a valid email address.")
    elif not subject.strip():
        st.error("Please enter a subject.")
    elif not message.strip():
        st.error("Please enter a message.")
    else:
        with st.spinner("Sending…"):
            ok, info = _send_email(
                name.strip(), sender_email.strip(), subject.strip(), message.strip(),
            )
        if ok:
            st.success(info)
        else:
            st.error(info)
