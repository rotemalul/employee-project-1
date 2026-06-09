"""SmartRecruiters adapter.

Public postings API (no auth):
    https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100&offset=N
Response: {"totalFound", "content": [{"id","name","releasedDate",
           "location": {"city","region","country","remote"}}]}
Apply URL: https://jobs.smartrecruiters.com/{token}/{id}
"""
from __future__ import annotations

from .base import Adapter, Job

API = "https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100&offset={offset}"
_MAX = 600


class SmartRecruitersAdapter(Adapter):
    ats_name = "smartrecruiters"

    def fetch_jobs(self, company: dict) -> list[Job]:
        token = company["token"]
        jobs: list[Job] = []
        offset = 0
        total = None
        while offset < _MAX:
            data = self._get_json(API.format(token=token, offset=offset))
            content = data.get("content") or []
            if total is None:
                total = data.get("totalFound", 0)
            for item in content:
                loc = item.get("location") or {}
                location = ", ".join(
                    p for p in (loc.get("city"), loc.get("region"), loc.get("country")) if p
                )
                if loc.get("remote"):
                    location = (location + " (Remote)").strip()
                released = item.get("releasedDate")
                jobs.append(
                    Job(
                        job_id=self.make_id("smartrecruiters", token, item.get("id")),
                        company=company["name"],
                        title=item.get("name", "") or "",
                        location=location,
                        url=f"https://jobs.smartrecruiters.com/{token}/{item.get('id')}",
                        source="smartrecruiters",
                        posted_at=released[:10] if isinstance(released, str) and released else None,
                    )
                )
            offset += 100
            if not content or offset >= (total or 0):
                break
        return jobs
