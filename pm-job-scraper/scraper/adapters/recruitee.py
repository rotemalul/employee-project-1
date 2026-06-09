"""Recruitee adapter.

Public offers API (no auth):
    https://{token}.recruitee.com/api/offers/
Response: {"offers": [{"id","title","location","city","country",
            "careers_url","published_at"}]}
"""
from __future__ import annotations

from .base import Adapter, Job

API = "https://{token}.recruitee.com/api/offers/"


class RecruiteeAdapter(Adapter):
    ats_name = "recruitee"

    def fetch_jobs(self, company: dict) -> list[Job]:
        token = company["token"]
        data = self._get_json(API.format(token=token))
        jobs = []
        for item in data.get("offers", []) or []:
            location = item.get("location") or ", ".join(
                p for p in (item.get("city"), item.get("country")) if p
            )
            published = item.get("published_at")
            jobs.append(
                Job(
                    job_id=self.make_id("recruitee", token, item.get("id")),
                    company=company["name"],
                    title=item.get("title", "") or "",
                    location=location or "",
                    url=item.get("careers_url", "") or item.get("careers_apply_url", "") or "",
                    source="recruitee",
                    posted_at=published[:10] if isinstance(published, str) and published else None,
                )
            )
        return jobs
