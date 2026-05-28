"""Parse PDF, DOCX, and TXT uploads into plain text."""
from __future__ import annotations

import io
import re
from typing import BinaryIO

from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    pass


def parse_uploaded_file(filename: str, file_bytes: bytes) -> str:
    """Dispatch to the right parser based on file extension."""
    name = filename.lower().strip()
    if name.endswith(".pdf"):
        return _parse_pdf(file_bytes)
    if name.endswith(".docx"):
        return _parse_docx(file_bytes)
    if name.endswith(".txt") or name.endswith(".md"):
        return file_bytes.decode("utf-8", errors="ignore")
    raise UnsupportedFileTypeError(
        f"Unsupported file type: {filename}. Use PDF, DOCX, or TXT."
    )


def _parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return clean_text("\n".join(pages))


_MC_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"


def _is_in_mc_fallback(elem) -> bool:
    """True if elem lives inside an <mc:Fallback> branch (legacy Word fallback)."""
    parent = elem.getparent()
    while parent is not None:
        if parent.tag == _MC_FALLBACK:
            return True
        parent = parent.getparent()
    return False


def _parse_docx(file_bytes: bytes) -> str:
    """Extract text from every <w:p> in the document.

    `doc.paragraphs` only yields body-level paragraphs; designer-style resumes
    lay out columns with floating text boxes (<w:txbxContent>). Walking the
    underlying lxml tree for all <w:p> elements catches text-boxed paragraphs,
    table cells, and nested drawings uniformly.

    Word stores `<mc:AlternateContent>` with both a modern `<mc:Choice>` and a
    legacy `<mc:Fallback>` rendering for back-compat; we skip the fallback
    branch to avoid extracting every paragraph twice.
    """
    doc = Document(io.BytesIO(file_bytes))
    parts: list[str] = []
    for p_elem in doc.element.body.iter(qn("w:p")):
        if _is_in_mc_fallback(p_elem):
            continue
        text = "".join(t.text or "" for t in p_elem.iter(qn("w:t")))
        if text.strip():
            parts.append(text)
    return clean_text("\n".join(parts))


def clean_text(raw: str) -> str:
    """Collapse weird whitespace and form-feed artifacts from PDF extraction."""
    text = raw.replace("\x0c", "\n").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
