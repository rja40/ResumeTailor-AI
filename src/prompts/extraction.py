"""Prompts for structured extraction from JD and resume."""

RESUME_EXTRACTION_SYSTEM = """You are a precise resume parser. Extract structured \
information from the resume text exactly as written. Never invent or infer facts \
that are not explicitly stated. If a field is missing, return an empty array or \
empty string. Return strict JSON only — no commentary, no markdown fences."""

RESUME_EXTRACTION_USER = """Extract the following JSON schema from the resume text below.

Schema:
{{
  "contact": {{
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "links": ["string"]
  }},
  "summary": "string",
  "skills": ["string"],
  "tools": ["string"],
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "start_date": "string",
      "end_date": "string",
      "bullets": ["string"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "year": "string"
    }}
  ],
  "achievements": ["string"],
  "certifications": ["string"],
  "keywords": ["string"]
}}

Rules:
- Use the resume's own wording for bullets and achievements.
- "keywords" = canonical nouns/verbs that recruiters would search for, drawn from the resume.
- Do not paraphrase. Do not invent metrics. Do not add skills not present.

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"

Return JSON only."""


JD_EXTRACTION_SYSTEM = """You are a precise job-description parser. Extract \
structured requirements from a job posting. Return strict JSON only — no commentary, \
no markdown fences."""

JD_EXTRACTION_USER = """Extract the following JSON schema from the job description below.

Schema:
{{
  "role_title": "string",
  "company": "string",
  "location": "string",
  "seniority": "string",
  "summary": "string",
  "must_have_skills": ["string"],
  "nice_to_have_skills": ["string"],
  "tools": ["string"],
  "responsibilities": ["string"],
  "qualifications": ["string"],
  "domain_keywords": ["string"],
  "soft_skills": ["string"]
}}

Rules:
- Split skills into must-have vs nice-to-have based on language ("required", "must", \
"need" vs "preferred", "plus", "bonus").
- "domain_keywords" = industry/domain terms a recruiter or ATS would search for.
- Do not invent requirements that are not in the text.

JOB DESCRIPTION:
\"\"\"
{jd_text}
\"\"\"

Return JSON only."""
