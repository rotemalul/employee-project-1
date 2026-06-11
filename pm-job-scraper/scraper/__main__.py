"""Entry point: scrape all companies, filter, reconcile, and write output.

    python -m scraper
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import datetime, timezone

from . import config, store
from .adapters import ADAPTERS
from .discovery import load_cache, resolve_ats, save_cache
from .filters import is_relevant


def run() -> int:
    started = datetime.now(timezone.utc)
    companies = config.load_companies()
    today = started.date().isoformat()

    # One shared HTTP session + ATS-detection cache for the whole run.
    try:
        import requests

        session = requests.Session()
        session.headers.update({"User-Agent": "pm-job-scraper/1.0 (+https://github.com)"})
    except Exception:
        session = None
    cache = load_cache(config.ATS_CACHE_FILE)

    # Optional pre-pass: harvest Comeet uid+token for companies whose token only
    # loads via JS, by rendering each company's careers page with a headless
    # browser and sniffing the Comeet API call. This is slow, so it runs only
    # when HARVEST_COMEET=true (manual workflow_dispatch). Results are cached
    # (committed) so the fast scheduled runs reuse them without a browser.
    from .browser import harvest_comeet

    to_harvest = [
        c for c in companies
        if c.get("comeet_url") and c.get("name") not in cache
    ]
    if to_harvest and os.environ.get("HARVEST_COMEET", "").lower() == "true":
        print(f"Harvesting Comeet tokens for {len(to_harvest)} companies...")
        for c in to_harvest:
            # The company's own careers page embeds the standard Comeet widget
            # (fires the public careers-api call); the hosted comeet_url is a
            # fallback. We pass the known uid (last path segment of comeet_url)
            # so the sniffer can also match the hosted page's own API call.
            uid = c["comeet_url"].rstrip("/").rsplit("/", 1)[-1]
            detected = harvest_comeet([c.get("careers_url"), c.get("comeet_url")], expected_uid=uid)
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
        track = company.get("track", "hightech")
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
            "track": track,
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
            for j in jobs:
                j.track = track
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
    scanned = sum(v for k, v in platforms.items() if k != "unknown")
    error_companies = sorted(r["name"] for r in company_rows if r["error"])
    finished = datetime.now(timezone.utc)
    store.append_run(config.RUNS_FILE, {
        "finished_at": finished.isoformat(timespec="seconds"),
        "duration_sec": round((finished - started).total_seconds()),
        "status": "ok" if errors == 0 else "partial",
        "jobs": len(jobs),
        "new": new_count,
        "companies": len(companies),
        "scanned": scanned,
        "errors": errors,
        "error_companies": error_companies,
        "ats": dict(sorted(platforms.items())),
    })

    breakdown = ", ".join(f"{k}={v}" for k, v in sorted(platforms.items()))
    print(
        f"Done: {len(jobs)} relevant jobs ({new_count} new) from {len(companies)} "
        f"companies, {errors} errors."
    )
    print(f"ATS breakdown: {breakdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
