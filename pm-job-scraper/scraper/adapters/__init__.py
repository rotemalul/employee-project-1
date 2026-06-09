"""ATS adapters: each knows how to pull job postings from one platform."""
from .base import Adapter, Job
from .ashby import AshbyAdapter
from .comeet import ComeetAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .workday import WorkdayAdapter

# Registry: maps the `ats` field in companies.yaml to its adapter class.
ADAPTERS = {
    "ashby": AshbyAdapter,
    "comeet": ComeetAdapter,
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "workday": WorkdayAdapter,
}

__all__ = ["Adapter", "Job", "ADAPTERS"]
