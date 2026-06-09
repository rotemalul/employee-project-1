"""Headless-browser fallback for ATS detection (Comeet).

Comeet careers widgets load their positions from
    https://www.comeet.co/careers-api/2.0/company/{uid}/positions?token={token}
but the uid+token only appear *after* the page's JavaScript runs, so static
HTML scraping (discovery.py) can't see them. Here we render the page with a
headless browser and sniff that network request to recover uid+token.

We try the company's own careers page first (its embedded widget fires the
public careers-api call we need), falling back to any extra URLs provided.

Playwright is optional: if it isn't installed (e.g. local dev without the
browser), harvesting is skipped and the caller leaves the company undetected.
"""
from __future__ import annotations

import re
import sys

# Match the Comeet positions API in live network traffic. Kept loose on host
# (.co/.com) and version so widget variations still resolve to uid + token.
_CAREERS_API = re.compile(
    r"comeet\.com?/careers-api/[\d.]+/company/([0-9A-Za-z._-]+)/positions",
    re.IGNORECASE,
)
_TOKEN = re.compile(r"[?&]token=([0-9A-Za-z]+)", re.IGNORECASE)


def harvest_comeet(urls, expected_uid: str | None = None, timeout_ms: int = 30000) -> dict | None:
    """Render each URL until a Comeet positions request is seen.

    ``urls`` may be a single URL or a list (tried in order). ``expected_uid`` is
    the company's known Comeet uid (from comeet_url); when given we also accept
    any Comeet request that carries that uid + a token, not just the
    careers-api/2.0 path — this catches the hosted comeet.com pages too.
    Returns ``{'ats','uid','token'}`` or ``None`` (Playwright missing / nothing).
    """
    if isinstance(urls, str):
        urls = [urls]
    urls = [u for u in urls if u]
    if not urls:
        return None
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    found: dict = {}

    def _scan(request) -> None:
        if found:
            return
        u = request.url
        if "comeet" not in u.lower() or "token=" not in u.lower():
            return
        t = _TOKEN.search(u)
        if not t:
            return
        m = _CAREERS_API.search(u)
        if m:
            found["uid"], found["token"] = m.group(1), t.group(1)
        elif expected_uid and expected_uid.lower() in u.lower():
            found["uid"], found["token"] = expected_uid, t.group(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.on("request", _scan)
            for url in urls:
                try:
                    page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                except Exception:
                    pass  # a timeout is fine — the request may already be caught
                if found:
                    break
            browser.close()
    except Exception as exc:  # a browser crash must not fail the whole scrape
        print(f"    (browser harvest failed for {urls[0]}: {exc})", file=sys.stderr)
        return None

    if "uid" in found and "token" in found:
        return {"ats": "comeet", "uid": found["uid"], "token": found["token"]}
    return None
