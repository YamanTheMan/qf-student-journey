"""Phase 3: one quality flag for every measure x university x year.

A measure is one thing the dashboard shows: a Student Data stage (applied ... graduated) or one of
the other tables. The year is the submission's academic year. The flag comes from the data itself
(is anything there?) and from the quality findings (pipeline.checks):

  complete           numbers present and consistent
  breakdown_partial  totals fine, but some nationality / gender parts withheld or blank
  differs            higher than a reference, or parts that don't add up, but plausibly so
  partial            fewer than a reference, or a key part missing (e.g. entrants for a rate)
  not_comparable     means something else (a cumulative list, a funnel that widens, 1.5x off)
  not_reported       the form had the sheet, but no numbers (or only formula zeros)
  not_in_form        that year's form didn't have the sheet

The `use` column says what the dashboard does with each flag (D-025): show, show with a note,
show marked 'partial', or leave out as a visible gap.
"""
import pandas as pd

from pipeline.sources import submissions

ALL = ("v2019", "v2020", "v2021", "v2021-alt", "v2022")
MEASURES = {  # measure: (table, stage, templates whose form has it and that we read)
    "applied": ("student_data", "applied", ALL),
    "admitted": ("student_data", "admitted", ALL),
    "newly_enrolled": ("student_data", "newly_enrolled", ALL),
    "registered": ("student_data", "registered", ALL),
    "graduated": ("student_data", "graduated", ALL),
    "student_pipeline": ("student_pipeline", None, ("v2021", "v2022")),
    "graduation_rate": ("graduation_rate", None, ("v2022",)),          # 2021-22: percentages only (P-23)
    "outcomes": ("outcomes", None, ("v2021", "v2022")),
    "nationalities": ("nationalities", None, ALL),
    "registered_detailed": ("registered_detailed", None, ("v2021", "v2021-alt", "v2022")),
    "ages": ("ages", None, ALL),
    "graduate_nationalities": ("graduate_nationalities", None, ("v2021", "v2022")),
    "internships": ("internships", None, ("v2019", "v2020", "v2021", "v2022")),
    "funding": ("funding", None, ("v2022",)),
}
COUNTED_ROWS = ("program", "all_programs")
STATUS_ORDER = ["not_comparable", "partial", "differs", "breakdown_partial", "complete"]
SYMBOL = {"complete": "✓", "breakdown_partial": "◑", "differs": "≈", "partial": "◐",
          "not_comparable": "≠", "not_reported": "✗", "not_in_form": "–"}
# How the dashboard uses each flag (D-025)
USE = {"complete": "show", "breakdown_partial": "show", "differs": "show_with_note", "partial": "show_marked",
       "not_comparable": "leave_out", "not_reported": "leave_out", "not_in_form": "not_applicable"}


def status_of(finding):
    """The flag a single finding points to, or None if it doesn't affect the flag."""
    status, severity = finding["status"], finding["severity"]
    if status in ("not_one_class", "newly_enrolled_above_admitted", "admitted_above_applied", "far_below_last_year"):
        return "not_comparable"
    if status == "higher":
        return "not_comparable" if finding["found"] >= 1.5 * finding["expected"] else "differs"
    if status in ("lower", "no_entrants", "class_size_missing", "sponsor_rows"):
        return "partial"
    if status in ("mismatch", "more_outcomes_than_graduates", "more_graduates_than_entrants", "class_larger"):
        return "differs"
    if status in ("withheld", "partly_withheld") and severity == "info" or status == "split_exceeds_class":
        return "breakdown_partial"
    return None


def measure_of(finding):
    if finding["table"] == "student_data":
        return finding["stage"] if finding["stage"] in MEASURES else None
    return finding["table"] if finding["table"] in MEASURES else None


def has_numbers(table, stage):
    """(university, file_year) pairs where the measure has at least one non-zero count."""
    t = table
    if "row_type" in t.columns:
        t = t[t["row_type"].isin(COUNTED_ROWS)]
    if stage:
        t = t[t["stage"] == stage]
    if stage == "graduated":
        t = t[t["graduates_status"] != "not_reported"]  # D-011: e.g. TAMU-Q 2022-23's incomplete early count
    if "measure" in t.columns:
        t = t[t["measure"] == "students"]
    t = t[t["count"].fillna(0) > 0]
    return set(zip(t["university"], t["file_year"]))


def quality_flags(tables, findings):
    files = pd.DataFrame([(s.university, s.academic_year, s.template) for s in submissions()],
                         columns=["university", "file_year", "template"]).drop_duplicates(["university", "file_year"])
    by_key = {}
    for _, f in findings.iterrows():
        measure, status = measure_of(f), status_of(f)
        if measure and status:
            by_key.setdefault((measure, f["university"], f["file_year"]), []).append((status, f))

    rows = []
    for measure, (table, stage, templates) in MEASURES.items():
        present = has_numbers(tables[table], stage)
        for _, file in files.iterrows():
            key = (measure, file["university"], file["file_year"])
            notes = by_key.get(key, [])
            if file["template"] not in templates:
                status = "not_in_form"
            elif (file["university"], file["file_year"]) not in present:
                status = "not_reported"
            else:
                found = {s for s, _ in notes}
                status = next((s for s in STATUS_ORDER if s in found), "complete")
            rows.append({
                "measure": measure, "university": file["university"], "file_year": file["file_year"],
                "status": status, "symbol": SYMBOL[status], "use": USE[status],
                "notes": "; ".join(sorted({f"{f['check']}: {f['status'].replace('_', ' ')}" for _, f in notes})),
            })
    return pd.DataFrame(rows)


def matrix(flags, measure):
    """University x year grid of symbols for one measure (for the report)."""
    m = flags[flags["measure"] == measure].pivot(index="university", columns="file_year", values="symbol")
    return m.fillna("")
