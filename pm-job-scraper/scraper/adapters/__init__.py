"""ATS adapters: each knows how to pull job postings from one platform."""
from .base import Adapter, Job
from .comeet import ComeetAdapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter

# Registry: maps the `ats` field in companies.yaml to its adapter class.
ADAPTERS = {
    "comeet": ComeetAdapter,
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
}

__all__ = ["Adapter", "Job", "ADAPTERS"]
