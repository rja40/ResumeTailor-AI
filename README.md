# ResumeTailor AI

An end-to-end Streamlit app that tailors your resume and cover letter to a specific job description — grounded strictly in your master resume, with no fabricated experience.

> **Live demo:** *(add Streamlit Cloud URL after deployment)*

## Features

- **JD + Resume parsing** — PDF, DOCX, TXT, or pasted text; can also fetch JD from a URL.
- **Structured extraction** of skills, experience, achievements, tools, and keywords.
- **Tailored resume** rewriting (truthful, ATS-friendly).
- **Tailored cover letter** grounded only in verified resume facts.
- **Gap analysis** — ranked learning priorities + interview prep plan.
- **JD-to-resume match score** with breakdown.
- **DOCX + PDF export.**
- **Four UI themes** — `terminal`, `minimal`, `workspace`, `wizard`. Swap via env var.
- **Pluggable LLM providers** — Anthropic and OpenAI (also works with OpenRouter / Together / any OpenAI-compatible endpoint).
- **Contact page** powered by Resend.

## Project Structure

```
Resume_update/
├── app.py                          # Streamlit entrypoint
├── CLAUDE.md                       # guidance for Claude Code
├── requirements.txt
├── .env.example
├── pages/
│   └── 2_Contact.py                # contact form (Resend)
├── src/
│   ├── config.py                   # env vars + settings (also bridges Streamlit Cloud secrets)
│   ├── llm/                        # provider abstraction
│   │   ├── base.py
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── factory.py
│   ├── parsers/
│   │   ├── document_parser.py      # PDF/DOCX/TXT loaders
│   │   └── jd_url_fetcher.py
│   ├── analysis/
│   │   ├── extractor.py
│   │   └── matcher.py
│   ├── generators/
│   │   ├── resume_generator.py
│   │   ├── resume_template_generator.py
│   │   ├── cover_letter_generator.py
│   │   └── gap_analyzer.py
│   ├── prompts/                    # all prompt templates
│   ├── exporters/
│   │   ├── docx_exporter.py
│   │   ├── pdf_exporter.py
│   │   └── template_exporter.py
│   ├── ui/
│   │   ├── pipeline.py
│   │   ├── widgets.py
│   │   └── themes/                 # terminal | minimal | workspace | wizard
│   └── utils/
│       ├── cache.py
│       └── json_utils.py
└── README.md
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/rja40/ResumeTailor-AI.git
cd ResumeTailor-AI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your keys
```

Required (pick one):
- `ANTHROPIC_API_KEY` (default provider)
- `OPENAI_API_KEY` (set `LLM_PROVIDER=openai`; supports OpenRouter via `OPENAI_BASE_URL`)

Optional:
- `UI_THEME` — `terminal` (default), `minimal`, `workspace`, or `wizard`.
- `RESEND_API_KEY` + `CONTACT_TO_EMAIL` — enable the Contact page.

### 3. Run

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Deploying to Streamlit Community Cloud

1. Push to a public GitHub repo.
2. Go to https://share.streamlit.io/, sign in with GitHub, click **Create app**.
3. Pick the repo, branch `main`, main file `app.py`.
4. In **Advanced settings → Secrets**, paste TOML:

   ```toml
   LLM_PROVIDER = "anthropic"
   ANTHROPIC_API_KEY = "sk-ant-..."
   ANTHROPIC_MODEL = "claude-opus-4-7"
   UI_THEME = "terminal"
   RESEND_API_KEY = "re_..."
   CONTACT_TO_EMAIL = "you@example.com"
   ```

5. Deploy.

`src/config.py` automatically bridges `st.secrets` into `os.environ`, so the same code path works locally and on Streamlit Cloud.

## How it works

1. **Parse JD** — clean the JD text into a normalized representation (URL fetch supported).
2. **Parse resume** — extract plain text from PDF/DOCX/TXT or paste.
3. **Extract structured data** — skills, tools, achievements, experience, education.
4. **Compare** — JD vs resume → match score + missing items.
5. **Generate resume** — rewrite bullets grounded **only** in the master resume.
6. **Generate cover letter** — grounded in verified resume facts.
7. **Gap analysis** — ranked learning priorities + interview prep questions.

## Truthfulness guarantees

Every generator prompt enforces:
- No invented employers, titles, dates, tools, metrics, or achievements.
- Quantified impact only when explicitly supported by source text.
- Reuse phrasing from the master resume when claims are made.

## Swapping LLM providers

Add a new file in `src/llm/`, implement `LLMProvider`, register it in `src/llm/factory.py`.

## Caching

Repeated calls with the same `(prompt, model)` pair are cached in-process via `functools.lru_cache` plus Streamlit's `@st.cache_data`.

## Contact page

`pages/2_Contact.py` is a Streamlit multipage that sends messages via [Resend](https://resend.com). It auto-appears in the sidebar nav.

To enable:

```bash
RESEND_API_KEY=re_...
CONTACT_TO_EMAIL=you@example.com
CONTACT_FROM_EMAIL=onboarding@resend.dev   # optional, defaults to Resend's sandbox
```

For production use, verify your own domain in Resend and set `CONTACT_FROM_EMAIL` to a verified address.

## Notes

- DOCX export uses `python-docx`.
- PDF export uses `reportlab` (no system dependencies).
- For best ATS compatibility, prefer DOCX.

## License

MIT
