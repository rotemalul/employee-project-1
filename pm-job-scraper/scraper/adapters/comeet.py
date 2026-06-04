"""Comeet adapter (very common among Israeli startups).

Public positions API (no auth beyond a public token):
    https://www.comeet.co/careers-api/2.0/company/{uid}/positions?token={token}
Response: a list of positions, each roughly:
    {"uid", "name", "location": {"name", "city", "country"},
     "url_comeet_hosted_page" / "url_active_page", "time_updated"}

companies.yaml entry needs both `uid` and `token` for Comeet, e.g.:
    - name: "Example"
      ats: "comeet"
      uid: "00.000"
      token: "ABCDEF..."
"""
from __future__ import annotations

from .base import Adapter, Job

API = "https://www.comeet.co/careers-api/2.0/company/{uid}/positions"


class ComeetAdapter(Adapter):
    ats_name = "comeet"

    def fetch_jobs(self, company: dict) -> list[Job]:
        uid = company.get("uid")
        token = company.get("token")
        if not uid or not token:
            raise ValueError(
                f"Comeet company '{company.get('name')}' needs both 'uid' and 'token'"
            )
        data = self._get_json(API.format(uid=uid), params={"token": token})
        jobs = []
        for item in data or []:
            location = item.get("location") or {}
            loc_name = location.get("name") if isinstance(location, dict) else str(location)
            url = (
                item.get("url_comeet_hosted_page")
                or item.get("url_active_page")
                or item.get("url_detected")
                or ""
            )
            jobs.append(
                Job(
                    job_id=self.make_id("comeet", token, item.get("uid")),
                    company=company["name"],
                    title=item.get("name", "") or "",
                    location=loc_name or "",
                    url=url,
                    source="comeet",
                    posted_at=(item.get("time_updated") or "")[:10] or None,
                )
            )
        return jobs
