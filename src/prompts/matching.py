"""Prompts for JD-to-resume match scoring."""

MATCH_SCORE_SYSTEM = """You are an ATS-style matching engine. You compute an \
honest, evidence-based match score between a candidate and a job description. \
Return strict JSON only — no commentary, no markdown fences."""

MATCH_SCORE_USER = """Score the candidate's fit for the role. Use both the \
structured data and the raw resume text as evidence. Be calibrated, not generous.

# Target Role
{jd_json}

# Candidate Resume (structured)
{resume_json}

# Candidate Resume (raw text)
\"\"\"
{resume_text}
\"\"\"

Return JSON in this exact schema:

{{
  "overall_score": 0-100,
  "verdict": "strong fit | moderate fit | stretch | poor fit",
  "breakdown": {{
    "skills_match": {{"score": 0-100, "rationale": "string"}},
    "experience_match": {{"score": 0-100, "rationale": "string"}},
    "tools_match": {{"score": 0-100, "rationale": "string"}},
    "domain_match": {{"score": 0-100, "rationale": "string"}},
    "seniority_match": {{"score": 0-100, "rationale": "string"}}
  }},
  "matched_keywords": ["string"],
  "missing_keywords": ["string"],
  "matched_skills": ["string"],
  "missing_must_have_skills": ["string"],
  "summary": "2-3 sentence honest assessment"
}}

Rules:
- "overall_score" is a weighted blend: skills 30%, experience 30%, tools 15%, \
  domain 15%, seniority 10%.
- "matched_keywords" must actually appear in the resume text.
- "missing_must_have_skills" only includes must-haves from the JD that the resume \
  truly lacks evidence for.
- Be honest. A poor match should score low.

Return JSON only."""
