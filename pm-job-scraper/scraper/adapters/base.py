"""Shared adapter interface and the Job data model."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Job:
    """A single job posting, normalized across all ATS platforms."""

    job_id: str          # stable unique id, e.g. "greenhouse:monday:12345"
    company: str
    title: str
    location: str
    url: str
    source: str                      # which ATS it came from
    track: str = "hightech"          # "hightech" | "enterprise" (set from company)
    posted_at: Optional[str] = None  # ISO date string, if available
    first_seen: Optional[str] = None # filled in by the store layer
    is_new: bool = False             # filled in by the store layer

    def to_dict(self) -> dict:
        return asdict(self)


class Adapter:
    """Base class for ATS adapters.

    Subclasses implement `fetch_jobs(company)` and return a list of `Job`.
    A company dict comes straight from companies.yaml (name, ats, token, ...).
    """

    ats_name = "base"

    def __init__(self, session=None):
        # Imported lazily so unit tests that only touch filters don't need requests.
        import requests

        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": "pm-job-scraper/1.0 (+https://github.com)"}
        )

    def fetch_jobs(self, company: dict) -> list[Job]:
        raise NotImplementedError

    def _get_json(self, url: str, **kwargs):
        resp = self.session.get(url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def make_id(source: str, token: str, raw_id) -> str:
        return f"{source}:{token}:{raw_id}"
