"""Checks on the processed Student Pipeline table."""
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
READ = dict(dtype={"degree_raw": str, "program_raw": str}, keep_default_na=False,
            na_values={"count": [""], "level": [""], "program": [""]})


def table(name):
    return pd.read_csv(PROCESSED / name, **READ)


def entry_totals(df, university, year, stage, breakdown=None):
    d = df[(df.university == university) & (df.file_year == year) & (df.stage == stage)
           & df.row_type.isin(["program", "all_programs"]) & df.level.isin(["undergraduate", "foundation"])]
    if breakdown:
        d = d[d.breakdown == breakdown]
    return int(d["count"].sum())


def test_every_program_row_is_mapped():
    pl = table("student_pipeline.csv")
    assert pl[pl.row_type.isin(["program", "all_programs"])].level.notna().all()


def test_no_program_named_after_an_excel_error():
    pl = table("student_pipeline.csv")
    assert not pl.program_raw.str.startswith("#").any()


def test_pipeline_matches_student_data_where_both_are_complete():
    pl, sd = table("student_pipeline.csv"), table("student_data.csv")
    for year in ("2022-2023", "2023-2024", "2024-2025"):
        for stage in ("applied", "admitted", "newly_enrolled"):
            assert entry_totals(pl, "GU-Q", year, stage) == entry_totals(sd, "GU-Q", year, stage, "total")


def test_hbku_pipeline_covers_undergraduate_entry_only():
    # 1,953 = applicants to HBKU's only undergraduate program (Computer Engineering) in Student Data
    pl, sd = table("student_pipeline.csv"), table("student_data.csv")
    assert entry_totals(pl, "HBKU", "2022-2023", "applied") == 1953 == \
        entry_totals(sd, "HBKU", "2022-2023", "applied", "total")


def test_vcuq_misaligned_rows_map_by_degree():
    pl = table("student_pipeline.csv")
    row = pl[(pl.university == "VCU-Q") & (pl.file_year == "2022-2023") & (pl.degree_raw == "BA")
             & (pl.program_raw == "Art Foundation-FYI")].iloc[0]
    assert (row.program, row.level) == ("Art History", "undergraduate")
