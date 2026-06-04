"""Greenhouse adapter.

Public board API (no auth):
    https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=false
Response: {"jobs": [{"id", "title", "location": {"name"}, "absolute_url",
                     "updated_at"}, ...]}
"""
from __future__ import annotations

from .base import Adapter, Job

API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


class GreenhouseAdapter(Adapter):
    ats_name = "greenhouse"

    def fetch_jobs(self, company: dict) -> list[Job]:
        token = company["token"]
        data = self._get_json(API.format(token=token))
        jobs = []
        for item in data.get("jobs", []):
            location = (item.get("location") or {}).get("name", "") or ""
            jobs.append(
                Job(
                    job_id=self.make_id("greenhouse", token, item.get("id")),
                    company=company["name"],
                    title=item.get("title", "") or "",
                    location=location,
                    url=item.get("absolute_url", "") or "",
                    source="greenhouse",
                    posted_at=(item.get("updated_at") or "")[:10] or None,
                )
            )
        return jobs
