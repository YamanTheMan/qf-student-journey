"""Phase 2: give every 'graduated' number its graduating class (decision D-011).

Universities don't agree on which class a year's file describes (data dictionary P-07),
so each number is dated by the best evidence available, in this order:
  1. label         a graduation date in or above the column header ('May 2024 Graduates', 'Class of 2025')
  2. remark/outcomes  a hand-checked entry in data/reference/graduate_timing.csv
  3. form_default  the form's own definition: graduates of the file's academic year
Then, per university and class:
  - a file whose graduates for that class are all zero or blank -> not_reported (not collected yet)
  - the same class reported by several files -> the latest file is used, earlier ones superseded
"""
import re

import pandas as pd

from pipeline.headers import MONTHS
from pipeline.inventory import REFERENCE_DIR

GRADUATION_DATE = re.compile(rf"\b({MONTHS})\s+(20\d\d)\b|\bclass of (20\d\d)\b", re.I)
MONTH_NUMBER = {name: i + 1 for i, name in enumerate(MONTHS.split("|"))}
NEW_COLUMNS = ("graduating_year", "timing_evidence", "timing_note", "graduates_status")
COUNTED_ROWS = ("program", "all_programs")  # sheet totals and unnamed subtotals never decide anything


def academic_year(start):
    return f"{start}-{start + 1}"


def year_from_label(label):
    """'May 2024 Graduates' -> '2023-2024'.

    The academic year runs July-June, so an August-December graduation belongs to the year
    that starts then, and a January-July graduation to the year that ends then.
    """
    if not isinstance(label, str):
        return None
    m = GRADUATION_DATE.search(label)
    if not m:
        return None
    if m.group(3):
        return academic_year(int(m.group(3)) - 1)
    month, year = MONTH_NUMBER[m.group(1).lower()], int(m.group(2))
    return academic_year(year if month >= 8 else year - 1)


def load_exceptions(path=REFERENCE_DIR / "graduate_timing.csv"):
    return pd.read_csv(path).set_index(["university", "file_year"])


def date_row(row, exceptions):
    """(graduating_year, evidence, note, exception status) for one graduated number."""
    for label in (row["period_label"], row["band_label"]):
        year = year_from_label(label)
        if year:
            return year, "label", label, None
    key = (row["university"], row["file_year"])
    if key in exceptions.index:
        e = exceptions.loc[key]
        return e["graduating_year"], e["evidence_type"], e["evidence"], e["status"]
    return row["file_year"], "form_default", "Form definition: graduates of the file's academic year", None


def assign_graduating_class(table, exceptions=None):
    exceptions = load_exceptions() if exceptions is None else exceptions
    out = table.copy()
    for col in NEW_COLUMNS:
        out[col] = pd.Series(pd.NA, index=out.index, dtype="string")
    grad = out.index[out["stage"] == "graduated"]
    if len(grad) == 0:
        return out

    dated = pd.DataFrame([date_row(out.loc[i], exceptions) for i in grad], index=grad,
                         columns=["graduating_year", "timing_evidence", "timing_note", "exception_status"])
    for col in ("graduating_year", "timing_evidence", "timing_note"):
        out.loc[grad, col] = dated[col]

    # A class counts as reported by a file only if that file gives it at least one graduate.
    rows = out.loc[grad]
    has_graduates = rows["row_type"].isin(COUNTED_ROWS) & (rows["count"].fillna(0) > 0)
    reported = set(map(tuple, rows.loc[has_graduates, ["source_file", "graduating_year"]].drop_duplicates().values))
    status = pd.Series(
        ["used" if (f, y) in reported else "not_reported" for f, y in zip(rows["source_file"], rows["graduating_year"])],
        index=grad)
    status[dated["exception_status"] == "not_reported"] = "not_reported"

    # The same class from several files: the latest file wins (D-011).
    live = rows[status == "used"]
    latest = live.groupby(["university", "graduating_year"])["file_year"].transform("max")
    status[live.index[live["file_year"] < latest]] = "superseded"

    out.loc[grad, "graduates_status"] = status
    return out
