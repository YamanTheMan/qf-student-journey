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

    def columns(self):
        """The output columns this header describes."""
        return {"stage": self.stage, "nationality": self.nationality, "residency": self.residency,
                "gender": self.gender, "breakdown": self.breakdown, "period_label": self.period}


def student_data_header(header):
    """Header reader for the Student Data sheet (used by pipeline.tables)."""
    m = parse_measure(header)
    return m.columns() if m else None


# Student Pipeline: '# <stage> from <school type>'. 'Recommended for ABP Year' must be checked first:
# it names ABP but describes students from the school type after 'from'.
PIPELINE_STAGES = [
    ("recommended_abp", r"\brecommended for abp\b"),
    ("applied", r"\bapplied\b"),
    ("admitted", r"\b(admitted|accepted)\b"),
    ("newly_enrolled", r"\benrolled\b"),
    ("denied", r"\bdenied\b"),
]
SCHOOL_TYPES = [
    ("Academic Bridge Program", r"^(abp|academic bridge)\b"),
    ("QF schools", r"\bqf\b|qatar academy"),
    ("Independent/public schools", r"\b(independent|public)\b"),
    ("Private schools", r"\bprivate\b"),
    ("International schools", r"\binternational\b"),
]


def student_pipeline_header(header):
    """'# Admitted from International Schools outside of Qatar' -> {'stage': 'admitted', 'school_type': ...}."""
    if not isinstance(header, str):
        return None
    text = re.sub(r"\s+", " ", header).strip().lower()
    if not text.startswith("#") or " from " not in text:
        return None
    stage = next((name for name, pattern in PIPELINE_STAGES if re.search(pattern, text)), None)
    source = text.rsplit(" from ", 1)[1]  # last 'from': one file says 'from from Private Schools'
    school = next((name for name, pattern in SCHOOL_TYPES if re.search(pattern, source)), None)
    if stage is None or school is None:
        return None
    return {"stage": stage, "school_type": school}


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
    nationality, residency, gender = student_groups(text)
    period = PERIOD.search(text)
    return Measure(stage, nationality, residency, gender, period.group(1).title() if period else None)


def student_groups(text):
    """(nationality, residency, gender) named in a lower-case header; 'All' when not split."""
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
    return nationality, residency, gender


# Graduation Rate: one entering class (cohort) followed to completion.
GRADUATION_STAGES = [
    ("entered", r"first[\s-]*time degree seeking enrolled"),
    ("non_completers", r"non[\s-]*completers"),
    ("dropouts", r"drop[\s-]*outs?"),
    ("graduated_100", r"within 100\s*%"),
    ("graduated_150", r"within 150\s*%"),
]


def graduation_rate_header(header):
    """'# Non-Qatari Females Graduated within 150% of Normal Time' -> stage, nationality, gender, breakdown.

    Only '#' count columns: the 2021-22 template's '%' rate columns are not read (data dictionary P-23).
    """
    if not isinstance(header, str):
        return None
    text = re.sub(r"\s+", " ", header).strip().lower()
    if not text.startswith("#"):
        return None
    stage = next((name for name, pattern in GRADUATION_STAGES if re.search(pattern, text)), None)
    if stage is None:
        return None
    nationality, _, gender = student_groups(text)
    parts = [name for name, value in (("nationality", nationality), ("gender", gender)) if value != "All"]
    return {"stage": stage, "nationality": nationality, "gender": gender, "breakdown": "_".join(parts) or "total"}
