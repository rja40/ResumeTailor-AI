"""Export Markdown / plain text to PDF bytes via reportlab."""
from __future__ import annotations

import io
import re
from html import escape

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _inline(text: str) -> str:
    """Convert Markdown bold to reportlab tags and escape the rest."""
    escaped = escape(text)
    return _BOLD_RE.sub(r"<b>\1</b>", escaped)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=18, spaceAfter=10, textColor="#111111",
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, spaceBefore=10, spaceAfter=4, textColor="#222222",
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=11, spaceBefore=6, spaceAfter=2, textColor="#333333",
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=14,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=14, leftIndent=12,
        ),
    }


def markdown_to_pdf_bytes(md: str) -> bytes:
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )

    story: list = []
    bullets: list = []

    def flush_bullets() -> None:
        if not bullets:
            return
        story.append(
            ListFlowable(
                [ListItem(Paragraph(b, styles["bullet"])) for b in bullets],
                bulletType="bullet",
                leftIndent=14,
            )
        )
        bullets.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_bullets()
            story.append(Spacer(1, 4))
            continue

        if line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(_inline(line[4:].strip()), styles["h3"]))
        elif line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(_inline(line[3:].strip()), styles["h2"]))
        elif line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(_inline(line[2:].strip()), styles["h1"]))
        elif line.lstrip().startswith(("- ", "* ")):
            bullets.append(_inline(line.lstrip()[2:]))
        else:
            flush_bullets()
            story.append(Paragraph(_inline(line), styles["body"]))

    flush_bullets()
    doc.build(story)
    return buf.getvalue()


def text_to_pdf_bytes(text: str) -> bytes:
    """Render plain text as a clean PDF — each paragraph on its own line."""
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
    )
    story: list = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        story.append(Paragraph(_inline(block).replace("\n", "<br/>"), styles["body"]))
        story.append(Spacer(1, 8))
    doc.build(story)
    return buf.getvalue()
