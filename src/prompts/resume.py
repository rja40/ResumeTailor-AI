"""Prompts for tailored resume generation."""

RESUME_REWRITE_SYSTEM = """You are an expert resume writer and ATS specialist. \
You rewrite resumes to align with a target job description while remaining 100% \
truthful to the candidate's master resume.

Inviolable rules:
1. NEVER invent employers, titles, dates, tools, technologies, metrics, or achievements.
2. NEVER add a skill that does not appear in the master resume.
3. Quantify impact only when a number is explicitly present in the source resume.
4. Reuse the candidate's own verbs and nouns when describing concrete experience.
5. Emphasize, reorder, and re-phrase — but do not fabricate.
6. Use strong action verbs and ATS-friendly keywords drawn from BOTH the resume \
   and the JD where the candidate has genuine matching experience.
7. Output in clean Markdown suitable for both DOCX and PDF export."""

RESUME_REWRITE_USER = """Rewrite the candidate's resume so it is tailored to the \
target role. Stay strictly grounded in the master resume facts.

# Target Role (structured JD)
{jd_json}

# Candidate Master Resume (structured)
{resume_json}

# Candidate Master Resume (raw text — source of truth)
\"\"\"
{resume_text}
\"\"\"

Output the tailored resume in this exact Markdown structure:

# {{Full Name}}
{{email}} · {{phone}} · {{location}} · {{links joined by ' · '}}

## Professional Summary
{{2–4 sentences tailored to the role, using only facts present in the master resume.}}

## Core Skills
- {{Comma-separated lines of skills the candidate actually has, prioritizing those \
the JD emphasizes.}}

## Experience
### {{Title}} — {{Company}}, {{Location}} · {{Start}} – {{End}}
- {{Bullet using candidate's real achievements, re-phrased to mirror JD language \
where the underlying fact is the same.}}
- {{...}}

(Repeat for each role in the master resume, in reverse-chronological order.)

## Education
- {{Degree}}, {{Institution}}, {{Year}}

## Certifications
- {{Each cert on its own line, only if present in master resume.}}

Return Markdown only — no commentary, no code fences."""
