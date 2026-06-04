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

    # Pre-pass: harvest Comeet uid+token for companies whose token only loads
    # via JS. We render each company's `comeet_url` with a headless browser and
    # sniff the Comeet API call. Results are cached (by name) so later runs skip
    # the browser entirely. Companies already in the cache are not re-harvested.
    from .browser import harvest_comeet

    to_harvest = [
        c for c in companies
        if c.get("comeet_url") and c.get("name") not in cache
    ]
    if to_harvest:
        print(f"Harvesting Comeet tokens for {len(to_harvest)} companies...")
        for c in to_harvest:
            # The company's own careers page embeds the standard Comeet widget
            # (fires the public careers-api call); the hosted comeet_url is a
            # fallback.
            detected = harvest_comeet([c.get("careers_url"), c.get("comeet_url")])
            if detected:
                cache[c["name"]] = detected
                print(f"  + {c['name']}: comeet uid={detected['uid']}")
            else:
                print(f"  ! {c['name']}: comeet token not harvested", file=sys.stderr)
        save_cache(config.ATS_CACHE_FILE, cache)

    all_jobs = []
    errors = 0
    platforms = Counter()  # how many companies resolved to each ATS
    company_rows = []  # roster for the dashboard's company view
    for company in companies:
        name = company.get("name", "<unnamed>")
        resolved = resolve_ats(company, session=session, cache=cache)
        ats = resolved.get("ats") if resolved else None
        adapter_cls = ADAPTERS.get(ats)
        row = {
            "name": name,
            "description": company.get("description", ""),
            "category": company.get("category", ""),
            "hq": company.get("hq", ""),
            "careers_url": company.get("careers_url", ""),
            "ats": ats or "unknown",
            "jobs_count": 0,
            "error": False,
        }
        if adapter_cls is None:
            platforms["unknown"] += 1
            company_rows.append(row)
            continue
        platforms[ats] += 1
        try:
            adapter = adapter_cls(session=session)
            jobs = adapter.fetch_jobs(resolved)
            relevant = [j for j in jobs if is_relevant(j)]
            all_jobs.extend(relevant)
            row["jobs_count"] = len(relevant)
            if relevant:
                print(f"  - {name} ({ats}): {len(jobs)} total, {len(relevant)} PM/IL")
        except Exception as exc:  # one bad company must not fail the whole run
            errors += 1
            row["error"] = True
            print(f"  ! {name} ({ats}): {type(exc).__name__}: {exc}", file=sys.stderr)
        company_rows.append(row)

    save_cache(config.ATS_CACHE_FILE, cache)

    # De-duplicate by job_id (same posting can surface twice).
    unique = {j.job_id: j for j in all_jobs}
    jobs = sorted(unique.values(), key=lambda j: (j.company.lower(), j.title.lower()))

    history = store.load_history(config.HISTORY_FILE)
    updated_history = store.reconcile(jobs, history, today)
    store.write_jobs(config.JOBS_FILE, jobs)
    store.write_history(config.HISTORY_FILE, updated_history)
    store.write_companies(config.COMPANIES_JSON_FILE, company_rows)

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
