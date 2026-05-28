# CLAUDE.md

Project-specific guidance for Claude Code working in this repo.

## What this project is

**ResumeTailor AI** — a Streamlit app that tailors a user's resume and cover letter to a specific job description, grounded strictly in the user's master resume (no fabricated experience). Supports Anthropic and OpenAI providers via a pluggable factory, four UI themes, and DOCX/PDF export. Includes a Contact page powered by Resend.

## Architecture at a glance

```
app.py                          # entry — dispatches to active UI theme
pages/
  └── 2_Contact.py              # Streamlit multipage: contact form (Resend)
src/
  ├── config.py                 # env-driven settings (single source of truth)
  ├── llm/                      # provider abstraction (anthropic, openai/openrouter)
  ├── parsers/                  # PDF/DOCX/TXT and JD URL fetching
  ├── analysis/                 # extractor + matcher (JD ↔ resume scoring)
  ├── generators/               # resume / cover letter / gap analysis
  ├── prompts/                  # all prompt templates live here
  ├── exporters/                # docx + pdf
  ├── ui/
  │   ├── pipeline.py           # orchestrates the full tailoring pipeline
  │   ├── widgets.py            # shared widgets (url fetch, result tabs)
  │   └── themes/               # terminal | minimal | workspace | wizard
  └── utils/                    # cache, json helpers
```

## Key conventions

- **Settings come from env vars only.** Edit `src/config.py` to add a new setting; never read `os.getenv` directly elsewhere. `config.py` also bridges Streamlit Cloud `st.secrets` into `os.environ` so the same code works locally and on Streamlit Cloud.
- **Themes are isolated.** Each theme module in `src/ui/themes/` exposes a single `render()` function that owns the full page (its own CSS, layout, widgets). To add a theme: drop a new file in that directory, register it in `src/ui/themes/__init__.py`, add the slug to `VALID_THEMES` in `src/config.py`.
- **Prompts live in `src/prompts/`.** Don't inline prompts in generators or analyzers.
- **Truthfulness is non-negotiable.** Every generator prompt forbids invented employers, titles, dates, tools, metrics, or achievements. When editing prompts, preserve those constraints.
- **LLM access goes through `src/llm/factory.py`.** Never instantiate provider SDKs directly in business logic.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in keys
streamlit run app.py
```

## Deployment

Deployed on Streamlit Community Cloud. Secrets are configured via the Streamlit Cloud UI in TOML format — the bridging logic in `src/config.py` exposes them as env vars so existing code works unchanged.

## Contact page

`pages/2_Contact.py` is a Streamlit multipage that uses the Resend API. Required env vars: `RESEND_API_KEY`, `CONTACT_TO_EMAIL`. Optional: `CONTACT_FROM_EMAIL` (defaults to `onboarding@resend.dev`, Resend's shared sandbox sender).

The page is reachable from Streamlit's sidebar (auto-populated by multipage discovery). Theme CSS no longer hides the sidebar.

## Things to be careful about

- **Do not commit `.env`.** It's gitignored. The `.env.example` is the canonical template.
- **Do not commit `data/*.db*` files.** They may contain personal resume/JD content; the gitignore covers this.
- **The repo is public.** Be careful not to introduce sample data containing real personal info — use synthetic samples only.
- **API costs.** Any deployed instance burns the owner's LLM credits. The "BYO key" pattern is not yet implemented; if adding it, the UI input should override `settings.active_api_key` for that session only.
