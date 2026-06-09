"""Ashby adapter.

Public job-board API (no auth):
    https://api.ashbyhq.com/posting-api/job-board/{token}
Response: {"jobs": [{"id", "title", "location", "employmentType",
                     "jobUrl", "publishedDate"/"publishedAt", ...}]}
"""
from __future__ import annotations

from .base import Adapter, Job

API = "https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=false"


class AshbyAdapter(Adapter):
    ats_name = "ashby"

    def fetch_jobs(self, company: dict) -> list[Job]:
        token = company["token"]
        data = self._get_json(API.format(token=token))
        jobs = []
        for item in data.get("jobs", []) or []:
            posted = item.get("publishedDate") or item.get("publishedAt")
            posted_at = posted[:10] if isinstance(posted, str) and posted else None
            jobs.append(
                Job(
                    job_id=self.make_id("ashby", token, item.get("id")),
                    company=company["name"],
                    title=item.get("title", "") or "",
                    location=item.get("location", "") or item.get("locationName", "") or "",
                    url=item.get("jobUrl", "") or item.get("applyUrl", "") or "",
                    source="ashby",
                    posted_at=posted_at,
                )
            )
        return jobs
