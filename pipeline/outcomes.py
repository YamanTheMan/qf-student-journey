"""Phase 2: extract the Student Outcomes after 1 Yr sheet: where graduates are a year later.

Writes data/processed/outcomes.csv with one row per number: stage (graduates = the class size,
then employed, self_employed, grad_school, still_searching, not_seeking), nationality,
location (In Qatar / Outside Qatar), program, graduating class, and the exact source cell.

Each number gets its graduating class: the class named in the header ('AY 2021-22') or above
the block ('Class of 2023'), otherwise the form's definition, the previous academic year.
When several files report the same class, the earliest real report is used (D-013), and every
row records how many years after graduation it was measured.

Run from the project folder:
    .venv/bin/python -m pipeline.outcomes
"""
import re

import pandas as pd

from pipeline.graduates import academic_year, year_from_label
from pipeline.headers import outcomes_header
from pipeline.inventory import ROOT
from pipeline.tables import extract_sheet, map_programs, report_problems

OUTPUT = ROOT / "data" / "processed" / "outcomes.csv"
TEMPLATES = ("v2021", "v2022")  # the sheet was introduced in 2021-22
COUNTED_ROWS = ("program", "all_programs")
OUTCOMES = ("employed", "self_employed", "grad_school", "still_searching", "not_seeking")


def graduating_class(period_label, band_label, file_year):
    """(graduating_year, evidence) for one number."""
    m = re.search(r"20\d\d", period_label) if isinstance(period_label, str) else None
    if m:
        return academic_year(int(m.group(0))), "label"
    year = year_from_label(band_label)
    if year:
        return year, "label"
    return academic_year(int(file_year[:4]) - 1), "form_default"


def apply_earliest_report(table):
    """D-013: when several files report the same class, use the earliest real report.

    A 'class' is a university's graduating year, compared across files as a whole, not program
    by program: CMU-Q's 2023-24 sheet lists its programs without names, so a program-level
    comparison would count the class of 2023 twice. A file reports a class's outcomes only if
    at least one outcome is non-zero: a class size with all-zero outcomes means the outcomes
    weren't collected yet.
    """
    out = table.copy()
    dated = [graduating_class(p, b, y) for p, b, y in zip(out["period_label"], out["band_label"], out["file_year"])]
    out["graduating_year"] = [d[0] for d in dated]
    out["class_evidence"] = [d[1] for d in dated]
    # e.g. the class of 2022-23 in the 2023-24 file: 2024 - 2023 = 1 year after graduation
    out["years_after_graduation"] = out["file_year"].str[5:].astype(int) - out["graduating_year"].str[5:].astype(int)

    status = pd.Series(pd.NA, index=out.index, dtype="string")
    rows = out[out["row_type"].isin(COUNTED_ROWS)]
    key = ["university", "graduating_year"]
    has_outcome = rows["stage"].isin(OUTCOMES) & (rows["count"].fillna(0) > 0)
    real = has_outcome.groupby([rows[k] for k in key] + [rows["source_file"]], dropna=False).transform("any")
    status[rows.index] = "empty"
    reported = rows[real.astype(bool)]
    earliest = reported.groupby(key, dropna=False)["file_year"].transform("min")
    status[reported.index] = "used"
    status[reported.index[reported["file_year"] > earliest]] = "later_report"
    out["report_status"] = status
    return out


def extract_all():
    table, problems = extract_sheet("student outcomes after 1 yr", outcomes_header, TEMPLATES)
    table, problems = map_programs(table, problems)
    return apply_earliest_report(table), problems


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files\n")
    print("Report status (D-013):", table["report_status"].value_counts().to_dict())
    print("Class dated by:", table["class_evidence"].value_counts().to_dict())
    used = table[(table["report_status"] == "used") & (table["breakdown"] == "total")]
    print("\nAll universities, used reports (totals):")
    print(used.pivot_table(index="graduating_year", columns="stage", values="count", aggfunc="sum")
          [["graduates", *OUTCOMES]].to_string())
    report_problems(problems)


if __name__ == "__main__":
    main()
