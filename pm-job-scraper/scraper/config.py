"""Loading the company list and resolving file paths."""
from __future__ import annotations

import os

import yaml

# pm-job-scraper/ root, regardless of where the process is launched from.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.yaml")
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")
COMPANIES_JSON_FILE = os.path.join(DATA_DIR, "companies.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
ATS_CACHE_FILE = os.path.join(DATA_DIR, "ats_cache.json")


def load_companies(path: str = COMPANIES_FILE) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        companies = yaml.safe_load(f) or []
    if not isinstance(companies, list):
        raise ValueError("companies.yaml must contain a list of companies")
    return companies
