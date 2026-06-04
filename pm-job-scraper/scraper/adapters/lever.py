"""Lever adapter.

Public postings API (no auth):
    https://api.lever.co/v0/postings/{token}?mode=json
Response: [{"id", "text", "categories": {"location", "team", "commitment"},
            "hostedUrl", "createdAt"}, ...]
"""
from __future__ import annotations

from datetime import datetime, timezone

from .base import Adapter, Job

API = "https://api.lever.co/v0/postings/{token}?mode=json"


class LeverAdapter(Adapter):
    ats_name = "lever"

    def fetch_jobs(self, company: dict) -> list[Job]:
        token = company["token"]
        data = self._get_json(API.format(token=token))
        jobs = []
        for item in data:
            categories = item.get("categories") or {}
            posted_at = None
            created = item.get("createdAt")
            if created:
                # Lever returns epoch milliseconds.
                try:
                    posted_at = (
                        datetime.fromtimestamp(created / 1000, tz=timezone.utc)
                        .date()
                        .isoformat()
                    )
                except (TypeError, ValueError, OSError):
                    posted_at = None
            jobs.append(
                Job(
                    job_id=self.make_id("lever", token, item.get("id")),
                    company=company["name"],
                    title=item.get("text", "") or "",
                    location=categories.get("location", "") or "",
                    url=item.get("hostedUrl", "") or "",
                    source="lever",
                    posted_at=posted_at,
                )
            )
        return jobs
