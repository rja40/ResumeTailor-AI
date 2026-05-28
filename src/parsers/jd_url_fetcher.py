"""Fetch a job description from a URL.

Best-effort, deterministic, no LLM calls. Three tiers of extraction:

1. **Known ATS providers** (Greenhouse, Lever, Ashby) — clean JSON APIs.
2. **LinkedIn** — undocumented but stable `jobs-guest/jobs/api/jobPosting/{id}`
   endpoint that serves a static JD without authentication.
3. **Indeed / Glassdoor / everything else** — generic HTTP GET with browser-like
   headers, content extraction via BeautifulSoup. CloudFlare/imperva bot-check
   pages are detected and surfaced as `BotCheckError` rather than returned as
   misleading "empty" content.
"""
from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from .document_parser import clean_text


# ──────────────────────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────────────────────


class JDFetchError(Exception):
    """Base class for all fetcher failures."""


class MalformedURLError(JDFetchError):
    """URL is not parseable or not http(s)."""


class NetworkError(JDFetchError):
    """Network failure: timeout, DNS error, non-2xx status."""


class LoginWallError(JDFetchError):
    """Page redirected to a login/signin/authwall URL."""


class BotCheckError(JDFetchError):
    """CloudFlare / imperva challenge page detected."""


class EmptyJDError(JDFetchError):
    """Fetched and parsed but produced too little text to be a real JD."""


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}

TIMEOUT = 15
MIN_JD_LENGTH = 200

_BOTCHECK_PHRASES = (
    "verify you are human",
    "checking your browser",
    "press & hold",
    "press and hold",
    "unusual traffic from your computer",
    "enable javascript and cookies to continue",
)

_LOGIN_PATH_HINTS = ("/login", "/signin", "/sign-in", "/authwall", "/log-in")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _html_to_text(html_str: str) -> str:
    """HTML → plain text. Strips tags, decodes entities."""
    if not html_str:
        return ""
    soup = BeautifulSoup(html.unescape(html_str), "html.parser")
    return soup.get_text("\n")


def _looks_like_botcheck(text: str) -> bool:
    """Heuristic detection of CloudFlare/imperva challenge pages."""
    lower = text.lower()
    return any(phrase in lower for phrase in _BOTCHECK_PHRASES)


def _finalize(text: str) -> str:
    """Normalize and length-gate the extracted text."""
    cleaned = clean_text(text)
    if len(cleaned.strip()) < MIN_JD_LENGTH:
        raise EmptyJDError(
            f"Extracted only {len(cleaned.strip())} chars (need ≥ {MIN_JD_LENGTH})."
        )
    return cleaned


def _get(url: str) -> requests.Response:
    """Wrap requests.get with our headers, timeout, and uniform error mapping."""
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        raise NetworkError(f"{type(e).__name__}: {e}") from e
    if r.status_code >= 400:
        raise NetworkError(f"HTTP {r.status_code} from {url}")
    return r


# ──────────────────────────────────────────────────────────────────────────────
# Generic HTML extractor
# ──────────────────────────────────────────────────────────────────────────────

_NOISE_TAGS = ("script", "style", "nav", "footer", "header", "aside", "form", "noscript", "iframe")
_NOISE_CLASS_RE = re.compile(r"\b(nav|menu|footer|header|sidebar|cookie|banner)\b", re.I)


