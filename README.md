# ResumeTailor AI

An end-to-end Streamlit app that tailors your resume and cover letter to a specific job description — grounded strictly in your master resume, with no fabricated experience.

## Features

- **JD + Resume parsing** (PDF, DOCX, TXT, or pasted text)
- **Structured extraction** of skills, experience, achievements, tools, and keywords
- **Tailored resume** rewriting (truthful, ATS-friendly)
- **Tailored cover letter** grounded only in verified resume facts
- **Gap analysis** with ranked learning priorities + interview prep plan
- **JD-to-resume match score** with breakdown
- **DOCX + PDF export**
- **Pluggable LLM providers** (Anthropic, OpenAI) via a single factory

## Project Structure

```
Resume_update/
├── app.py                          # Streamlit entrypoint
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py                   # Env vars and settings
│   ├── llm/                        # Provider abstraction
│   │   ├── base.py
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── factory.py
│   ├── parsers/
│   │   └── document_parser.py      # PDF/DOCX/TXT loaders
│   ├── analysis/
│   │   ├── extractor.py            # Structured extraction
│   │   └── matcher.py              # Match scoring
│   ├── generators/
│   │   ├── resume_generator.py
│   │   ├── cover_letter_generator.py
│   │   └── gap_analyzer.py
│   ├── prompts/                    # All prompt templates
│   │   ├── extraction.py
│   │   ├── resume.py
│   │   ├── cover_letter.py
│   │   ├── gap.py
│   │   └── matching.py
│   ├── exporters/
│   │   ├── docx_exporter.py
│   │   └── pdf_exporter.py
│   └── utils/
│       ├── cache.py
│       └── json_utils.py
└── README.md
```

## Setup

### 1. Clone and install

```bash
cd Resume_update
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your key
```

You need one of:
- `ANTHROPIC_API_KEY` (default provider)
- `OPENAI_API_KEY`

Choose provider with `LLM_PROVIDER=anthropic` or `LLM_PROVIDER=openai`.

### 3. Run

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## How it works

1. **Parse JD** — clean the JD text into a normalized representation.
2. **Parse resume** — extract plain text from PDF/DOCX/TXT or paste.
3. **Extract structured data** — skills, tools, achievements, experience, education.
4. **Compare** — JD vs resume gives match score + missing items.
5. **Generate resume** — rewrite resume bullets grounded **only** in the master resume.
6. **Generate cover letter** — grounded in verified resume facts.
7. **Gap analysis** — ranked learning priorities + interview prep questions.

## Truthfulness guarantees

Every generator prompt enforces:
- No invented employers, titles, dates, tools, metrics, or achievements.
- Quantified impact only when explicitly supported by source text.
- Reuse phrasing from the master resume when claims are made.

## Swapping LLM providers

Add a new file in `src/llm/`, implement `LLMProvider`, register it in `src/llm/factory.py`. Done.

## Caching

Repeated calls with the same `(prompt, model)` pair are cached in-process via `functools.lru_cache` plus Streamlit's `@st.cache_data`.

## Notes

- DOCX export uses `python-docx`.
- PDF export uses `reportlab` (no system dependencies required).
- For best ATS compatibility, prefer DOCX.
