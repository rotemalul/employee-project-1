"""Unit tests for ATS auto-discovery (URL + embedded-HTML parsing, no network)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.discovery import detect_from_text, resolve_ats


class TestDetectFromText:
    def test_greenhouse_board_url(self):
        assert detect_from_text("https://boards.greenhouse.io/monday") == {
            "ats": "greenhouse", "token": "monday"
        }

    def test_greenhouse_job_boards_host(self):
        assert detect_from_text("https://job-boards.greenhouse.io/gong")["token"] == "gong"

    def test_greenhouse_api_url(self):
        out = detect_from_text("https://boards-api.greenhouse.io/v1/boards/lemonade/jobs")
        assert out == {"ats": "greenhouse", "token": "lemonade"}

    def test_greenhouse_embed_for_param(self):
        html = '<script src="https://boards.greenhouse.io/embed/job_board/js?for=fiverr"></script>'
        assert detect_from_text(html) == {"ats": "greenhouse", "token": "fiverr"}

    def test_lever_url(self):
        assert detect_from_text("https://jobs.lever.co/taboola")["token"] == "taboola"
        assert detect_from_text("https://api.lever.co/v0/postings/welltory") == {
            "ats": "lever", "token": "welltory"
        }

    def test_comeet_careers_api(self):
        html = 'fetch("https://www.comeet.co/careers-api/2.0/company/A1.B2C/positions?token=DEADBEEF42")'
        assert detect_from_text(html) == {
            "ats": "comeet", "uid": "A1.B2C", "token": "DEADBEEF42"
        }

    def test_comeet_wins_over_greenhouse_when_both_present(self):
        text = (
            "https://boards.greenhouse.io/foo "
            "https://www.comeet.co/careers-api/2.0/company/00.001/positions?token=ABC123"
        )
        assert detect_from_text(text)["ats"] == "comeet"

    def test_no_match(self):
        assert detect_from_text("https://example.com/careers") is None
        assert detect_from_text("") is None


class TestResolveAts:
    def test_manual_override_is_respected(self):
        company = {"name": "X", "ats": "greenhouse", "token": "x"}
        assert resolve_ats(company) is company

    def test_detect_from_careers_url_without_network(self):
        company = {"name": "Monday", "careers_url": "https://boards.greenhouse.io/monday"}
        out = resolve_ats(company, session=None)
        assert out["ats"] == "greenhouse" and out["token"] == "monday"
        # original company dict is not mutated
        assert "ats" not in company

    def test_unknown_returns_none(self):
        company = {"name": "Y", "careers_url": "https://example.com/jobs"}
        assert resolve_ats(company, session=None) is None

    def test_cache_is_populated_on_hit(self):
        cache = {}
        company = {"name": "Gong", "careers_url": "https://jobs.lever.co/gong"}
        resolve_ats(company, session=None, cache=cache)
        assert cache["Gong"]["ats"] == "lever"
