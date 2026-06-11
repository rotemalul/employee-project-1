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


# --- Enterprise ("traditional company") digital roles ------------------------
# Broader than PM: product, project, and digital/automation leadership at banks,
# insurers, retailers, telecoms, HMOs, etc. Project Manager IS wanted here (so
# the PM-only negative list does not apply), but clearly off-target functions
# (sales/store/logistics/etc.) are still excluded.

_ENTERPRISE_NEGATIVE = re.compile(
    r"\b(sales|account|store|branch|retail\s+store|warehouse|logistics|supply|"
    r"fleet|security|cashier|maintenance|field\s+service|collections|"
    r"underwriting|actuary|teller)\b",
    re.IGNORECASE,
)

_ENTERPRISE_POSITIVE = re.compile(
    r"\bproduct\s+manager\b|\bproduct\s+owner\b|\bproduct\s+lead\b"
    r"|\b(?:director|vp|vice\s+president|head|chief)\s+(?:of\s+)?product\b"
    r"|\bproject\s+manager\b|\bprogram\s+manager\b"
    r"|\bdigital\b|\bautomation\b|\bux\b|\buser\s+experience\b"
    r"|\bcustomer\s+experience\b|\bdigital\s+transformation\b"
    r"|מנהל(?:ת)?\s+מוצר|מנהל(?:ת)?\s+המוצר"
    r"|מנהל(?:ת)?\s+פרו?יי?קט|מוביל(?:ה)?\s+(?:דיגיטל|מוצר)"
    r"|ראש\s+(?:תחום\s+)?דיגיטל|מנהל(?:ת)?\s+(?:תחום\s+)?דיגיטל"
    r"|דיגיטל|אוטומציה|חווי?י?ת\s+לקוח|מוצר\s+דיגיטלי",
    re.IGNORECASE,
)


def is_digital_title(title: str) -> bool:
    """True for product / project / digital leadership roles (enterprise track)."""
    if not title:
        return False
    if _ENTERPRISE_NEGATIVE.search(title):
        return False
    return bool(_ENTERPRISE_POSITIVE.search(title))



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
    """Relevant if located in Israel and the title fits the job's track:
    PM-only for hi-tech, broader product/project/digital for enterprise.
    """
    if not is_in_israel(job.location):
        return False
    if getattr(job, "track", "hightech") == "enterprise":
        return is_digital_title(job.title)
    return is_pm_title(job.title)
