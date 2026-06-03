"""Filtering logic: keep only Product Manager roles located in Israel.

This module is pure (no network) so it is fully unit-tested.
"""
from __future__ import annotations

import re

# --- Product Manager title matching -----------------------------------------

# Titles that contain "manager" but are NOT product management.
_NEGATIVE_TITLE = re.compile(
    r"\b(project|program|programme|community|engineering|account|marketing|"
    r"operations|office|partner|category|brand|portfolio)\s+manager\b",
    re.IGNORECASE,
)

# Positive Product-Manager signals (all PM seniorities + Hebrew).
_POSITIVE_TITLE = re.compile(
    r"\bproduct\s+manager\b"
    r"|\bproduct\s+owner\b"
    r"|\bproduct\s+lead\b"
    r"|\b(?:director|vp|vice\s+president|head)\s+(?:of\s+)?product\b"
    r"|\bchief\s+product\s+officer\b"
    r"|\bcpo\b"
    r"|\bproduct\s+management\b"
    r"|מנהל(?:ת)?\s+מוצר"
    r"|מנהל(?:ת)?\s+המוצר",
    re.IGNORECASE,
)


def is_pm_title(title: str) -> bool:
    """True if the title is a Product Manager role (any seniority)."""
    if not title:
        return False
    if _NEGATIVE_TITLE.search(title):
        return False
    return bool(_POSITIVE_TITLE.search(title))


# --- Israel location matching -----------------------------------------------

# Major Israeli hubs + the country name. Word-bounded to avoid false matches
# (e.g. "IL" inside "Brazil" must not match).
_ISRAEL_EN = re.compile(
    r"\b("
    r"israel|tel[\s-]?aviv|tlv|herzl?iya|haifa|jerusalem|ra'?anana|netanya|"
    r"petah\s+tikva|petach\s+tikva|yokneam|yoqneam|be'?er\s+sheva|beersheba|"
    r"rehovot|ramat\s+gan|givatayim|kfar\s+saba|caesarea|modi'?in|"
    r"airport\s+city|or\s+yehuda|il"
    r")\b",
    re.IGNORECASE,
)
_ISRAEL_HE = re.compile(r"ישראל|תל[\s-]?אביב|הרצליה|חיפה|ירושלים")


def is_in_israel(location: str) -> bool:
    """True if the location string refers to a place in Israel."""
    if not location:
        return False
    return bool(_ISRAEL_EN.search(location) or _ISRAEL_HE.search(location))


# --- Combined ---------------------------------------------------------------

def is_relevant(job) -> bool:
    """A job is relevant if it is a PM role located in Israel."""
    return is_pm_title(job.title) and is_in_israel(job.location)
