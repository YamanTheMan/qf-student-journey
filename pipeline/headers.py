"""Understand a column header such as '# Admitted Resident Non-Qatari Female' or 'Total Graduated Students May 2025'.

Columns are always read by what their header says, never by their position, because the
wording and order change between template versions (data dictionary P-12).
"""
import re
from dataclasses import dataclass

# Checked in order: 'newly enrolled' must win before anything else matches.
STAGES = [
    ("newly_enrolled", r"\bnewly\s*enrolled\b"),
    ("applied", r"\bappl(ied|icants?)\b"),
    ("admitted", r"\b(admitted|accepted)\b"),
    ("registered", r"\bregistered\b"),
    ("graduated", r"\bgraduated\b"),
]
MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"
PERIOD = re.compile(rf"\b((?:{MONTHS}|fall|spring|summer)\s+20\d\d|class of 20\d\d)\b", re.I)


@dataclass(frozen=True)
class Measure:
    stage: str           # applied / admitted / newly_enrolled / registered / graduated
    nationality: str     # Qatari / Non-Qatari / All
    residency: str       # Resident / International / All (only splits Non-Qatari)
    gender: str          # Male / Female / All
    period: str | None   # e.g. 'May 2025', when the header names one

    @property
    def breakdown(self):
        """Which split this number belongs to. Only numbers with the same breakdown add up to the total."""
        parts = [name for name, value in (("nationality", self.nationality), ("gender", self.gender))
                 if value != "All"]
        return "_".join(parts) or "total"


def parse_measure(header):
    """Header text -> Measure, or None when the column isn't a student count."""
    if not isinstance(header, str):
        return None
    text = re.sub(r"\s+", " ", header).strip().lower()
    if text.startswith("remarks"):
        return None
    stage = next((name for name, pattern in STAGES if re.search(pattern, text)), None)
    if stage is None:
        return None

    if re.search(r"non[\s-]*qatari", text):
        nationality = "Non-Qatari"
    elif re.search(r"\bqatari\b", text):
        nationality = "Qatari"
    else:
        nationality = "All"

    residency = "All"
    if nationality == "Non-Qatari":
        if re.search(r"\bresident\b", text):
            residency = "Resident"
        elif re.search(r"\binternational\b", text):
            residency = "International"

    if re.search(r"\bfemales?\b", text):
        gender = "Female"
    elif re.search(r"\bmales?\b", text):
        gender = "Male"
    else:
        gender = "All"

    period = PERIOD.search(text)
    return Measure(stage, nationality, residency, gender, period.group(1).title() if period else None)
