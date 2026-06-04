"""Headless-browser fallback for ATS detection (Comeet).

Comeet careers widgets load their positions from
    https://www.comeet.co/careers-api/2.0/company/{uid}/positions?token={token}
but the uid+token only appear *after* the page's JavaScript runs, so static
HTML scraping (discovery.py) can't see them. Here we render the page with a
headless browser and sniff that network request to recover uid+token.

Playwright is optional: if it isn't installed (e.g. local dev without the
browser), harvesting is skipped and the caller leaves the company undetected.
"""
from __future__ import annotations

import re
import sys

# Same marker discovery.py looks for, but matched against live network traffic.
_COMEET_API = re.compile(
    r"comeet\.co/careers-api/2\.0/company/([0-9A-Za-z._-]+)/positions\?token=([0-9A-Za-z]+)",
    re.IGNORECASE,
)


def harvest_comeet(url: str, timeout_ms: int = 45000) -> dict | None:
    """Render ``url`` and return ``{'ats','uid','token'}`` from the Comeet API
    call the page makes, or ``None`` if Playwright is unavailable / nothing found.
    """
    if not url:
        return None
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    found: dict = {}

    def _scan(request) -> None:
        if found:
            return
        m = _COMEET_API.search(request.url)
        if m:
            found["uid"], found["token"] = m.group(1), m.group(2)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.on("request", _scan)
            try:
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            except Exception:
                pass  # partial loads are fine — we only need the API request
            browser.close()
    except Exception as exc:  # a browser crash must not fail the whole scrape
        print(f"    (browser harvest failed for {url}: {exc})", file=sys.stderr)
        return None

    if "uid" in found and "token" in found:
        return {"ats": "comeet", "uid": found["uid"], "token": found["token"]}
    return None
