"""Phase 2: extract the Student Pipeline sheet: applicants by the type of school they come from.

Writes data/processed/student_pipeline.csv with one row per number: stage (applied, admitted,
newly_enrolled, denied, recommended_abp), school type (QF schools, independent/public, private,
international, Academic Bridge Program), program, and the exact source cell.

'Recommended for ABP' students are already counted in 'denied' (form instructions).

Run from the project folder:
    .venv/bin/python -m pipeline.student_pipeline
"""
import pandas as pd

from pipeline.headers import student_pipeline_header
from pipeline.inventory import ROOT
from pipeline.tables import extract_sheet, map_programs, report_problems

OUTPUT = ROOT / "data" / "processed" / "student_pipeline.csv"
TEMPLATES = ("v2021", "v2022")  # the sheet was introduced in 2021-22


def extract_all():
    table, problems = extract_sheet("student pipeline", student_pipeline_header, TEMPLATES)
    return map_programs(table, problems)


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files\n")
    programs = table[table["row_type"].isin(["program", "all_programs"]) & (table["level"] != "non_degree")]
    print("All years, all universities (program rows):")
    print(programs.pivot_table(index="school_type", columns="stage", values="count", aggfunc="sum")
          [["applied", "admitted", "newly_enrolled", "denied", "recommended_abp"]].to_string(), "\n")
    print("Row types:", table["row_type"].value_counts().to_dict())
    print(f"Blank cells: {table['count'].isna().sum():,}   non-numeric text cells: {table['value_text'].notna().sum():,}",
          table["value_text"].value_counts().head(3).to_dict())
    report_problems(problems)


if __name__ == "__main__":
    main()
