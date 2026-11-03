"""Phase 2: extract Registered Students Detailed: registered students by program, nationality,
gender, full/part time, scholarship, sponsorship, language of study and class year.

Writes data/processed/registered_detailed.csv with one row per number and its exact source cell.
The sheet exists from 2021-22. Programs get their standard names from data/reference/programs.csv.

Run from the project folder:
    .venv/bin/python -m pipeline.registered_detailed
"""
from pipeline.headers import detailed_header
from pipeline.inventory import ROOT
from pipeline.lists import extract_list_sheet
from pipeline.tables import map_programs, report_problems

OUTPUT = ROOT / "data" / "processed" / "registered_detailed.csv"
TEMPLATES = ("v2021", "v2022")
KEYS = {
    "entity_reported": lambda t: t == "entity name",
    "degree": lambda t: t == "degree",
    "program": lambda t: t == "program",
    "nationality": lambda t: t == "nationality",
    "gender": lambda t: t == "gender",
    "attendance": lambda t: t.startswith("full time"),
    "scholarship": lambda t: t.startswith("scholarship"),
    "sponsorship": lambda t: t.startswith("sponsorship"),
    "language": lambda t: t.startswith("language"),
    "year_class": lambda t: t.startswith("year classification"),
}
REQUIRED = ("program", "nationality", "gender")
# Standard values next to the raw ones; anything else (e.g. 'Majority Full-Time', 'Various') is 'Mixed'
ATTENDANCE = {"ft": "Full-time", "full time": "Full-time", "full-time": "Full-time",
              "pt": "Part-time", "part time": "Part-time", "part-time": "Part-time"}
YES_NO = {"y": "Yes", "yes": "Yes", "n": "No", "no": "No"}


def standard_value(raw, mapping):
    std = raw.str.strip().str.lower().map(mapping)
    return std.where(raw.isna() | std.notna(), "Mixed")


def extract_all():
    table, problems = extract_list_sheet("registered students detailed", KEYS, detailed_header, TEMPLATES, REQUIRED,
                                         missing_ok=True)
    # A line without a program is the university's single total (GU-Q 2021-22 filled in only that)
    table.insert(2, "row_type", table["program"].notna().map({True: "program", False: "all_programs"}))
    table["attendance_std"] = standard_value(table["attendance"], ATTENDANCE)
    table["scholarship_std"] = standard_value(table["scholarship"], YES_NO)
    table["sponsorship_std"] = standard_value(table["sponsorship"], YES_NO)
    return map_programs(table, problems)


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files\n")
    for col in ("attendance_std", "scholarship_std", "year_class"):
        print(f"{col}:", table.groupby(table[col].fillna("(blank)"))["count"].sum().nlargest(8).to_dict())
    report_problems(problems)


if __name__ == "__main__":
    main()
