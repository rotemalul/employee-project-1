"""Automatic ATS (applicant tracking system) discovery.

Given a company's careers URL we figure out which ATS it uses (Greenhouse /
Lever / Comeet) and the token/uid needed to query that ATS's public API — so
companies.yaml only needs a careers URL, not a hand-verified token.

Detection order:
  1. If the YAML already pins `ats`, trust it (manual override).
  2. Parse the careers URL itself — many companies link straight to their ATS.
  3. Otherwise fetch the careers page HTML and look for the same markers
     embedded in the page's scripts/iframes.

Successful detections are cached in data/ats_cache.json so we don't refetch
pages on every run. Undetected companies are retried next run (self-healing).
"""
from __future__ import annotations

import json
import os
import re

# --- marker patterns (applied to both URLs and page HTML) -------------------

# Comeet is most specific (carries both uid and token), so check it first.
_COMEET = re.compile(
    r"comeet\.co/careers-api/2\.0/company/([0-9A-Za-z._-]+)/positions\?token=([0-9A-Za-z]+)",
    re.IGNORECASE,
)
_GH_API = re.compile(
    r"boards-api\.greenhouse\.io/v1/boards/([a-zA-Z0-9_]+)", re.IGNORECASE
)
_GH_EMBED = re.compile(
    r"greenhouse\.io/embed/job_board(?:/js)?\?(?:[^\"'&]*&)?for=([a-zA-Z0-9_]+)",
    re.IGNORECASE,
)
_GH_BOARD = re.compile(
    r"(?:boards|job-boards)\.greenhouse\.io/(?!embed\b)([a-zA-Z0-9_]+)",
    re.IGNORECASE,
)
_LEVER = re.compile(
    r"(?:jobs|api)\.lever\.co/(?:v0/postings/)?([a-zA-Z0-9_-]+)", re.IGNORECASE
)


def detect_from_text(text: str) -> dict | None:
    """Return {'ats', 'token'[, 'uid']} if a known ATS marker is found."""
    if not text:
        return None
    m = _COMEET.search(text)
    if m:
        return {"ats": "comeet", "uid": m.group(1), "token": m.group(2)}
    for pat in (_GH_API, _GH_EMBED, _GH_BOARD):
        m = pat.search(text)
        if m:
            return {"ats": "greenhouse", "token": m.group(1)}
    m = _LEVER.search(text)
    if m:
        return {"ats": "lever", "token": m.group(1)}
    return None


def _detect(url: str, session) -> dict | None:
    if not url:
        return None
    # 1. Straight from the URL (no network needed).
    found = detect_from_text(url)
    if found:
        return found
    # 2. Fetch the page and scan its HTML.
    if session is None:
        return None
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return detect_from_text(resp.text)
    except Exception:
        return None


def resolve_ats(company: dict, session=None, cache: dict | None = None) -> dict | None:
    """Return the company enriched with ats/token(/uid), or None if undetected.

    `cache` maps company name -> detection dict. It is mutated in place when a
    new detection succeeds.
    """
    # Manual override wins.
    if company.get("ats"):
        return company

    name = company.get("name", "")
    if cache is not None and name in cache:
        detected = cache[name]
    else:
        detected = _detect(company.get("careers_url") or company.get("homepage"), session)
        if detected and cache is not None:
            cache[name] = detected  # only cache hits, so misses retry next run

    if not detected:
        return None
    merged = dict(company)
    merged.update(detected)
    return merged


# --- cache persistence ------------------------------------------------------

def load_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(path: str, cache: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
