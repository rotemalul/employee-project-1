"""Entry point: scrape all companies, filter, reconcile, and write output.

    python -m scraper
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from . import config, store
from .adapters import ADAPTERS
from .filters import is_relevant


def run() -> int:
    companies = config.load_companies()
    today = datetime.now(timezone.utc).date().isoformat()

    all_jobs = []
    errors = 0
    for company in companies:
        name = company.get("name", "<unnamed>")
        ats = company.get("ats")
        adapter_cls = ADAPTERS.get(ats)
        if adapter_cls is None:
            print(f"  ! {name}: unknown ats '{ats}', skipping", file=sys.stderr)
            continue
        try:
            adapter = adapter_cls()
            jobs = adapter.fetch_jobs(company)
            relevant = [j for j in jobs if is_relevant(j)]
            all_jobs.extend(relevant)
            print(f"  - {name} ({ats}): {len(jobs)} total, {len(relevant)} PM/IL")
        except Exception as exc:  # one bad company must not fail the whole run
            errors += 1
            print(f"  ! {name} ({ats}): {type(exc).__name__}: {exc}", file=sys.stderr)

    # De-duplicate by job_id (same posting can surface twice).
    unique = {j.job_id: j for j in all_jobs}
    jobs = sorted(unique.values(), key=lambda j: (j.company.lower(), j.title.lower()))

    history = store.load_history(config.HISTORY_FILE)
    updated_history = store.reconcile(jobs, history, today)
    store.write_jobs(config.JOBS_FILE, jobs)
    store.write_history(config.HISTORY_FILE, updated_history)

    new_count = sum(1 for j in jobs if j.is_new)
    print(
        f"Done: {len(jobs)} relevant jobs ({new_count} new), "
        f"{len(companies)} companies, {errors} errors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
