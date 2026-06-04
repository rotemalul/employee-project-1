"""Persistence: history of seen jobs + the jobs.json output."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def load_history(path: str) -> dict:
    """history.json maps job_id -> first_seen ISO date."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def reconcile(jobs: list, history: dict, today: str):
    """Mark each job's first_seen / is_new and return an updated history.

    A job is "new" if its id was never seen before this run. The returned
    history is the union of the old history and today's jobs, so a posting
    that briefly disappears and returns is not falsely flagged as new.
    """
    updated = dict(history)
    for job in jobs:
        if job.job_id in history:
            job.first_seen = history[job.job_id]
            job.is_new = False
        else:
            job.first_seen = today
            job.is_new = True
        updated[job.job_id] = job.first_seen
    return updated


def write_jobs(path: str, jobs: list) -> None:
    new_count = sum(1 for j in jobs if j.is_new)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(jobs),
        "new_count": new_count,
        "jobs": [j.to_dict() for j in jobs],
    }
    _write_json(path, payload)


def write_companies(path: str, companies: list[dict]) -> None:
    """The full scanned-company roster (for the dashboard's company view)."""
    scanned = sum(1 for c in companies if c.get("ats") and c["ats"] != "unknown")
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(companies),
        "scanned_count": scanned,
        "companies": companies,
    }
    _write_json(path, payload)


def write_history(path: str, history: dict) -> None:
    _write_json(path, history)


def _write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
