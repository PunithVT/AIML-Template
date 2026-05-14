"""Extract work-experience entries from resume text."""

import re


def extract_experience(text: str) -> list[dict]:
    """Return a list of experience records extracted from resume text."""
    pattern = re.compile(r"(\d+)\+?\s*(?:years|year|yrs|yr)", re.IGNORECASE)
    matches = [int(match.group(1)) for match in pattern.finditer(text)]
    total_years = max(matches) if matches else 0

    if total_years == 0:
        return []

    return [{
        "years": float(total_years),
        "summary": f"{total_years}+ years experience found"
    }]
