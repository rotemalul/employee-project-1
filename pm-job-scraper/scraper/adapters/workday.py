"""Workday adapter.

Workday has no uniform public API — every company runs its own tenant, so a
single "token" isn't enough. Each company pins three coordinates in
companies.yaml:

    ats: workday
    workday_host:   "intel.wd1.myworkdayjobs.com"   # the myworkdayjobs host
    workday_tenant: "intel"                          # tenant id
    workday_site:   "External"                       # career-site path
    workday_search: "Product"   # optional: narrows the search (default "Product")

We POST to the CXS jobs endpoint and paginate. `searchText` keeps the result
set small (these tenants can hold thousands of global postings); the usual
PM/Israel filter still runs afterwards.

    POST https://{host}/wday/cxs/{tenant}/{site}/jobs
    body: {"appliedFacets":{}, "limit":20, "offset":N, "searchText":"Product"}
    -> {"total":N, "jobPostings":[{"title","locationsText","externalPath","postedOn"}]}

Apply URL: https://{host}/en-US/{site}{externalPath}
"""
from __future__ import annotations

from .base import Adapter, Job

_PAGE = 20
_MAX = 400  # safety cap on how deep we page per company


class WorkdayAdapter(Adapter):
    ats_name = "workday"

    def fetch_jobs(self, company: dict) -> list[Job]:
        host = company["workday_host"]
        tenant = company["workday_tenant"]
        site = company["workday_site"]
        search = company.get("workday_search", "Product")
        url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

        jobs: list[Job] = []
        offset = 0
        total = None
        while offset < _MAX:
            payload = {"appliedFacets": {}, "limit": _PAGE, "offset": offset, "searchText": search}
            resp = self.session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            postings = data.get("jobPostings") or []
            if total is None:
                total = data.get("total", 0)
            for p in postings:
                ext = p.get("externalPath", "") or ""
                jobs.append(
                    Job(
                        job_id=self.make_id("workday", tenant, ext or p.get("title")),
                        company=company["name"],
                        title=p.get("title", "") or "",
                        location=p.get("locationsText", "") or "",
                        url=f"https://{host}/en-US/{site}{ext}",
                        source="workday",
                        posted_at=None,  # Workday exposes "Posted 30+ Days Ago", not a date
                    )
                )
            offset += _PAGE
            if not postings or offset >= (total or 0):
                break
        return jobs
