"""Phase 2: extract the Student Data sheet from every university submission.

Writes data/processed/student_data.csv with one row per number found:
what it counts (stage, nationality, residency, gender), where it belongs
(year, university, program) and exactly where it came from (file and cell).

Run from the project folder:
    .venv/bin/python -m pipeline.student_data
"""
import pandas as pd

from pipeline import vcu_2021_22
from pipeline.graduates import assign_graduating_class
from pipeline.headers import student_data_header
from pipeline.inventory import ROOT
from pipeline.tables import extract_sheet, extract_table, map_programs, report_problems

OUTPUT = ROOT / "data" / "processed" / "student_data.csv"
TEMPLATES = ("v2019", "v2020", "v2021", "v2022")  # v2021-alt (VCU-Q 2021-22): pipeline.vcu_2021_22


def extract_file(src):
    """Every number in one file's Student Data sheet, as a list of row dicts."""
    return extract_table(src, "student data", student_data_header)


def extract_all():
    table, problems = extract_sheet("student data", student_data_header, TEMPLATES)
    table = pd.concat([table, pd.DataFrame(vcu_2021_22.student_data_records())], ignore_index=True)
    table["count"] = table["count"].astype("Int64")
    return map_programs(assign_graduating_class(table), problems)


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files\n")
    filled = table[table["count"].notna()]
    print("Numbers found per year and stage (blank cells excluded):")
    print(pd.crosstab(filled["file_year"], filled["stage"]).to_string(), "\n")
    print("Rows per breakdown:", table["breakdown"].value_counts().to_dict())
    print("Row types:", table["row_type"].value_counts().to_dict())
    print(f"Blank cells: {table['count'].isna().sum():,}   non-numeric text cells: {table['value_text'].notna().sum():,}")
    grad = table[table["stage"] == "graduated"]
    print("Graduated numbers by status:", grad["graduates_status"].value_counts().to_dict())
    print("...and by timing evidence:", grad["timing_evidence"].value_counts().to_dict())
    reg = table[(table["stage"] == "registered") & (table["breakdown"] == "total") & table["level"].notna()]
    print("\nRegistered students by level (reported totals):")
    print(reg.pivot_table(index="file_year", columns="level", values="count", aggfunc="sum").to_string())
    report_problems(problems)


if __name__ == "__main__":
    main()
