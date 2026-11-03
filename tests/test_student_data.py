"""Checks on real files: each test pins down a trap found while building the extractor."""
import pandas as pd
import pytest

from pipeline.sources import submissions
from pipeline.student_data import extract_file

FILES = {src.path: src for src in submissions()}


def extract(path_part):
    srcs = [s for p, s in FILES.items() if path_part in p]
    return pd.DataFrame([r for s in srcs for r in extract_file(s)])


def total(df, stage, program=None, row_types=("program",)):
    d = df[(df.stage == stage) & (df.breakdown == "total") & df.row_type.isin(row_types)]
    if program:
        d = d[d.program == program]
    return int(d["count"].sum())


def test_every_number_points_to_its_cell():
    df = extract("AY24-25/AY24-25 CMU-Q")
    row = df[df.source_cell == "F8"].iloc[0]
    assert (row.program, row.stage, row.nationality, row.gender, row["count"]) == \
        ("Biological Sciences", "applied", "Qatari", "Male", 10)


def test_cmuq_2020_21_combines_both_files():
    # D-008: applicants from the original file, registered from the revision
    df = extract("CMU-Q Student Data Collection AY2020-2021")
    assert set(df.file_year) == {"2020-2021"}
    assert total(df, "applied", "Computer Science") == 418
    assert total(df, "applied", "Computational Biology") == 25
    assert total(df, "registered", "Computer Science") == 88
    assert total(df, "registered", "Computational Biology") == 5


def test_gu_q_duplicate_is_skipped():
    assert not any(p.endswith(".completed.xlsx") for p in FILES)


def test_program_named_applied_is_kept():
    df = extract("HBKU Student Data Collection AY2022-2023")
    assert total(df, "registered", "Applied Islamic Ethics") == 20
    assert total(df, "registered") == 904


def test_unnamed_subtotal_is_not_added():
    df = extract("AY22-23 HEC-Q")
    assert set(df[df.source_cell == "AJ12"].row_type) == {"unnamed_row"}
    assert total(df, "registered", row_types=("program", "all_programs")) == 238


def test_university_wide_line_is_kept():
    df = extract("GUQ_Fall Student Data Collection AY2023-2024")
    assert total(df, "registered", row_types=("all_programs",)) == 466


@pytest.mark.parametrize("path_part", ["VCU_Q Fall Student Data Collection AY2023-2024"])
def test_blank_cells_stay_blank(path_part):
    df = extract(path_part)
    detail = df[(df.row_type == "program") & (df.stage == "registered") & (df.breakdown == "nationality_gender")]
    assert detail["count"].isna().all()  # VCU-Q withheld counts below 10: never turned into 0
