"""Phase 2: the smaller 'Studying' and 'Graduating' sheets, each written to its own table.

  ages.csv                    registered students and new entrants by age and gender (all years)
  graduate_nationalities.csv  graduates by country of nationality (2021-22 onwards); needs student_data.csv first
  internships.csv             internships by type of employer (all years)
  funding.csv                 students by funding type and nationality, and average amounts in QAR (2022-23 onwards)

Run from the project folder:
    .venv/bin/python -m pipeline.student_life
"""
import re

import pandas as pd

from pipeline import vcu_2021_22
from pipeline.graduates import year_from_label
from pipeline.headers import MONTHS, ages_header, funding_header, single_count_header
from pipeline.inventory import ROOT
from pipeline.lists import extract_list_sheet
from pipeline.nationalities import mark_duplicates, standardise_countries
from pipeline.tables import extract_sheet, map_programs, report_problems

PROCESSED = ROOT / "data" / "processed"
MONTH_NAMES = MONTHS.split("|")
ALL_TEMPLATES = ("v2019", "v2020", "v2021", "v2022")
EMPLOYER_TYPES = [("QF", r"^qf\b|qatar foundation"), ("Public", r"^public|government|ministry"),
                  ("Private", r"^private"), ("Abroad", r"^abroad|outside qatar"), ("Other", r"^other\b")]


def ages():
    keys = {"age": lambda t: t == "age"}
    table, problems = extract_list_sheet("student ages", keys, ages_header, ALL_TEMPLATES)
    table = pd.concat([table, pd.DataFrame(vcu_2021_22.age_records())], ignore_index=True)
    table["count"] = table["count"].astype("Int64")
    return table, problems


def file_classes(student_data=None):
    """The graduating class(es) each file's graduate counts were given in Student Data (D-011).

    pipeline.build passes the table it just built; run on its own, this reads student_data.csv.
    """
    if student_data is None:
        sd = pd.read_csv(PROCESSED / "student_data.csv", usecols=["source_file", "row_type", "stage", "graduating_year"],
                         keep_default_na=False, dtype=str)
    else:
        sd = student_data[["source_file", "row_type", "stage", "graduating_year"]].astype("string").fillna("")
    # program rows only: footers have no class label above them and would add a second, default class
    graduated = sd[(sd["stage"] == "graduated") & (sd["graduating_year"] != "")
                   & sd["row_type"].isin(["program", "all_programs"])]
    return graduated.groupby("source_file")["graduating_year"].agg(set).to_dict()


def graduating_class(remarks, source_file, file_year, classes):
    """Graduate nationalities are dated exactly like the same file's graduate counts (D-011), so the
    two sheets never disagree: first a graduation date in the row's Remarks (CMU-Q 2024-25 lists two
    classes, each row dated '2024-05-01' or '2025-05-01'), then the class the file's Student Data
    graduates were given (e.g. CMU-Q 2023-24 -> 2022-23), otherwise the file's own academic year."""
    if isinstance(remarks, str) and re.fullmatch(r"20\d\d-\d\d-\d\d", remarks):
        return year_from_label(f"{MONTH_NAMES[int(remarks[5:7]) - 1]} {remarks[:4]}"), "label"
    in_file = classes.get(source_file, set())
    if len(in_file) == 1:
        return next(iter(in_file)), "student_data"
    return file_year, "form_default"


def graduate_nationalities(student_data=None):
    keys = {"country_raw": lambda t: t.startswith("list of graduate nationalities"),
            "remarks": lambda t: t.startswith("remarks")}
    table, problems = extract_list_sheet("graduate nationalities", keys,
                                         single_count_header(r"(#|total) graduates", "graduated"),
                                         ("v2021", "v2022"), required=("country_raw",), missing_ok=True)
    classes = file_classes(student_data)
    dated =[graduating_class(r, f, y, classes) for r, f, y in zip(table["remarks"], table["source_file"], table["file_year"])]
    table.insert(table.columns.get_loc("remarks") + 1, "graduating_year", [d[0] for d in dated])
    table.insert(table.columns.get_loc("graduating_year") + 1, "timing_evidence", [d[1] for d in dated])
    table, country_problems = standardise_countries(table)
    problems += country_problems
    table, duplicate_problems = mark_duplicates(table, extra_keys=("graduating_year",))
    return table, problems + duplicate_problems


def employer_type(raw):
    """The five types used from 2021-22. Older files name each employer instead ('Qatar Museums',
    'Brookings Doha Center'): those are kept as 'Named employer' (sorting them into types is a
    Phase 4 task)."""
    text = (raw or "").strip().lower()
    return next((name for name, pattern in EMPLOYER_TYPES if re.search(pattern, text)), "Named employer")


def internships():
    keys = {"employer_raw": lambda t: t.startswith("employers providing internship")}
    parse = single_count_header(r"(#|total) internships", "internships")
    old, p1 = extract_list_sheet("internship - employers", keys, parse, ("v2019", "v2020"))
    new, p2 = extract_list_sheet("internships", keys, parse, ("v2021", "v2022"))
    table = pd.concat([old, new], ignore_index=True)
    table.insert(table.columns.get_loc("employer_raw") + 1, "employer_type", table["employer_raw"].map(employer_type))
    return table, p1 + p2


FUNDING_DETAILS = {
    "company_sponsor_details": lambda t: t.startswith("please provide details on company"),
    "government_sponsor_details": lambda t: t.startswith("please provide details on government"),
    "multiple_funding_details": lambda t: t.startswith("please provide details on students numbers"),
}


def funding():
    table, problems = extract_sheet("student funding", funding_header, ("v2022",), FUNDING_DETAILS)
    # Rows with a sponsor's details but no program name break a university's funding down by sponsor
    # (GU-Q 2023-24: 'GU-Q Grant', VCU-Q: 'Qatar Airways', ...). Kept, but never added to totals:
    # whether they repeat or extend the program rows differs by university (P-34).
    no_name = table[["entity_reported", "degree", "program"]].isna().all(axis=1)
    has_detail = table[list(FUNDING_DETAILS)].notna().any(axis=1)
    table.loc[no_name & has_detail, "row_type"] = "sponsor_detail"
    # Amounts are money, not students: move them to their own column (some have decimals)
    amount = table["measure"] == "average_amount_qar"
    as_number = pd.to_numeric(table["value_text"].str.replace(",", ""), errors="coerce")
    table["amount_qar"] = table["count"].astype("Float64").where(table["count"].notna(), as_number).where(amount)
    table.loc[amount & table["amount_qar"].notna(), "value_text"] = pd.NA
    table["count"] = table["count"].where(~amount)
    return map_programs(table, problems)


TABLES = {"ages": ages, "graduate_nationalities": graduate_nationalities, "internships": internships, "funding": funding}


def main():
    problems = []
    for name, build in TABLES.items():
        table, table_problems = build()
        problems += table_problems
        path = PROCESSED / f"{name}.csv"
        table.to_csv(path, index=False)
        print(f"Wrote {path.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files")
    report_problems(problems)


if __name__ == "__main__":
    main()