def _extract_generic(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")

    # Strip obviously-non-content tags.
    for tag in list(soup(_NOISE_TAGS)):
        tag.decompose()

    # Strip elements whose class or id reads like chrome. Collect first, then
    # decompose — mutating during iteration invalidates BS4's element refs.
    chrome: list = []
    for el in soup.find_all(True):
        if el.attrs is None:
            continue
        classes = " ".join(el.get("class") or [])
        el_id = el.get("id") or ""
        if (classes and _NOISE_CLASS_RE.search(classes)) or (
            el_id and _NOISE_CLASS_RE.search(el_id)
        ):
            chrome.append(el)
    for el in chrome:
        el.decompose()

    # Prefer semantic main content; else the largest content block.
    container = soup.find("main") or soup.find("article")
    if container is None:
        candidates = soup.find_all(["section", "div"])
        if candidates:
            container = max(candidates, key=lambda c: len(c.get_text(" ", strip=True)))
    if container is None:
        container = soup.body or soup

    return container.get_text("\n")


# ──────────────────────────────────────────────────────────────────────────────
# Site-specific extractors
# ──────────────────────────────────────────────────────────────────────────────


_GREENHOUSE_RE = re.compile(r"^/(?P<board>[^/]+)/jobs/(?P<id>\d+)")


def _fetch_greenhouse(board: str, job_id: str) -> str:
    api = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"
    r = _get(api)
    data = r.json()
    return _html_to_text(data.get("content", ""))


_LEVER_RE = re.compile(r"^/(?P<company>[^/]+)/(?P<uuid>[0-9a-fA-F-]{8,})")


def _fetch_lever(company: str, uuid: str) -> str:
    api = f"https://api.lever.co/v0/postings/{company}/{uuid}?mode=json"
    r = _get(api)
    data = r.json()
    parts: list[str] = []
    if data.get("descriptionPlain"):
        parts.append(data["descriptionPlain"])
    elif data.get("description"):
        parts.append(_html_to_text(data["description"]))
    for lst in data.get("lists", []) or []:
        if lst.get("text"):
            parts.append(_html_to_text(lst["text"]))
    if data.get("additionalPlain"):
        parts.append(data["additionalPlain"])
    return "\n\n".join(parts)


_ASHBY_RE = re.compile(r"^/(?P<company>[^/]+)/(?P<uuid>[0-9a-fA-F-]{8,})")


def _fetch_ashby(company: str, uuid: str) -> str:
    # The single-posting endpoint requires auth; the job-board listing does not.
    # Fetch the org's full board and find the matching job by id.
    api = f"https://api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true"
    r = _get(api)
    data = r.json()
    target = next((j for j in data.get("jobs", []) if j.get("id") == uuid), None)
    if not target:
        raise EmptyJDError(f"Ashby board has no job with id {uuid}.")
    desc = target.get("descriptionHtml") or target.get("descriptionPlain") or ""
    return _html_to_text(desc) if "<" in desc else desc


# Ashby slug detection in company-hosted career pages.
# Two signals: (1) iframe/script src containing "ashbyhq.com/<slug>",
# (2) inline JSON like organizationSlug: "<slug>" or "organization":"<slug>".
_ASHBY_SLUG_FROM_HTML_RE = re.compile(
    r'(?:ashbyhq\.com/embed/|jobs\.ashbyhq\.com/|'
    r'organizationSlug["\']?\s*[:=]\s*["\']|'
    r'organization["\']?\s*[:=]\s*["\'])(?P<slug>[a-zA-Z0-9_-]+)'
)


def _resolve_ashby_slug(html_str: str) -> str | None:
    """Try to find the Ashby org slug from the company's careers page HTML."""
    m = _ASHBY_SLUG_FROM_HTML_RE.search(html_str)
    return m.group("slug") if m else None


def _fetch_ashby_embedded(careers_url: str, ashby_jid: str) -> str:
    """Handle company-hosted careers pages with `?ashby_jid=<uuid>` query param.

    Strategy:
      1. Guess the org slug from the careers URL's second-level domain
         (e.g. wrapbook.com → "wrapbook"). Try the public board API.
      2. If that 404s or the job isn't in the result, fetch the careers page
         HTML and look for an Ashby slug reference (iframe/script src,
         organizationSlug literal). Retry with the discovered slug.
    """
    parsed = urlparse(careers_url)
    host = parsed.netloc.lower().lstrip("www.")
    guessed_slug = host.split(".")[0] if host else ""

    if guessed_slug:
        try:
            return _fetch_ashby(guessed_slug, ashby_jid)
        except (NetworkError, EmptyJDError):
            pass  # fall through to HTML-scrape discovery

    # Fetch the careers page and look for the real slug.
    r = _get(careers_url)
    real_slug = _resolve_ashby_slug(r.text)
    if not real_slug:
        raise EmptyJDError(
            f"Couldn't determine Ashby org slug for {host}. The page may load jobs "
            "via JavaScript that requires a browser."
        )
    if real_slug == guessed_slug:
        # We already tried this slug above and it failed.
        raise EmptyJDError(f"Ashby slug '{real_slug}' has no job with id {ashby_jid}.")
    return _fetch_ashby(real_slug, ashby_jid)


_LINKEDIN_ID_RE = re.compile(
    r"/jobs(?:/view|-guest/jobs/api/jobPosting)/(?P<id>\d+)"
)


def _fetch_linkedin(url: str) -> str:
    m = _LINKEDIN_ID_RE.search(url)
    if not m:
        # No recognizable job ID — fall back to generic.
        r = _get(url)
        return _extract_generic(r.text)
    job_id = m.group("id")
    api = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    r = _get(api)
    if _looks_like_botcheck(r.text):
        raise BotCheckError("LinkedIn returned a challenge page.")
    soup = BeautifulSoup(r.text, "html.parser")
    container = (
        soup.find(class_="description__text")
        or soup.find(class_="show-more-less-html__markup")
    )
    if container is not None:
        return container.get_text("\n")
    # Fall back to generic if the structure changed.
    return _extract_generic(r.text)


def _get_with_botcheck_on_403(url: str, site: str) -> requests.Response:
    """For Indeed/Glassdoor, 403/429 means bot-detection — surface a clearer error."""
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        raise NetworkError(f"{type(e).__name__}: {e}") from e
    if r.status_code in (403, 429):
        raise BotCheckError(f"{site} blocked the request (HTTP {r.status_code}).")
    if r.status_code >= 400:
        raise NetworkError(f"HTTP {r.status_code} from {url}")
    return r


def _fetch_indeed(url: str) -> str:
    r = _get_with_botcheck_on_403(url, "Indeed")
    if _looks_like_botcheck(r.text):
        raise BotCheckError("Indeed returned a bot-check page.")
    soup = BeautifulSoup(r.text, "html.parser")
    container = soup.find(id="jobDescriptionText")
    if container is not None:
        return container.get_text("\n")
    return _extract_generic(r.text)


def _fetch_glassdoor(url: str) -> str:
    r = _get_with_botcheck_on_403(url, "Glassdoor")
    if _looks_like_botcheck(r.text):
        raise BotCheckError("Glassdoor returned a bot-check page.")
    soup = BeautifulSoup(r.text, "html.parser")
    container = soup.find(class_=re.compile(r"jobDescriptionContent|JobDetails_jobDescription"))
    if container is not None:
        return container.get_text("\n")
    return _extract_generic(r.text)


# ──────────────────────────────────────────────────────────────────────────────
# Site detection + dispatch
# ──────────────────────────────────────────────────────────────────────────────


def _detect_and_dispatch(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""
    qs = parse_qs(parsed.query or "")

    # Company-hosted careers pages that embed Ashby with `?ashby_jid=<uuid>`.
    if "ashby_jid" in qs and qs["ashby_jid"]:
        return _fetch_ashby_embedded(url, qs["ashby_jid"][0])

    # Same pattern for Greenhouse-embedded boards: `?gh_jid=<id>` or `?gh_src=...`.
    if "gh_jid" in qs and qs["gh_jid"]:
        # gh_jid in isolation lacks a board slug; try domain root.
        gh_id = qs["gh_jid"][0]
        slug = (host.lstrip("www.").split(".")[0]) if host else ""
        if slug:
            try:
                return _fetch_greenhouse(slug, gh_id)
            except (NetworkError, EmptyJDError):
                pass  # fall through to generic

    if host in ("boards.greenhouse.io", "job-boards.greenhouse.io"):
        m = _GREENHOUSE_RE.match(path)
        if m:
            return _fetch_greenhouse(m.group("board"), m.group("id"))

    if host == "jobs.lever.co":
        m = _LEVER_RE.match(path)
        if m:
            return _fetch_lever(m.group("company"), m.group("uuid"))

    if host == "jobs.ashbyhq.com" or host.endswith(".ashbyhq.com"):
        m = _ASHBY_RE.match(path)
        if m:
            return _fetch_ashby(m.group("company"), m.group("uuid"))
        # Subdomain form: <company>.ashbyhq.com/<uuid>
        if host.endswith(".ashbyhq.com"):
            company = host.split(".ashbyhq.com")[0]
            uuid_match = re.match(r"^/(?P<uuid>[0-9a-fA-F-]{8,})", path)
            if uuid_match:
                return _fetch_ashby(company, uuid_match.group("uuid"))

    if host.endswith("linkedin.com"):
        return _fetch_linkedin(url)

    if host.endswith("indeed.com"):
        return _fetch_indeed(url)

    if "glassdoor." in host:
        return _fetch_glassdoor(url)

    # Generic
    r = _get(url)
    final = r.url or url
    if any(hint in final.lower() for hint in _LOGIN_PATH_HINTS):
        raise LoginWallError(f"Redirected to a login page: {final}")
    if _looks_like_botcheck(r.text):
        raise BotCheckError("Page returned a bot-check challenge.")
    return _extract_generic(r.text)


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────


def fetch_jd_from_url(url: str) -> str:
    """Fetch and extract the JD text from `url`. Always returns clean text or raises.

    Raises:
        MalformedURLError, NetworkError, LoginWallError, BotCheckError, EmptyJDError
        (all subclasses of JDFetchError).
    """
    if not url or not isinstance(url, str):
        raise MalformedURLError("URL is empty.")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise MalformedURLError("URL must start with http:// or https:// and have a host.")
    text = _detect_and_dispatch(url.strip())
    return _finalize(text)
