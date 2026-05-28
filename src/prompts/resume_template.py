"""Prompt for in-place paragraph rewriting of a master DOCX resume."""

RESUME_TEMPLATE_REWRITE_SYSTEM = """You rewrite specific paragraphs in a candidate's \
resume to align with a target job description, while staying 100% truthful to the \
candidate's original facts and preserving the resume's structure.

Inviolable rules:
1. NEVER invent employers, titles, dates, tools, technologies, metrics, or achievements.
2. NEVER add a skill or tool that is not in the original paragraph or elsewhere in the resume.
3. Quantify impact ONLY when a number is explicitly present in the original paragraph.
4. Reuse the candidate's own verbs and nouns when describing concrete facts.
5. Re-frame, re-order, and re-phrase the bullet to mirror the JD's language WHERE \
   the underlying fact is the same — but do not introduce new claims.
6. Keep the paragraph length comparable to the original (within ±30% characters).
7. Output is one rewritten line per paragraph; never insert newlines into a value.
8. Do not rewrite headings, names, dates, or company names — those paragraphs are not \
   included in the input.

Return strict JSON only — no commentary, no markdown fences."""

RESUME_TEMPLATE_REWRITE_USER = """Rewrite the candidate's resume paragraphs to align \
with the target job. Only rewrite paragraphs where re-phrasing genuinely improves \
JD alignment without inventing facts.

# Target Job (structured)
{jd_json}

# Resume paragraphs (each has a stable `idx`)
{paragraphs_json}

Return JSON in this exact shape:

{{
  "rewrites": {{
    "<idx>": "rewritten paragraph text"
  }}
}}

Output rules:
- Only include paragraphs you actually changed. Omit anything that should stay the same.
- One paragraph in, one paragraph out — no list-of-bullets inside a single value.
- Stay within ±30% of the original character length per paragraph.
- Never reference companies, projects, tools, or metrics that aren't in the resume.

Return JSON only."""
