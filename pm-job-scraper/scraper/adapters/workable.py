"""Workable adapter.

Public job-board widget API (no auth):
    https://apply.workable.com/api/v1/widget/accounts/{token}?details=true
Response: {"name", "jobs": [{"title","shortcode","city","country",
            "url","application_url","published_on"}]}
"""
from __future__ import annotations

from .base import Adapter, Job

API = "https://apply.workable.com/api/v1/widget/accounts/{token}?details=true"


class WorkableAdapter(Adapter):
    ats_name = "workable"

    def fetch_jobs(self, company: dict) -> list[Job]:
        token = company["token"]
        data = self._get_json(API.format(token=token))
        jobs = []
        for item in data.get("jobs", []) or []:
            location = ", ".join(
                p for p in (item.get("city"), item.get("state"), item.get("country")) if p
            )
            published = item.get("published_on") or item.get("created_at")
            url = item.get("url") or item.get("application_url") or ""
            if not url and item.get("shortcode"):
                url = f"https://apply.workable.com/{token}/j/{item['shortcode']}/"
            jobs.append(
                Job(
                    job_id=self.make_id("workable", token, item.get("shortcode") or item.get("id")),
                    company=company["name"],
                    title=item.get("title", "") or "",
                    location=location,
                    url=url,
                    source="workable",
                    posted_at=published[:10] if isinstance(published, str) and published else None,
                )
            )
        return jobs
