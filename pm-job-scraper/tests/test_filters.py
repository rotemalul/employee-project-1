"""Unit tests for the PM + Israel filtering logic (no network needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.adapters.base import Job
from scraper.filters import is_in_israel, is_pm_title, is_relevant


# --- title matching ---------------------------------------------------------

class TestIsPmTitle:
    def test_plain_product_manager(self):
        assert is_pm_title("Product Manager")

    def test_all_seniorities(self):
        for title in [
            "Senior Product Manager",
            "Junior Product Manager",
            "Associate Product Manager",
            "Group Product Manager",
            "Lead Product Manager",
            "Principal Product Manager",
            "Staff Product Manager",
            "Technical Product Manager",
            "Director of Product",
            "VP Product",
            "Head of Product",
            "Chief Product Officer",
            "Product Owner",
            "Product Lead",
        ]:
            assert is_pm_title(title), title

    def test_hebrew(self):
        assert is_pm_title("מנהל מוצר")
        assert is_pm_title("מנהלת מוצר בכירה")

    def test_rejects_project_and_program_manager(self):
        assert not is_pm_title("Project Manager")
        assert not is_pm_title("Senior Program Manager")
        assert not is_pm_title("Product Marketing Manager")
        assert not is_pm_title("Engineering Manager")

    def test_rejects_unrelated(self):
        assert not is_pm_title("Software Engineer")
        assert not is_pm_title("Data Analyst")
        assert not is_pm_title("")


# --- location matching ------------------------------------------------------

class TestIsInIsrael:
    def test_israeli_locations(self):
        for loc in [
            "Tel Aviv, Israel",
            "Tel-Aviv",
            "Herzliya",
            "Haifa, Israel",
            "Jerusalem",
            "Ra'anana",
            "Petah Tikva",
            "TLV",
            "Remote, IL",
            "ישראל",
            "תל אביב",
        ]:
            assert is_in_israel(loc), loc

    def test_non_israeli_locations(self):
        for loc in [
            "New York, USA",
            "London, UK",
            "Brazil",          # must not match via the "il" token
            "Remote - US",
            "Berlin, Germany",
            "",
        ]:
            assert not is_in_israel(loc), loc


# --- combined ---------------------------------------------------------------

class TestIsRelevant:
    def _job(self, title, location):
        return Job(
            job_id="x", company="C", title=title, location=location,
            url="", source="test",
        )

    def test_pm_in_israel_is_relevant(self):
        assert is_relevant(self._job("Senior Product Manager", "Tel Aviv, Israel"))

    def test_pm_abroad_is_not_relevant(self):
        assert not is_relevant(self._job("Product Manager", "New York, USA"))

    def test_non_pm_in_israel_is_not_relevant(self):
        assert not is_relevant(self._job("Project Manager", "Tel Aviv, Israel"))
