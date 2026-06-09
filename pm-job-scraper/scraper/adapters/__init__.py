"""ATS adapters: each knows how to pull job postings from one platform."""
from .base import Adapter, Job
from .ashby import AshbyAdapter
from .comeet import ComeetAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .recruitee import RecruiteeAdapter
from .smartrecruiters import SmartRecruitersAdapter
from .workable import WorkableAdapter
from .workday import WorkdayAdapter

# Registry: maps the `ats` field in companies.yaml to its adapter class.
ADAPTERS = {
    "ashby": AshbyAdapter,
    "comeet": ComeetAdapter,
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "recruitee": RecruiteeAdapter,
    "smartrecruiters": SmartRecruitersAdapter,
    "workable": WorkableAdapter,
    "workday": WorkdayAdapter,
}

__all__ = ["Adapter", "Job", "ADAPTERS"]
