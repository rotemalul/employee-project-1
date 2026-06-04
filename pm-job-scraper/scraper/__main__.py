"""Entry point: scrape all companies, filter, reconcile, and write output.

    python -m scraper
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone

from . import config, store
from .adapters import ADAPTERS
from .discovery import load_cache, resolve_ats, save_cache
from .filters import is_relevant


def run() -> int:
    companies = config.load_companies()
    today = datetime.now(timezone.utc).date().isoformat()

    # One shared HTTP session + ATS-detection cache for the whole run.
    try:
        import requests

        session = requests.Session()
        session.headers.update({"User-Agent": "pm-job-scraper/1.0 (+https://github.com)"})
    except Exception:
        session = None
    cache = load_cache(config.ATS_CACHE_FILE)

    all_jobs = []
    errors = 0
    platforms = Counter()  # how many companies resolved to each ATS
    for company in companies:
        name = company.get("name", "<unnamed>")
        resolved = resolve_ats(company, session=session, cache=cache)
        ats = resolved.get("ats") if resolved else None
        adapter_cls = ADAPTERS.get(ats)
        if adapter_cls is None:
            platforms["unknown"] += 1
            continue
        platforms[ats] += 1
        try:
            adapter = adapter_cls(session=session)
            jobs = adapter.fetch_jobs(resolved)
            relevant = [j for j in jobs if is_relevant(j)]
            all_jobs.extend(relevant)
            if relevant:
                print(f"  - {name} ({ats}): {len(jobs)} total, {len(relevant)} PM/IL")
        except Exception as exc:  # one bad company must not fail the whole run
            errors += 1
            print(f"  ! {name} ({ats}): {type(exc).__name__}: {exc}", file=sys.stderr)

    save_cache(config.ATS_CACHE_FILE, cache)

    # De-duplicate by job_id (same posting can surface twice).
    unique = {j.job_id: j for j in all_jobs}
    jobs = sorted(unique.values(), key=lambda j: (j.company.lower(), j.title.lower()))

    history = store.load_history(config.HISTORY_FILE)
    updated_history = store.reconcile(jobs, history, today)
    store.write_jobs(config.JOBS_FILE, jobs)
    store.write_history(config.HISTORY_FILE, updated_history)

    new_count = sum(1 for j in jobs if j.is_new)
    breakdown = ", ".join(f"{k}={v}" for k, v in sorted(platforms.items()))
    print(
        f"Done: {len(jobs)} relevant jobs ({new_count} new) from {len(companies)} "
        f"companies, {errors} errors."
    )
    print(f"ATS breakdown: {breakdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
