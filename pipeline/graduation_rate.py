"""Phase 2: extract the Graduation Rate sheet: each entering class followed to completion.

Writes data/processed/graduation_rate.csv with one row per number: program, entering class
(cohort), stage (entered, non_completers, dropouts, graduated_100, graduated_150),
nationality, gender, and exactly where it came from.

The same class is often reported again in later files; the latest real report is used (D-012).

Run from the project folder:
    .venv/bin/python -m pipeline.graduation_rate
"""
import re

import pandas as pd

from pipeline.headers import graduation_rate_header
from pipeline.inventory import ROOT
from pipeline.tables import extract_sheet, map_programs, report_problems

OUTPUT = ROOT / "data" / "processed" / "graduation_rate.csv"
TEMPLATES = ("v2022",)  # the 2021-22 template reports only percentages, without class sizes (P-23)
ROW_FIELDS = {
    "cohort_raw": lambda text: text.startswith("cohort year"),
    "normal_years": lambda text: text.startswith("# normal time"),
}
COUNTED_ROWS = ("program", "all_programs")


def cohort_year(raw):
    """'AY2018/2019', '2018-2019', '2018-19' or 'AY2018' -> '2018-2019', the academic year the class started.

    HEC-Q writes two-year programs as 'AY2022/2024': that class also started in 2022-23.
    """
    if not isinstance(raw, str):
        return None
    m = re.search(r"20\d\d", raw)
    return f"{m.group(0)}-{int(m.group(0)) + 1}" if m else None


def apply_latest_report(table):
    """D-012: when several files report the same class, use the latest one.

    A file 'reports' a class only if it gives that class at least one non-zero number, so a
    later file that lists the class with blanks never replaces real figures.
    """
    out = table.copy()
    status = pd.Series(pd.NA, index=out.index, dtype="string")
    rows = out[out["row_type"].isin(COUNTED_ROWS) & out["cohort"].notna()]
    key = ["university", "program", "cohort"]
    # dropna=False: a program not yet in programs.csv must not vanish from the grouping
    real = rows.groupby(key + ["source_file"], dropna=False)["count"].transform(lambda s: (s.fillna(0) > 0).any())
    status[rows.index] = "empty"
    reported = rows[real.astype(bool)]
    latest = reported.groupby(key, dropna=False)["file_year"].transform("max")
    status[reported.index] = "used"
    status[reported.index[reported["file_year"] < latest]] = "superseded"
    out["report_status"] = status
    return out


def extract_all():
    table, problems = extract_sheet("graduation rate", graduation_rate_header, TEMPLATES, ROW_FIELDS)
    table, problems = map_programs(table, problems)
    table.insert(table.columns.get_loc("cohort_raw") + 1, "cohort", table["cohort_raw"].map(cohort_year))
    undated = table[table["row_type"].isin(COUNTED_ROWS) & table["cohort"].isna() & (table["count"].fillna(0) > 0)]
    problems += [f"{f} cell {c}: graduation-rate numbers with no readable cohort year"
                 for f, c in zip(undated["source_file"], undated["source_cell"])][:20]
    return apply_latest_report(table), problems


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files\n")
    print("Report status (D-012):", table["report_status"].value_counts().to_dict())
    used = table[(table["report_status"] == "used") & (table["breakdown"] == "total")]
    print("\nEntering classes per university (used reports):")
    print(used[used["stage"] == "entered"].groupby("university")["cohort"]
          .agg(lambda s: f"{s.min()} .. {s.max()} ({s.nunique()} classes)").to_string())
    report_problems(problems)


if __name__ == "__main__":
    main()
